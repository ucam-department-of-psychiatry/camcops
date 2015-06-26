// bugtest_table_events_singletap_doubletap_click.js

/*jslint node: true */
"use strict";
/*global Titanium */

function eventArrived(e) {
    Titanium.API.trace("Event from table: " + JSON.stringify(e));
}

var rowdata = [
    {title: "row_0"},
    {title: "row_1"},
    {title: "row_2"},
];
var win = Titanium.UI.createWindow({ backgroundColor: '#FFFFFF' });
var table = Titanium.UI.createTableView({ data: rowdata });

// Either:

//table.addEventListener('singletap', eventArrived);
//table.addEventListener('doubletap', eventArrived);

// Or:

table.addEventListener('click', eventArrived);

win.add(table);
win.open();


/*

TEST RIG:

Test date: 15 Oct 2013
Platform: Mac OS X 10.8.5
Titanium Studio, build: 3.1.3.201309132423

TESTING:

Run, then tap/click and/or double-tap the three rows in order.

OUTPUT:

With singletap and doubletap events:

[TRACE] :  Event from table: {"x":222,"y":31,"bubbles":true,"type":"singletap","source":{"hideSearchOnSelection":true,"horizontalWrap":true,"searchHidden":false},"cancelBubble":false}
[TRACE] :  Event from table: {"x":91,"y":61,"bubbles":true,"type":"singletap","source":{"hideSearchOnSelection":true,"horizontalWrap":true,"searchHidden":false},"cancelBubble":false}
[TRACE] :  Event from table: {"x":145,"y":101,"bubbles":true,"type":"singletap","source":{"hideSearchOnSelection":true,"horizontalWrap":true,"searchHidden":false},"cancelBubble":false}
[TRACE] :  Event from table: {"x":137,"y":22,"bubbles":true,"type":"doubletap","source":{"hideSearchOnSelection":true,"horizontalWrap":true,"searchHidden":false},"cancelBubble":false}
[TRACE] :  Event from table: {"x":130,"y":73,"bubbles":true,"type":"doubletap","source":{"hideSearchOnSelection":true,"horizontalWrap":true,"searchHidden":false},"cancelBubble":false}
[TRACE] :  Event from table: {"x":129,"y":100,"bubbles":true,"type":"doubletap","source":{"hideSearchOnSelection":true,"horizontalWrap":true,"searchHidden":false},"cancelBubble":false}

With click events:

[TRACE] :  Event from table: {"x":122,"section":{"horizontalWrap":true},"row":{"horizontalWrap":true,"title":"row_0"},"index":0,"y":36,"rowData":{"horizontalWrap":true,"title":"row_0"},"searchMode":false,"detail":false,"bubbles":true,"type":"click","source":{"horizontalWrap":true,"title":"row_0"},"cancelBubble":false}
[TRACE] :  Event from table: {"x":135,"section":{"horizontalWrap":true},"row":{"horizontalWrap":true,"title":"row_1"},"index":1,"y":9,"rowData":{"horizontalWrap":true,"title":"row_1"},"searchMode":false,"detail":false,"bubbles":true,"type":"click","source":{"horizontalWrap":true,"title":"row_1"},"cancelBubble":false}
[TRACE] :  Event from table: {"x":166,"section":{"horizontalWrap":true},"row":{"horizontalWrap":true,"title":"row_2"},"index":2,"y":23,"rowData":{"horizontalWrap":true,"title":"row_2"},"searchMode":false,"detail":false,"bubbles":true,"type":"click","source":{"horizontalWrap":true,"title":"row_2"},"cancelBubble":false}

*/