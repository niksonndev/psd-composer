#!/usr/bin/env python3
"""
PSD Composer - Orquestrador Python
Lê colors.json e executa o script ExtendScript no Photoshop
"""

import json
import subprocess
import sys
import os
from pathlib import Path

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
COLORS_FILE = SCRIPT_DIR / "colors.json"
COMPOSER_SCRIPT = SCRIPT_DIR / "composer.jsx"

# ============================================================================
# FUNÇÕES
# ============================================================================

def load_colors():
    """Carrega lista de cores do colors.json"""
    print("[INFO] Carregando cores de colors.json...")
    
    try:
        with open(COLORS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            colors = [color["name"] for color in data["colors"]]
            print(f"[INFO] {len(colors)} cores carregadas: {', '.join(colors)}")
            return colors
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {COLORS_FILE}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[ERRO] JSON inválido em: {COLORS_FILE}")
        sys.exit(1)


def run_extendscript(design_name, psd_path, output_dir):
    """
    Executa o script ExtendScript no Photoshop
    
    Args:
        design_name: Nome do design/projeto
        psd_path: Caminho completo do arquivo PSD
        output_dir: Diretório para salvar exports
    """
    print(f"\n[INFO] Iniciando exportação: {design_name}")
    print(f"  PSD: {psd_path}")
    print(f"  Output: {output_dir}")
    
    # Criar diretório de output se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # Preparar argumentos para o script
    # Nota: Em um projeto real, seria necessário passar os argumentos
    # de forma mais robusta (ex: via arquivo de config ou API do PS)
    args = [
        f'"{COMPOSER_SCRIPT}"',
        f'"{psd_path}"',
        f'"{output_dir}"',
        f'"{design_name}"'
    ]
    
    print(f"[DEBUG] Script: {COMPOSER_SCRIPT}")
    
    # Executar via Adobe Photoshop
    # Nota: Este é um exemplo conceitual. A execução real depende
    # de como você vai chamar o ExtendScript (via PS CLI, VBScript, etc)
    try:
        # Exemplo: usando subprocess para chamar psunidcode ou similar
        # Este é um placeholder para a integração real
        print("[INFO] [PLACEHOLDER] Executando ExtendScript no Photoshop...")
        print("[INFO] (Integração real com Photoshop será implementada)")
        
        # Em produção, você usaria algo como:
        # subprocess.run(["psunidcode", ...], check=True)
        
        print(f"[INFO] ✓ Exportação concluída para: {output_dir}")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha na execução: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        sys.exit(1)


def main():
    """Função principal"""
    print("=" * 70)
    print("  PSD COMPOSER - Orquestrador Python")
    print("=" * 70)
    
    # Carregar cores
    colors = load_colors()
    
    # Exemplo de uso (comentado - será preenchido com parâmetros reais)
    # design_name = "MyDesign"
    # psd_path = "C:/designs/mydesign.psd"
    # output_dir = "C:/output/exports"
    # run_extendscript(design_name, psd_path, output_dir)
    
    print("\n[INFO] Configuração inicial concluída!")
    print("[INFO] Para usar, chame: run_extendscript(design_name, psd_path, output_dir)")
    print("=" * 70)


if __name__ == "__main__":
    main()
