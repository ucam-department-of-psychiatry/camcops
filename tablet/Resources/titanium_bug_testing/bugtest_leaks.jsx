// bugtest_table_events_ios_v_android.js

/*jslint node: true */
/*global Titanium */

var label = Titanium.UI.createLabel({
    text: "label"
});

var view = Titanium.UI.createView({
    backgroundColor: '#FFFFFF'
});

view.add(label);

var win = Titanium.UI.createWindow();
win.add(view);

win.open();
