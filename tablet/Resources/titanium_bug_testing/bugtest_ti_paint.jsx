/*jslint node: true */
"use strict";
/*global Titanium */

var Paint = require('ti.paint');

var win = Titanium.UI.createWindow({ backgroundColor:  '#fff' });
var paintViewProps = {
    top: 0,
    right: 0,
    bottom: 80,
    left: 0,
    // strokeWidth (float), strokeColor (string), strokeAlpha (int, 0-255)
    strokeColor: '#0f0',
    strokeAlpha: 255,
    strokeWidth: 10,
    eraseMode: false
};
var paintView = Paint.createPaintView(paintViewProps);
win.add(paintView);

var buttonStrokeWidth = Titanium.UI.createButton({ left: 10, bottom: 10, right: 10, height: 30, title: 'Decrease Stroke Width' });
buttonStrokeWidth.addEventListener('click', function (e) {
    paintView.strokeWidth = (paintView.strokeWidth === 10) ? 5 :  10;
    e.source.title = (paintView.strokeWidth === 10) ? 'Decrease Stroke Width' :  'Increase Stroke Width';
});
win.add(buttonStrokeWidth);

var buttonStrokeColorRed = Titanium.UI.createButton({ bottom: 100, left: 10, width: 75, height: 30, title: 'Red' });
buttonStrokeColorRed.addEventListener('click', function () { paintView.strokeColor = 'red'; });
var buttonStrokeColorGreen = Titanium.UI.createButton({ bottom: 70, left: 10, width: 75, height: 30, title: 'Green' });
buttonStrokeColorGreen.addEventListener('click', function () { paintView.strokeColor = '#0f0'; });
var buttonStrokeColorBlue = Titanium.UI.createButton({ bottom: 40, left: 10, width: 75, height: 30, title: 'Blue' });
buttonStrokeColorBlue.addEventListener('click', function () { paintView.strokeColor = '#0000ff'; });
win.add(buttonStrokeColorRed);
win.add(buttonStrokeColorGreen);
win.add(buttonStrokeColorBlue);

var clear = Titanium.UI.createButton({ bottom: 40, left: 100, width: 75, height: 30, title: 'Clear' });
clear.addEventListener('click', function () { paintView.clear(); });
win.add(clear);

var buttonStrokeAlpha = Titanium.UI.createButton({ bottom: 70, right: 10, width: 100, height: 30, title: 'Alpha :  100%' });
buttonStrokeAlpha.addEventListener('click', function (e) {
    paintView.strokeAlpha = (paintView.strokeAlpha === 255) ? 127 :  255;
    e.source.title = (paintView.strokeAlpha === 255) ? 'Alpha :  100%' :  'Alpha :  50%';
});
win.add(buttonStrokeAlpha);

var buttonStrokeColorEraser = Titanium.UI.createButton({ bottom: 40, right: 10, width: 100, height: 30, title: 'Erase :  Off' });
buttonStrokeColorEraser.addEventListener('click', function (e) {
    paintView.eraseMode = (paintView.eraseMode) ? false :  true;
    e.source.title = (paintView.eraseMode) ? 'Erase :  On' :  'Erase :  Off';
});
win.add(buttonStrokeColorEraser);

// RNC:
var setImageButton = Titanium.UI.createButton({ bottom:  70, left:  200, right:  200, height: 30, title: 'SET IMAGE' });
setImageButton.addEventListener('click', function () {
    var platform = require('lib/platform'),
        image = "images/expdet/V_cue_07.png";
    if (platform.android) {
        win.remove(paintView);
        paintView = null;
        paintViewProps.image = image;
        paintView = Paint.createPaintView(paintViewProps);
        win.add(paintView);
    } else {
        paintView.setImage(image); // fine on iOS
        // On Android:
        // ... either a simple crash probably relating to a duff filename (e.g. leading '/'), or:
        // Uncaught Error:  Only te original thread that created a view hierarchy can touch its views.
    }
});
win.add(setImageButton);

win.open();
