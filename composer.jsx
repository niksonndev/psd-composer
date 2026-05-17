#target photoshop

/**
 * PSD Composer - ExtendScript para automação de exportação em Photoshop
 * Busca layers, troca artwork via Smart Object e exporta em diferentes cores
 *
 * Uso via Python (main.py):
 *   photoshop.exe -r composer.jsx -- "DesignName" "C:/png" "C:/psds" "C:/output" "Black,Navy,Grey"
 *
 * Uso manual (F5 no VS Code com Photoshop aberto):
 *   Edita as variáveis em CONFIG abaixo e roda
 */

// ============================================================================
// CONFIG — edita aqui para testes manuais
// ============================================================================

var CONFIG = {
  designName : "Iron-Aran",
  pngPath    : "C:/psd-composer/assets/designs/iron-aran.png",
  templatesDir: "C:/psd-composer/assets/templates",
  outputDir  : "C:/psd-composer/assets/output",
  colors     : ["Black", "Navy", "Grey", "White", "Maroon"],

  // Nomes dos layers no PSD — ajusta conforme o PSD real do cliente
  artworkLayerName: "ARTWORK",
  colorLayerPrefix: "COLOR_"
};

// ============================================================================
// FUNÇÕES AUXILIARES
// ============================================================================

/**
 * Busca recursivamente um layer pelo nome
 * @param {Object} layers - Coleção de layers do documento ou grupo
 * @param {String} name - Nome exato do layer
 * @returns {Layer|null}
 */
function findLayer(layers, name) {
  for (var i = 0; i < layers.length; i++) {
    var layer = layers[i];

    if (layer.name === name) {
      return layer;
    }

    if (layer.typename === "LayerSet") {
      var found = findLayer(layer.layers, name);
      if (found !== null) return found;
    }
  }
  return null;
}

/**
 * Exporta o documento ativo como JPG
 * @param {Document} doc
 * @param {String} outputPath - Caminho completo do arquivo de saída
 * @param {Number} quality - Qualidade JPEG 0-12 (padrão 10)
 */
function exportJPG(doc, outputPath, quality) {
  quality = quality || 10;

  var jpgFile = new File(outputPath);
  var opts = new JPEGSaveOptions();
  opts.quality = quality;
  opts.embedColorProfile = true;
  opts.formatOptions = FormatOptions.STANDARDBASELINE;
  opts.matte = MatteType.NONE;

  doc.saveAs(jpgFile, opts, true); // true = salva cópia, não altera o PSD
  $.writeln("[OK] Exportado: " + outputPath);
}

/**
 * Substitui o conteúdo de um Smart Object com um PNG externo
 * @param {Document} doc - Documento pai
 * @param {Layer} smartObjLayer - Layer do tipo Smart Object
 * @param {String} pngPath - Caminho do PNG de artwork
 */
function replaceSmartObjectContent(doc, smartObjLayer, pngPath) {
  doc.activeLayer = smartObjLayer;

  // Abre o Smart Object para edição interna
  var idEdit = stringIDToTypeID("placedLayerEditContents");
  executeAction(idEdit, undefined, DialogModes.NO);

  var smartDoc = app.activeDocument;

  // Remove layers existentes dentro do Smart Object
  while (smartDoc.layers.length > 1) {
    smartDoc.layers[smartDoc.layers.length - 1].remove();
  }

  // Coloca o PNG como novo conteúdo
  var pngFile = new File(pngPath);
  var placed = smartDoc.place(pngFile);

  // Centraliza e confirma o place
  placed.translate(
    -placed.bounds[0] + (smartDoc.width - placed.bounds[2] + placed.bounds[0]) / 2,
    -placed.bounds[1] + (smartDoc.height - placed.bounds[3] + placed.bounds[1]) / 2
  );
  placed.rasterize(RasterizeType.ENTIRELAYER);

  // Fecha o Smart Object salvando as alterações de volta no PSD pai
  smartDoc.close(SaveOptions.SAVECHANGES);

  $.writeln("[OK] Artwork aplicado: " + pngPath);
}

/**
 * Ativa uma cor no PSD escondendo todas as outras
 * @param {Document} doc
 * @param {Array} colors - Lista completa de cores
 * @param {String} activeColor - Cor a ativar
 * @returns {Boolean} - false se a cor não existir nesse PSD (skip silencioso)
 */
function setActiveColor(doc, colors, activeColor) {
  var targetLayer = findLayer(doc.layers, CONFIG.colorLayerPrefix + activeColor);

  if (!targetLayer) {
    $.writeln("[SKIP] Cor '" + activeColor + "' não encontrada nesse PSD");
    return false;
  }

  // Esconde todas as cores primeiro
  for (var i = 0; i < colors.length; i++) {
    var layer = findLayer(doc.layers, CONFIG.colorLayerPrefix + colors[i]);
    if (layer) layer.visible = false;
  }

  // Mostra só a cor ativa
  targetLayer.visible = true;
  return true;
}

/**
 * Garante que a pasta de output existe, criando se necessário
 * @param {String} path
 */
function ensureFolder(path) {
  var folder = new Folder(path);
  if (!folder.exists) {
    folder.create();
    $.writeln("[OK] Pasta criada: " + path);
  }
}

/**
 * Retorna todos os PSDs de uma pasta
 * @param {String} folderPath
 * @returns {Array} - Array de File
 */
function getPSDFiles(folderPath) {
  var folder = new Folder(folderPath);
  if (!folder.exists) {
    $.writeln("[ERRO] Pasta de templates não encontrada: " + folderPath);
    return [];
  }
  return folder.getFiles("*.psd");
}

// ============================================================================
// LOOP PRINCIPAL
// ============================================================================

/**
 * Processa um PSD: aplica artwork e exporta uma vez por cor disponível
 * @param {File} psdFile
 * @param {String} pngPath
 * @param {String} designName
 * @param {Array} colors
 * @param {String} outputDir
 */
function processPSD(psdFile, pngPath, designName, colors, outputDir) {
  $.writeln("\n── Processando: " + psdFile.name);

  var doc = app.open(psdFile);

  // Busca o layer de artwork
  var artworkLayer = findLayer(doc.layers, CONFIG.artworkLayerName);
  if (!artworkLayer) {
    $.writeln("[ERRO] Layer '" + CONFIG.artworkLayerName + "' não encontrado — pulando");
    doc.close(SaveOptions.DONOTSAVECHANGES);
    return;
  }

  // Aplica o PNG no Smart Object
  replaceSmartObjectContent(doc, artworkLayer, pngPath);

  // Extrai o product code do nome do arquivo PSD (ex: "Men-Tshirt.psd" → "Men-Tshirt")
  var productCode = psdFile.name.replace(".psd", "");

  // Itera cada cor
  for (var c = 0; c < colors.length; c++) {
    var colorName = colors[c];
    var applied = setActiveColor(doc, colors, colorName);

    if (!applied) continue;

    // Monta nome final: DesignName-ProductCode-Color.jpg
    var fileName = designName + "-" + productCode + "-" + colorName + ".jpg";
    var outputPath = outputDir + "/" + fileName;

    exportJPG(doc, outputPath, 10);
  }

  doc.close(SaveOptions.DONOTSAVECHANGES);
  $.writeln("── Concluído: " + psdFile.name);
}

/**
 * Entry point — roda o pipeline completo
 */
function main() {
  $.writeln("========================================");
  $.writeln("PSD Composer iniciado");
  $.writeln("Design : " + CONFIG.designName);
  $.writeln("PNG    : " + CONFIG.pngPath);
  $.writeln("PSDs   : " + CONFIG.templatesDir);
  $.writeln("Output : " + CONFIG.outputDir);
  $.writeln("Cores  : " + CONFIG.colors.join(", "));
  $.writeln("========================================\n");

  // Garante que a pasta de output existe
  ensureFolder(CONFIG.outputDir);

  // Busca todos os PSDs na pasta de templates
  var psdFiles = getPSDFiles(CONFIG.templatesDir);
  if (psdFiles.length === 0) {
    $.writeln("[ERRO] Nenhum PSD encontrado em: " + CONFIG.templatesDir);
    return;
  }

  $.writeln("PSDs encontrados: " + psdFiles.length + "\n");

  // Processa cada PSD
  for (var i = 0; i < psdFiles.length; i++) {
    processPSD(
      psdFiles[i],
      CONFIG.pngPath,
      CONFIG.designName,
      CONFIG.colors,
      CONFIG.outputDir
    );
  }

  $.writeln("\n========================================");
  $.writeln("Pipeline concluído!");
  $.writeln("========================================");
}

// Roda
main();