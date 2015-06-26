/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var items = ["one", "two", "three", "four", "five"],
    data = [],
    i,
    section = Titanium.UI.createListSection(),
    listView;

for (i = 0; i < items.length; ++i) {
    data.push({ properties: {
        itemId: i,
        title: items[i],
        searchableText: items[i],
    }});
}
section.setItems(data);
var listView = Titanium.UI.createListView({
    canScroll: true,
    caseInsensitiveSearch: true,
    searchView: Titanium.UI.createSearchBar({
        top: 0,
        left: 0,
        height: 45,
        showCancel: false,
    }),
    sections: [section],
});
listView.addEventListener('itemclick', function (e) {
    Titanium.API.trace(
        "itemclick from listView: e.itemIndex = " +
            JSON.stringify(e.itemIndex) +
            ", e.sectionIndex = " +
            JSON.stringify(e.sectionIndex) +
            ", e.itemId = " +
            JSON.stringify(e.itemId)
    );
});
var win = Titanium.UI.createWindow({ backgroundColor: '#fff' });
win.add(listView);
win.open();

// ANDROID 4.1.1/Titanium 3.2.0: When a listview is filtered, itemId remains unchanged, but itemIndex is the index of the filtered content (e.g. always 0 if you've filtered down to one thing).
// iOS 7.0.3/Titanium 3.2.0: When a listview is filtered, itemIndex continues to reference the unfiltered list.
