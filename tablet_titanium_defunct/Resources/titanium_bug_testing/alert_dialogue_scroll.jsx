/*jslint node: true */

"use strict";
/*global Titanium */

function repeatString(s, n) {
    var x = "",
        i;
    for (i = 0; i < n; i += 1) {
        x += s;
    }
    return x;
}

var alertDlg,
    win = Titanium.UI.createWindow({ backgroundColor: '#fff' });

win.open();
alertDlg = Titanium.UI.createAlertDialog({
    message: repeatString("Repeat me", 1000),
    title: "Alert dialogue test",
    buttonNames: ["OK"]
});

/*
Alerts with large content no longer scroll (RNC discovered 2015-01-30).
NOT A TITANIUM BUG, apparently:
    https://jira.appcelerator.org/browse/TIMOB-17745
*/
