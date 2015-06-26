// bugtest_table_events_ios_v_android.js

/*jslint node: true */
"use strict";
/*global Titanium */

function eventArrived(e) {
    Titanium.API.trace("Event from table: " + JSON.stringify(e));
}

var rowdata = [
    {title: "row_0", myattribute: "A"},
    {title: "row_1", myattribute: "B"},
    {title: "row_2", myattribute: "C"},
];
var win = Titanium.UI.createWindow({ backgroundColor: '#FFFFFF' });
var table = Titanium.UI.createTableView({ data: rowdata });

// Or:

table.addEventListener('click', eventArrived);

win.add(table);
win.open();


/*

TEST RIG:

Test date: 15 Oct 2013
Platform: Mac OS X 10.8.5
Titanium Studio, build: 3.1.3.201309132423

Then either (A) iOS 7.0 simulator or (B) Android tablet (tablet running Android 4.1.1; Titanium defaulting to Google APIs for Android 2.3.3).

TESTING:

Run, then tap/click and/or double-tap the three rows in order.

OUTPUT:

On iOS:

[TRACE] :  Event from table: {"x":250,"section":{"horizontalWrap":true},"row":{"horizontalWrap":true,"title":"row_0","myattribute":"A"},"index":0,"y":19,"rowData":{"horizontalWrap":true,"title":"row_0","myattribute":"A"},"searchMode":false,"detail":false,"bubbles":true,"type":"click","source":{"horizontalWrap":true,"title":"row_0","myattribute":"A"},"cancelBubble":false}
[TRACE] :  Event from table: {"x":260,"section":{"horizontalWrap":true},"row":{"horizontalWrap":true,"title":"row_1","myattribute":"B"},"index":1,"y":10,"rowData":{"horizontalWrap":true,"title":"row_1","myattribute":"B"},"searchMode":false,"detail":false,"bubbles":true,"type":"click","source":{"horizontalWrap":true,"title":"row_1","myattribute":"B"},"cancelBubble":false}
[TRACE] :  Event from table: {"x":269,"section":{"horizontalWrap":true},"row":{"horizontalWrap":true,"title":"row_2","myattribute":"C"},"index":2,"y":22,"rowData":{"horizontalWrap":true,"title":"row_2","myattribute":"C"},"searchMode":false,"detail":false,"bubbles":true,"type":"click","source":{"horizontalWrap":true,"title":"row_2","myattribute":"C"},"cancelBubble":false}

When we expand the last one we get:

{
    "x":269,
    "section":{
        "horizontalWrap":true
    },
    "row":{
        "horizontalWrap":true,
        "title":"row_2",
        "myattribute":"C"
    },
    "index":2,
    "y":22,
    "rowData":{
        "horizontalWrap":true,
        "title":"row_2",
        "myattribute":"C"
    },
    "searchMode":false,
    "detail":false,
    "bubbles":true,
    "type":"click",
    "source":{
        "horizontalWrap":true,
        "title":"row_2",
        "myattribute":"C"
    },
    "cancelBubble":false
}

... i.e. one can tell which row the event came from using:

    e.index
    e.row.myattribute
    e.rowData.myattribute
    e.source.myattribute

On Android:

V/TiAPI   (30618):  Event from table: {"type":"click","source":{"touchEnabled":false,"title":"row_0","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},"index":0,"detail":false,"cancelBubble":false,"rowData":{"title":"row_0","myattribute":"A"},"section":{"bubbleParent":true,"rowCount":3,"children":[],"rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"rows":[{"touchEnabled":false,"title":"row_0","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},{"touchEnabled":false,"title":"row_1","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},{"touchEnabled":false,"title":"row_2","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true}]},"row":{"touchEnabled":false,"title":"row_0","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},"searchMode":false,"bubbles":true}
V/TiAPI   (30618):  Event from table: {"type":"click","source":{"touchEnabled":false,"title":"row_1","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},"index":1,"detail":false,"cancelBubble":false,"rowData":{"title":"row_1","myattribute":"B"},"section":{"bubbleParent":true,"rowCount":3,"children":[],"rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"rows":[{"touchEnabled":false,"title":"row_0","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},{"touchEnabled":false,"title":"row_1","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},{"touchEnabled":false,"title":"row_2","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true}]},"row":{"touchEnabled":false,"title":"row_1","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},"searchMode":false,"bubbles":true}
V/TiAPI   (30618):  Event from table: {"type":"click","source":{"touchEnabled":false,"title":"row_2","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},"index":2,"detail":false,"cancelBubble":false,"rowData":{"title":"row_2","myattribute":"C"},"section":{"bubbleParent":true,"rowCount":3,"children":[],"rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"rows":[{"touchEnabled":false,"title":"row_0","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},{"touchEnabled":false,"title":"row_1","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},{"touchEnabled":false,"title":"row_2","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true}]},"row":{"touchEnabled":false,"title":"row_2","backgroundRepeat":false,"children":[],"className":"__normal__","rect":{"height":0,"y":0,"x":0,"width":0},"size":{"height":0,"y":0,"width":0,"x":0},"keepScreenOn":false,"bubbleParent":true},"searchMode":false,"bubbles":true}

Again, unpacking the last:

{
    "type":"click",
    "source":{
        "touchEnabled":false,
        "title":"row_2",
        "backgroundRepeat":false,
        "children":[],
        "className":"__normal__",
        "rect":{"height":0,"y":0,"x":0,"width":0},
        "size":{"height":0,"y":0,"width":0,"x":0},
        "keepScreenOn":false,
        "bubbleParent":true
    },
    "index":2,
    "detail":false,
    "cancelBubble":false,
    "rowData":{
        "title":"row_2",
        "myattribute":"C"
    },
    "section":{
        "bubbleParent":true,
        "rowCount":3,
        "children":[],
        "rect":{"height":0,"y":0,"x":0,"width":0},
        "size":{"height":0,"y":0,"width":0,"x":0},
        "keepScreenOn":false,
        "rows":[
            {
                "touchEnabled":false,
                "title":"row_0",
                "backgroundRepeat":false,
                "children":[],
                "className":"__normal__",
                "rect":{"height":0,"y":0,"x":0,"width":0},
                "size":{"height":0,"y":0,"width":0,"x":0},
                "keepScreenOn":false,
                "bubbleParent":true
            },
            {
                "touchEnabled":false,
                "title":"row_1",
                "backgroundRepeat":false,
                "children":[],
                "className":"__normal__",
                "rect":{"height":0,"y":0,"x":0,"width":0},
                "size":{"height":0,"y":0,"width":0,"x":0},
                "keepScreenOn":false,
                "bubbleParent":true
            },
            {
                "touchEnabled":false,
                "title":"row_2",
                "backgroundRepeat":false,
                "children":[],
                "className":"__normal__",
                "rect":{"height":0,"y":0,"x":0,"width":0},
                "size":{"height":0,"y":0,"width":0,"x":0},
                "keepScreenOn":false,
                "bubbleParent":true
            }
        ]
    },
    "row":{
        "touchEnabled":false,
        "title":"row_2",
        "backgroundRepeat":false,
        "children":[],
        "className":"__normal__",
        "rect":{"height":0,"y":0,"x":0,"width":0},
        "size":{"height":0,"y":0,"width":0,"x":0},
        "keepScreenOn":false,
        "bubbleParent":true
    },
    "searchMode":false,
    "bubbles":true
}

... i.e. one can tell which row the event came from using:

    e.index
    e.rowData.myattribute
    NOT e.row.myattribute
    NOT e.source.myattribute

... so that's FINE: http://docs.appcelerator.com/titanium/3.0/#!/api/Titanium.UI.TableView-event-click

*/
