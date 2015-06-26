/*jslint node: true */
/*global Titanium */

var win = Titanium.UI.createWindow({
        navBarHidden: true,
        fullscreen: true,
        backgroundColor: '#FFFFFF',
        orientationModes: [],
    }),
    mainview = Titanium.UI.createView({
        top: 0,
        left: 0,
        height: Titanium.UI.FILL,
        width: Titanium.UI.FILL,
        layout: 'vertical',
    }),
    rule = Titanium.UI.createView({
        left: 0,
        top: 50,
        height: 2,
        width: Titanium.UI.FILL,
        backgroundColor: '#808080',
        touchEnabled: false,
    }),
    scrollview = Titanium.UI.createScrollView({
        left: 16,
        right: 16,
        top: 0,
        height: Titanium.UI.FILL,
        layout: 'vertical',
        scrollType: 'vertical',
        contentHeight: 'auto',
        showVerticalScrollIndicator: true,
        showHorizontalScrollIndicator: false,
        backgroundColor: '#00FF00',
    }),
    string1 = (
        "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. " +
            "This is a very long string. "
    ),
    string2 = "This is a short string.",
    nlabels = 2,
    i,
    label;

win.open();
win.add(mainview);
mainview.add(rule);
mainview.add(scrollview);
for (i = 0; i < nlabels; i += 1) {
    label = Titanium.UI.createLabel({
        left: 0,
        top: 16,
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        height: Titanium.UI.SIZE,
        touchEnabled: false,
        backgroundColor: '#FF0000',
        text: string1,
        // text: string2,
    });
    scrollview.add(label);
}
