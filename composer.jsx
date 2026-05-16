#target photoshop

/**
 * PSD Composer - ExtendScript para automação de exportação em Photoshop
 * Busca layers, troca artwork e exporta em diferentes cores
 */

// ============================================================================
// FUNÇÕES AUXILIARES
// ============================================================================

/**
 * Busca recursivamente um layer pelo nome em uma lista de layers
 * @param {Array} layers - Array de layers para buscar
 * @param {String} name - Nome do layer a procurar
 * @returns {Layer|null} - Layer encontrado ou null
 */
function findLayer(layers, name) {
  for (var i = 0; i < layers.length; i++) {
    var layer = layers[i];
    
    // Verifica se o nome corresponde
    if (layer.name === name) {
      return layer;
    }
    
    // Se é um grupo/folder, busca recursivamente
    if (layer.typename === "LayerSet") {
      var found = findLayer(layer.layers, name);
      if (found !== null) {
        return found;
      }
    }
  }
  
  return null;
}

/**
 * Exporta documento como JPG com qualidade especificada
 * @param {Document} doc - Documento a exportar
 * @param {String} outputPath - Caminho completo do arquivo de saída (ex: C:/output/design.jpg)
 * @param {Number} quality - Qualidade JPEG (0-12, padrão 10)
 */
function exportJPG(doc, outputPath, quality) {
  quality = quality || 10;
  
  // Configurar opções de exportação JPG via Save for Web
  var jpgFile = new File(outputPath);
  var exportOptions = new ExportOptionsSaveForWeb();
  exportOptions.quality = quality;
  
  // Exportar documento como JPG
  doc.exportDocument(jpgFile, ExportType.SAVEFORWEB, exportOptions);
  
  $.writeln("Exportado: " + outputPath);
}

// ============================================================================
// FLUXO PRINCIPAL (COMENTADO - SERÁ IMPLEMENTADO)
// ============================================================================

/*
// 1. Abrir PSD
var psdPath = "C:/path/to/design.psd";
var doc = app.open(File(psdPath));

// 2. Array de cores para iterar
var colors = ["Black", "Navy", "Grey", "White", "Maroon"];

// 3. Para cada cor
for (var c = 0; c < colors.length; c++) {
  var colorName = colors[c];
  
  // 4. Encontrar e atualizar layer de artwork
  var artworkLayer = findLayer(doc.layers, "artwork");
  if (artworkLayer) {
    artworkLayer.visible = true;
    // [Aqui viria lógica para trocar cor/conteúdo do layer]
  }
  
  // 5. Exportar como JPG
  var outputPath = "C:/output/design_" + colorName + ".jpg";
  exportJPG(doc, outputPath, 10);
}

// 6. Fechar documento sem salvar
doc.close(SaveOptions.DONOTSAVECHANGES);

alert("Processo concluído!");
*/

// Script carregado com sucesso
$.writeln("Composer.jsx carregado com sucesso no Photoshop");
