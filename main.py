#!/usr/bin/env python3
"""
PSD Composer - Orquestrador Python
Integração com Airtable, processamento em Photoshop via ExtendScript,
compressão de imagens e upload via FTP.

Pipeline:
1. Poll Airtable Designs table (Status="Pending")
2. Download design PNG attachment
3. Run ExtendScript 3x (main, marketing, print batches)
4. Compress exported JPGs
5. Upload to FTP
6. Update Airtable status
"""

import json
import subprocess
import sys
import os
import time
import logging
import shutil
import tempfile
import ftplib
import io
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from PIL import Image

# ============================================================================
# CARREGAMENTO DE VARIÁVEIS DE AMBIENTE
# ============================================================================

load_dotenv()

SCRIPT_DIR = Path(__file__).parent
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configurações de ambiente
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_DESIGNS_TABLE = os.getenv("AIRTABLE_DESIGNS_TABLE", "Designs")
AIRTABLE_COLORS_TABLE = os.getenv("AIRTABLE_COLORS_TABLE", "Colors")

PHOTOSHOP_EXE = os.getenv(
    "PHOTOSHOP_EXE", "C:/Program Files/Adobe/Adobe Photoshop 2024/Photoshop.exe"
)
COMPOSER_JSX = os.getenv("COMPOSER_JSX", str(SCRIPT_DIR / "composer.jsx"))

TEMPLATES_DIR_MAIN = os.getenv(
    "TEMPLATES_DIR_MAIN", "C:/psd-composer/assets/templates/main"
)
TEMPLATES_DIR_MARKETING = os.getenv(
    "TEMPLATES_DIR_MARKETING", "C:/psd-composer/assets/templates/marketing"
)
TEMPLATES_DIR_PRINT = os.getenv(
    "TEMPLATES_DIR_PRINT", "C:/psd-composer/assets/templates/print"
)

OUTPUT_BASE_DIR = Path(os.getenv("OUTPUT_BASE_DIR", "C:/psd-composer/assets/output"))

FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
FTP_BASE_PATH = os.getenv("FTP_BASE_PATH", "uploads/DTG")

JPG_QUALITY = int(os.getenv("JPG_QUALITY", "85"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

# ============================================================================
# LOGGER SETUP
# ============================================================================


def setup_logger():
    """Configura logger com arquivo rotativo"""
    logger = logging.getLogger("psd_composer")
    logger.setLevel(logging.DEBUG)

    # Handler para arquivo rotativo (10MB, max 5 arquivos)
    log_file = LOG_DIR / "psd_composer.log"
    file_handler = RotatingFileHandler(
        str(log_file), maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()

# ============================================================================
# AIRTABLE INTEGRATION
# ============================================================================


class AirtableClient:
    """Cliente para interagir com Airtable API"""

    def __init__(self, api_key, base_id):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.airtable.com/v0"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_records(self, table_name, filter_by_formula=None):
        """Retorna registros de uma tabela, opcionalmente filtrados"""
        url = f"{self.base_url}/{self.base_id}/{table_name}"
        params = {}
        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()["records"]
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar registros de {table_name}: {e}")
            return []

    def update_record(self, table_name, record_id, fields):
        """Atualiza um registro"""
        url = f"{self.base_url}/{self.base_id}/{table_name}/{record_id}"

        try:
            response = requests.patch(
                url, headers=self.headers, json={"fields": fields}
            )
            response.raise_for_status()
            logger.debug(f"Registro {record_id} atualizado em {table_name}")
            return True
        except requests.RequestException as e:
            logger.error(f"Erro ao atualizar registro {record_id}: {e}")
            return False

    def download_attachment(self, url, local_path):
        """Baixa um arquivo de attachment do Airtable"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Arquivo baixado: {local_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"Erro ao baixar attachment: {e}")
            return False


# ============================================================================
# FOTOSHOP INTEGRATION
# ============================================================================


def run_extendscript(batch_name, png_path, output_dir, colors, design_name):
    """
    Executa o script ExtendScript no Photoshop via linha de comando

    Args:
        batch_name: Nome do batch (main, marketing, print)
        png_path: Caminho do PNG de artwork
        output_dir: Diretório de output
        colors: Lista de cores para tentar
        design_name: Nome do design

    Returns:
        bool: True se sucesso, False se erro
    """
    logger.info(f"Iniciando batch '{batch_name}' para {design_name}")

    os.makedirs(output_dir, exist_ok=True)

    # Preparar string de cores
    colors_str = ",".join(colors)

    # Construir comando para chamar Photoshop via CLI
    # Formato: photoshop.exe -r script.jsx -- "DesignName" "C:/png" "C:/psds" "C:/output" "Colors"
    cmd = [
        PHOTOSHOP_EXE,
        "-r",
        COMPOSER_JSX,
        "--",
        design_name,
        png_path,
        os.path.dirname(os.path.dirname(TEMPLATES_DIR_MAIN))
        + "/templates/"
        + batch_name,
        output_dir,
        colors_str,
    ]

    try:
        logger.debug(f"Executando: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos por batch
        )

        if result.returncode != 0:
            logger.error(f"ExtendScript falhou: {result.stderr}")
            return False

        logger.info(f"✓ Batch '{batch_name}' concluído")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout ao executar batch '{batch_name}'")
        return False
    except Exception as e:
        logger.error(f"Erro ao executar ExtendScript: {e}")
        return False


# ============================================================================
# IMAGE COMPRESSION
# ============================================================================


def compress_jpg(input_path, output_path, quality=85, max_width=2000):
    """
    Comprime um JPG usando Pillow

    Args:
        input_path: Caminho do JPG original
        output_path: Caminho do JPG comprimido
        quality: Qualidade JPEG (0-95)
        max_width: Largura máxima (redimensiona se maior)

    Returns:
        bool: True se sucesso
    """
    try:
        with Image.open(input_path) as img:
            # Redimensionar se necessário
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Salvar com qualidade reduzida
            img.save(output_path, "JPEG", quality=quality, optimize=True)

        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        reduction = (1 - compressed_size / original_size) * 100

        logger.debug(
            f"Comprimido: {Path(input_path).name} "
            f"({original_size / 1024:.0f}KB → {compressed_size / 1024:.0f}KB, "
            f"-{reduction:.1f}%)"
        )
        return True

    except Exception as e:
        logger.error(f"Erro ao comprimir {input_path}: {e}")
        return False


def compress_batch_jpgs(jpg_dir, output_dir):
    """Comprime todos os JPGs de um diretório"""
    os.makedirs(output_dir, exist_ok=True)

    jpg_files = list(Path(jpg_dir).glob("*.jpg"))
    if not jpg_files:
        logger.warning(f"Nenhum JPG encontrado em {jpg_dir}")
        return 0

    logger.info(f"Comprimindo {len(jpg_files)} arquivos JPG...")

    compressed_count = 0
    for jpg_file in jpg_files:
        output_file = Path(output_dir) / jpg_file.name
        if compress_jpg(str(jpg_file), str(output_file), quality=JPG_QUALITY):
            compressed_count += 1

    logger.info(f"✓ {compressed_count}/{len(jpg_files)} arquivos comprimidos")
    return compressed_count


# ============================================================================
# FTP UPLOAD
# ============================================================================


def upload_to_ftp(local_dir, remote_path):
    """
    Faz upload de todos os arquivos de um diretório para FTP

    Args:
        local_dir: Diretório local com arquivos
        remote_path: Caminho remoto no FTP (ex: uploads/DTG/artist/design)

    Returns:
        bool: True se sucesso
    """
    if not FTP_HOST or not FTP_USER or not FTP_PASS:
        logger.warning("Credenciais FTP não configuradas, pulando upload")
        return False

    files = list(Path(local_dir).glob("*.jpg"))
    if not files:
        logger.warning(f"Nenhum arquivo para upload em {local_dir}")
        return False

    try:
        ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS)
        logger.info(f"Conectado ao FTP: {FTP_HOST}")

        # Criar diretórios remotos se necessário
        try:
            ftp.cwd(remote_path)
        except ftplib.all_errors:
            # Criar recursivamente
            parts = remote_path.split("/")
            for part in parts:
                if part:
                    try:
                        ftp.cwd(part)
                    except ftplib.all_errors:
                        ftp.mkd(part)
                        ftp.cwd(part)

        # Upload de cada arquivo
        uploaded = 0
        for file_path in files:
            try:
                with open(file_path, "rb") as f:
                    ftp.storbinary(f"STOR {file_path.name}", f)
                    uploaded += 1
                    logger.debug(f"Upload: {file_path.name}")
            except Exception as e:
                logger.error(f"Erro ao fazer upload de {file_path.name}: {e}")

        ftp.quit()
        logger.info(f"✓ {uploaded}/{len(files)} arquivos enviados para FTP")
        return uploaded == len(files)

    except ftplib.all_errors as e:
        logger.error(f"Erro FTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado no FTP: {e}")
        return False


# ============================================================================
# FOLDER STRUCTURE
# ============================================================================


def create_design_folders(base_dir, design_name):
    """Cria a estrutura de pastas padrão para um design"""
    base_path = Path(base_dir) / design_name

    folders = [
        "00 - CSV",
        "00 - MARKETING",
        "01 - ORIGINAL/Apparel",
        "01 - ORIGINAL/Accessories",
        "02 - OPTIMIZED",
        "03 - ART FILES",
        "Print-Files",
    ]

    for folder in folders:
        folder_path = base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Pasta criada: {folder_path}")

    return {
        "base": str(base_path),
        "marketing": str(base_path / "00 - MARKETING"),
        "original_apparel": str(base_path / "01 - ORIGINAL/Apparel"),
        "original_accessories": str(base_path / "01 - ORIGINAL/Accessories"),
        "optimized": str(base_path / "02 - OPTIMIZED"),
        "print": str(base_path / "Print-Files"),
    }


# ============================================================================
# MAIN PROCESSING PIPELINE
# ============================================================================


def process_design(airtable, design_record, colors):
    """
    Processa um design: baixa PNG, roda ExtendScript 3x, comprime e faz upload

    Args:
        airtable: Instância de AirtableClient
        design_record: Registro do design do Airtable
        colors: Lista de cores a processar

    Returns:
        bool: True se sucesso
    """
    try:
        record_id = design_record["id"]
        fields = design_record["fields"]

        design_name = fields.get("Design Name", "Unknown")
        artist_name = fields.get("Artist Name", "Unknown")
        notes = fields.get("Notes", "")

        logger.info(f"=" * 70)
        logger.info(f"Processando design: {design_name} (Artista: {artist_name})")
        logger.info(f"=" * 70)

        # Atualizar status para "Processing"
        airtable.update_record(
            AIRTABLE_DESIGNS_TABLE, record_id, {"Status": "Processing"}
        )

        # --- Baixar PNG attachment ---
        attachments = fields.get("Design PNG", [])
        if not attachments:
            raise ValueError("Nenhum arquivo PNG encontrado no design")

        png_url = attachments[0]["url"]
        temp_dir = tempfile.mkdtemp()
        png_path = Path(temp_dir) / "design.png"

        if not airtable.download_attachment(png_url, str(png_path)):
            raise Exception("Falha ao baixar PNG")

        # --- Criar estrutura de pastas ---
        folders = create_design_folders(str(OUTPUT_BASE_DIR), design_name)

        # --- Rodar ExtendScript 3x (um por batch) ---
        batches = [
            ("main", folders["original_apparel"]),
            ("marketing", folders["marketing"]),
            ("print", folders["print"]),
        ]

        for batch_name, output_dir in batches:
            success = run_extendscript(
                batch_name, str(png_path), output_dir, colors, design_name
            )
            if not success:
                raise Exception(f"Falha ao processar batch '{batch_name}'")

        # --- Comprimir imagens ---
        compress_batch_jpgs(folders["original_apparel"], folders["optimized"])

        # --- Upload FTP ---
        ftp_path = f"{FTP_BASE_PATH}/{artist_name}/{design_name}"
        upload_to_ftp(folders["optimized"], ftp_path)

        # --- Limpar temp ---
        shutil.rmtree(temp_dir, ignore_errors=True)

        # --- Atualizar status para "Complete" ---
        airtable.update_record(
            AIRTABLE_DESIGNS_TABLE,
            record_id,
            {"Status": "Complete", "Notes": notes + " | ✓ Processado com sucesso"},
        )

        logger.info(f"✓ Design {design_name} concluído com sucesso")
        return True

    except Exception as e:
        logger.error(f"✗ Erro ao processar design: {e}")

        # Tentar atualizar status para "Error"
        try:
            airtable.update_record(
                AIRTABLE_DESIGNS_TABLE,
                record_id,
                {"Status": "Error", "Notes": f"{notes} | ✗ Erro: {str(e)}"},
            )
        except:
            pass

        return False


def fetch_colors_from_airtable(airtable):
    """Busca lista de cores da tabela Colors no Airtable"""
    logger.info("Buscando cores do Airtable...")

    records = airtable.get_records(AIRTABLE_COLORS_TABLE)
    if not records:
        logger.warning("Nenhuma cor encontrada no Airtable, usando colors.json local")
        return load_colors_from_json()

    colors = [
        record["fields"].get("Name") for record in records if "Name" in record["fields"]
    ]
    logger.info(f"✓ {len(colors)} cores carregadas do Airtable: {', '.join(colors)}")
    return colors


def load_colors_from_json():
    """Fallback: carrega cores do colors.json local"""
    colors_file = SCRIPT_DIR / "colors.json"
    try:
        with open(colors_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            colors = [color["name"] for color in data.get("colors", [])]
            logger.info(f"✓ {len(colors)} cores carregadas de colors.json")
            return colors
    except Exception as e:
        logger.error(f"Erro ao carregar colors.json: {e}")
        return ["Black", "Navy", "Grey", "White"]


# ============================================================================
# POLLING LOOP
# ============================================================================


def main():
    """Função principal — polling loop"""
    logger.info("=" * 70)
    logger.info("  PSD COMPOSER - Orquestrador Python")
    logger.info(f"  Intervalo de polling: {POLL_INTERVAL}s")
    logger.info("=" * 70)

    # Validar configuração
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        logger.error("AIRTABLE_API_KEY ou AIRTABLE_BASE_ID não configurados")
        sys.exit(1)

    if not os.path.exists(PHOTOSHOP_EXE):
        logger.error(f"Photoshop não encontrado em: {PHOTOSHOP_EXE}")
        sys.exit(1)

    if not os.path.exists(COMPOSER_JSX):
        logger.error(f"composer.jsx não encontrado em: {COMPOSER_JSX}")
        sys.exit(1)

    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)

    # Polling loop
    while True:
        try:
            logger.debug(f"Poll iniciada em {datetime.now()}")

            # Buscar cores
            colors = fetch_colors_from_airtable(airtable)

            # Buscar designs pendentes
            pending_designs = airtable.get_records(
                AIRTABLE_DESIGNS_TABLE, 'AND({Status} = "Pending")'
            )

            if pending_designs:
                logger.info(f"Encontrados {len(pending_designs)} design(s) pendente(s)")

                for design_record in pending_designs:
                    process_design(airtable, design_record, colors)
            else:
                logger.debug("Nenhum design pendente")

            # Aguardar antes do próximo poll
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Pipeline interrompido pelo usuário")
            break
        except Exception as e:
            logger.error(f"Erro no polling loop: {e}", exc_info=True)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
