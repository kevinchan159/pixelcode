import globals from './globals';
import {createWebview, createWebViewChangeLocationDelegate, createWindow} from './webview/webview';

function onRun (context) {
  var sketch = context.api();
  var app = NSApplication.sharedApplication();
  var layers = sketch.selectedDocument.selectedLayers;
  var exportsPath = globals['exportsPath'];
  var application = new sketch.Application(context);

  if (layers.isEmpty) {
    context.document.showMessage('Pixelcode: No artboard selected.');
  } else {
    var artboards = [];
    var assetNames = [];
    layers.iterate(function (layer) {
      if (layer.isArtboard) {
        // Add artboard name to list of artboards
        artboards.push(layer.name);
        var output = exportJSON(layer, exportsPath);
        exportImages(layer, exportsPath);
        assetNames = getAssetNames(layer, assetNames);

        var svgOptions = {
          'scales': '1',
          'formats': 'svg',
          'overwriting': 'true',
          'output': exportsPath
        };
        layer.export(svgOptions);

        var pngOptions = {
          'scales': '3',
          'formats': 'png',
          'overwriting': 'true',
          'output': exportsPath
        };
        layer.export(pngOptions);

        layer.iterate(function (currentLayer) {
          renameLayers(currentLayer, output['originalNames']);
        });

        context.document.showMessage('Pixelcode: Your design was translated successfully.');
      } else {
        context.document.showMessage('Pixelcode: No artboard selected.');
        return;
      }
    });
    NSApp.run();
  }
}

function exportImages (layer, filepath, assetNames) {
  var options = {
    'scales': '1',
    'formats': 'png',
    'overwriting': 'true',
    'output': filepath
  };
  if (layer.isImage) {
    layer.export(options);
  } else if (layer.isGroup) {
    layer.iterate(function (sublayer) {
      exportImages(sublayer, filepath, assetNames);
    });
  }
}

function getAssetNames (layer, assetNames) {
  if (layer.isImage) {
    assetNames.push(layer.name);
  } else if (layer.isGroup) {
    layer.iterate(function (sublayer) {
      assetNames = getAssetNames(sublayer, assetNames);
    });
  }
  return assetNames;
}

function cleanSVG (layer, exportsPath) {
  var svg = NSString.stringWithContentsOfFile(exportsPath + layer.name + '.svg');
  var cleanedSVG = removePathD(removeImageLinks(svg));
  var cleanedSVGString = NSString.stringWithString(cleanedSVG);
  cleanedSVGString.writeToFile_atomically_encoding_error(exportsPath + layer.name + '.svg', true, NSUTF8StringEncoding, null);
}

function removeImageLinks (svg) {
  var data_index = svg.indexOf("data:image/");
  if (data_index == -1) {
    return svg;
  } else {
    var end_index = svg.indexOf('"', data_index);
    return removeImageLinks(svg.substr(0, data_index) + svg.substr(end_index));
  }
}

function removePathD (svg) {
  var d_index = svg.indexOf('path d="M');
  if (d_index == -1) {
    return svg;
  } else {
    var end_index = svg.indexOf('"', d_index + 8);
    return removePathD(svg.substr(0, d_index + 8) + svg.substr(end_index));
  }
}

function updateProjects (context) {
  var sketch = context.api();
  var application = new sketch.Application(context);
  var contentsPath = context.scriptPath.stringByDeletingLastPathComponent().stringByDeletingLastPathComponent();
  var resourcesPath = contentsPath + '/Resources';
  var token = application.settingForKey('token');

  if (token == null) {
    context.document.showMessage('Pixelcode: No user logged in.');
    return;
  }

  var options = {'method': 'GET', headers: {'Authorization': 'Token ' + token}};
  fetch(globals.userProjectsRoute, options)
    .then(response => response.text())
    .then(text => {
      var responseJSON = JSON.parse(text);
      if (responseJSON.hasOwnProperty('detail')) {
        context.document.showMessage('Pixelcode: Failed to get projects.');
      } else {
        application.setSettingForKey('projects', text);
        var projectsStr = NSString.stringWithString(text);
        projectsStr.writeToFile_atomically_encoding_error(resourcesPath + '/projects.json', true, NSUTF8StringEncoding, null);
      }
    }).catch(error => {
      context.document.showMessage('Pixelcode: Failed to get projects.');
    });
}

function renameLayers (layer, originalNames) {
  layer.name = originalNames[layer.id];
  if (layer.isGroup) {
    layer.iterate(function (subLayer) {
      renameLayers(subLayer, originalNames);
    });
  }
}

function exportJSON (artboard, filepath) {
  var layerArray = [];
  var ret = { 'layerNames': [], 'dictList': [], 'originalNames': {} };

  artboard.iterate(function (layer) {
    exportImages(layer, filepath);

    var output = checkFormatting(layer, ret['layerNames'], ret['originalNames']);
    ret = output;

    for (var i = 0; i < ret['dictList'].length; i++) {
      layerArray.push(ret['dictList'][i]);
    }
  });

  // Create JSON and save to file
  var artboardName = artboard.name;
  var jsonObj = { layers: layerArray };
  var file = NSString.stringWithString(JSON.stringify(jsonObj, null, '\t'));
  file.writeToFile_atomically_encoding_error(filepath + artboardName + '.json', true, NSUTF8StringEncoding, null);
  return ret;
}

// Account for sublayers in checking formatting
function checkFormatting (layer, layerNames, originalNames) {
  var ret = {
    'layerNames': layerNames,
    'dictList': [],
    'originalNames': originalNames
  };
  var stack = [layer];

  while (stack.length >= 1) {
    var currentLayer = stack.pop();
    var originalName = String(currentLayer.name);
    ret['originalNames'][currentLayer.id] = originalName;

    var layerName = String(currentLayer.name.replace(/\s+/, ''));
    layerName = lowerCaseFirstChar(layerName);

    if (arrayContains(layerName, ret['layerNames'])) {
      var name = layerName;
      var counter = 1;
      while (arrayContains(name, ret['layerNames'])) {
        name = layerName + counter;
        counter++;
      }
      layerName = name;
    }

    currentLayer.name = layerName;

    var currentDict = {};
    currentDict['originalName'] = originalName;
    currentDict['name'] = layerName;
    currentDict['x'] = String(currentLayer.frame.x);
    currentDict['y'] = String(currentLayer.frame.y);
    currentDict['height'] = String(currentLayer.frame.height);
    currentDict['width'] = String(currentLayer.frame.width);
    if (currentLayer.isText) {
      currentDict['text_align'] = String(currentLayer.alignment);
    }

    currentDict['abs_x'] = getAbsoluteX(currentLayer, currentLayer.frame.x);
    currentDict['abs_y'] = getAbsoluteY(currentLayer, currentLayer.frame.y);

    ret['layerNames'].push(layerName);
    ret['dictList'].push(currentDict);

    if (currentLayer.isGroup) {
      currentLayer.iterate(function (subLayer) {
        stack.push(subLayer);
      });
    }
  }
  return ret;
}

function getAbsoluteX (layer, x) {
  if (layer.container.isArtboard) {
    return x;
  } else {
    return getAbsoluteX(layer.container, x + layer.container.frame.x);
  }
}

function getAbsoluteY (layer, y) {
  if (layer.container.isArtboard) {
    return y;
  } else {
    return getAbsoluteY(layer.container, y + layer.container.frame.y);
  }
}

function hasWhiteSpace (s) {
  return s.indexOf(' ') >= 0;
}

function arrayContains (needle, arrhaystack) {
  return (arrhaystack.indexOf(needle) > -1);
}

function lowerCaseFirstChar (string) {
  return string.charAt(0).toLowerCase() + string.slice(1);
}

export default onRun;
