// test_html_to_attributed_string.jsx

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var html_to_attributed_string = require("lib/html_to_attributed_string"),
    html1 = "text <b>bold</b> not bold",
    as1 = html_to_attributed_string.parseSynchronous(html1),
    label1 = Titanium.UI.createLabel({
        attributedString: as1
    }),
    win = Titanium.UI.createWindow({
        title: 'Tab 2',
        backgroundColor: '#fff'
    });

win.add(label1);
win.open();
