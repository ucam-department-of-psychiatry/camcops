/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

// First, deal with bug with custom module that implements the reverted version of TextArea as per https://jira.appcelerator.org/browse/TIMOB-15535
var textAreaCreator = Titanium.UI.createTextArea;
if (Titanium.Platform.osname === 'android') {
    textAreaCreator = require('org.camcops.androidtibugfix').createTextArea; // custom module
}

// Now, onwards...

var n_things_of_each_kind = 20,
    labels = [],
    textcontent = "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
    view = Titanium.UI.createScrollView({ layout: 'vertical', backgroundColor: '#FFFFFF' }),
    smallbutton = Titanium.UI.createButton({ title: "small" }),
    bigbutton = Titanium.UI.createButton({ title: "big" }),
    visiblebutton = Titanium.UI.createButton({ title: "visible" }),
    invisiblebutton = Titanium.UI.createButton({ title: "invisible" }),
    i,
    newlabel;

smallbutton.addEventListener("click", function () {
    var i;
    for (i = 0; i < n_things_of_each_kind; ++i) {
        labels[i].setFont({ fontSize: 10 });
    }
});
view.add(smallbutton);

bigbutton.addEventListener("click", function () {
    var i;
    for (i = 0; i < n_things_of_each_kind; ++i) {
        labels[i].setFont({ fontSize: 20 });
    }
});
view.add(bigbutton);

function setVisibility(visible) {
    var i;
    for (i = 0; i < n_things_of_each_kind; ++i) {
        labels[i].setVisible(visible);
    }
}

visiblebutton.addEventListener("click", function () { setVisibility(true); });
view.add(visiblebutton);

invisiblebutton.addEventListener("click", function () { setVisibility(false); });
view.add(invisiblebutton);

for (i = 0; i < n_things_of_each_kind; ++i) {
    newlabel = Titanium.UI.createLabel({
        text: textcontent,
        color: '#000000',
        left: 0,
        top: 0,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.FILL,
    });
    labels.push(newlabel);
    view.add(newlabel);

    view.add(textAreaCreator({
        top: 0,
        left: 0,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.FILL,
        backgroundColor: '#888888',
        suppressReturn: false, // multiline
        autocapitalization: Titanium.UI.TEXT_AUTOCAPITALIZATION_NONE,
        autocorrect: false, // we're not measuring the spellchecker's speed
    }));
}

var win = Titanium.UI.createWindow();
win.add(view);
win.open();

/*

All with Titanium 3.2.0 (plus bugfix for Android multiline as per https://jira.appcelerator.org/browse/TIMOB-15535):

- iOS simulator (iOS 7.0.3) on Mac Mini 2.5GHz Intel Core i5 / OS X 10.8.5:
    visible lag with font size/visibility changes (ripple effect as each element changes one by one);
    sometimes, textarea contents suddenly go partially blank (e.g. typing a large number of short lines)
        then resolve with further keystrokes;
    textarea typing speed OK (very slightly perceptible lag)

- iPad 2 (iOS 7.0.4):
    marked lag/ripple with font size changes/visibility
    similarly, textarea contents sometimes partially vanish (in similar circumstances) then reappear
        with more keystrokes (not spontaneously)
    very marked lag when typing (significantly impairs utility)

- Asus Eee Pad Transformer Prime TF201 (Android 4.1.1):
    font size/visibility changes are instant/synchronous
    textarea contents do not disappear/reappear
    textarea typing speed fine (lag imperceptible)

*/
