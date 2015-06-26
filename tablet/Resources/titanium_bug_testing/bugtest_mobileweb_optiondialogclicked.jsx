/*jslint node: true */
"use strict";
/*global Titanium */

function popupSelected(e) {
    Titanium.API.trace("OPTION CLICKED: e = " + JSON.stringify(e));
}

var opts = {
        options: ["one", "two", "three"],
        cancel: -1, // disable cancel option
    },
    dialog = Titanium.UI.createOptionDialog(opts),
    popupListener = function (e) { popupSelected(e); },
    win = Titanium.UI.createWindow({ backgroundColor:  '#fff' });

dialog.addEventListener("click", popupListener);
win.open();
dialog.show();

// https://jira.appcelerator.org/browse/TC-5065
