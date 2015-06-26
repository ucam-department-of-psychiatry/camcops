/*jslint node: true */
"use strict";
/*global Titanium */

function rowClicked(e) {
    Titanium.API.trace("ROW CLICKED: e = " + JSON.stringify(e));
}

var with_sections = true,
    sectionOne = Titanium.UI.createTableViewSection({
        headerTitle: 'section_one'
    }),
    sectionTwo = Titanium.UI.createTableViewSection({
        headerTitle: 'section_two'
    }),
    tableview = Titanium.UI.createTableView({
        height: Titanium.UI.FILL,
        width: Titanium.UI.FILL,
        top: 0,
        showVerticalScrollIndicator: true,
        minRowHeight: 48,
    }),
    rowOne = Titanium.UI.createTableViewRow({
        title: 'row_one'
    }),
    rowTwo = Titanium.UI.createTableViewRow({
        title: 'row_two'
    }),
    win = Titanium.UI.createWindow({ backgroundColor:  '#fff' });

if (with_sections) {
    sectionOne.add(rowOne);
    sectionTwo.add(rowTwo);
    tableview.setData([sectionOne, sectionTwo]);
} else {
    tableview.setData([rowOne, rowTwo]);
}
tableview.addEventListener('click', rowClicked);
win.add(tableview);
win.open();

// Vary with_sections

// https://jira.appcelerator.org/browse/TC-5071
