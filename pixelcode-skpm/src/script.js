import globals from './globals';
import {createWebViewChangeLocationDelegate, createWindow, createWebView} from './webview/webview';

function onRun (context) {
  var sketch = context.api();
  var app = NSApplication.sharedApplication();
  var layers = sketch.selectedDocument.selectedLayers;
  //var filepath = "/Users/Young/Documents/pixelcode/app/tests/";
  var filepath = globals.filepath;
  var exportsPath = globals.exportsPath;
  var application = new sketch.Application(context);

  context.document.showMessage('Working!!!');

  // fetch('https://google.com')
  //   .then(response => response.text())
  //   .then(text => console.log(text));

  log("begins here:");
  log(application.settingForKey("token"));
  application.setSettingForKey("token", null);
  if (application.settingForKey("token") == null) {
    var window_ = createWindow(520, 496);
    var webView = createWebView(context, window_, 'index.html', 520, 496);
    // createWebViewRedirectDelegate(application, context, webView);
    createWebViewChangeLocationDelegate(application, context, webView);

    NSApp.run();
    return;
  }
  //
  // if (application.settingForKey("projects") == null) {
  //   updateProjects(context);
  // }
  //
  // log("Exporting now:")
  // if (layers.isEmpty) {
  //   context.document.showMessage("PixelCode: No artboard selected.");
  // } else {
  //   var artboards = [];
  //   layers.iterate(function(layer) {
  //       if (layer.isArtboard) {
  //           // Add artboard name to list of artboards
  //           artboards.push(layer.name);
  //           // log("Creating project folder in exports");
  //           // Create project folder in exports directory
  //           // var fileManager = [[NSFileManager alloc] init];
  //           // var projectDirectory = exportsPath + layer.name + '/';
  //           // log("project directory is:")
  //           // log(projectDirectory);
  //           // [fileManager createDirectoryAtPath:projectDirectory withIntermediateDirectories:false attributes:nil error:nil];
  //           // // Create assets folder in project directory
  //           // [fileManager createDirectoryAtPath:projectDirectory+'/assets/' withIntermediateDirectories:false attributes:nil error:nil];
  //           // output = exportJSON(layer, filepath);
  //           output = exportJSON(layer, exportsPath);
  //
  //           var options = {
  //               "scales" : "1",
  //               "formats" : "svg",
  //               "overwriting" : "true",
  //               //"output": filepath
  //               "output": exportsPath
  //           };
  //           layer.export(options);
  //           layer.iterate(function(currentLayer) {
  //               renameLayers(currentLayer, output["originalNames"]);
  //           });
  //           context.document.showMessage("Pixelcode: Export finished!");
  //       } else {
  //           context.document.showMessage("Pixelcode: No artboard selected.");
  //           return;
  //       }
  //   });
  //   // Create artboards.json
  //   createArtboardsJSON(artboards);
  //   // Get projects and open export window
  //   var projects = JSON.parse(application.settingForKey("projects"));
  //   var window_ = createWindow(560, 496);
  //   var webView = createWebView(context, window_, 'export.html', 560, 496);
  //   createWebViewChangeLocationDelegate(application, context, webView);
  //   [NSApp run];
  //   return;
  // };
}

export default onRun;
