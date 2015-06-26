// diagnosticcodelistfunc.js

/*
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

/*jslint node: true, plusplus: true, newcap: true */
"use strict";
/*global Titanium, L */

/*
    codelist elements:

    either:
        code, description
    or:
        startcode, endcode, description, range:true

    added by preprocess():
        parent
        firstchild
*/

/*
    To get a list manually from e.g. the ICD-10 code:

    - start Javascript console in e.g. Chrome

        var exports = {};
        var module = {};
        Titanium = { API: { trace: function (msg) { console.log(msg); } } }

    - copy/paste contents of diagnosticcodelistfunc.js

    - copy/paste this:

        var diagnosticcodelistfunc = exports;

    - copy/paste everything in the file below

    - copy/paste the following:

        var codestring = "";
        for (var i = 0; i < CODELIST.length; ++i) {
            if (CODELIST[i].code) {
                codestring += ("\n" + CODELIST[i].code + ": " +
                               CODELIST[i].description);
            }
        }

    - clear the console

    - run this:

        console.log(codestring);

    - then copy it to somewhere useful.
*/

function isChild(codelist, index1, index2) {
    // is item 1 a child of item 2?
    if (index1 <= index2) {
        return false; // because they're ordered
    }
    var childcode,
        childcodepart,
        parentstartcode,
        parentendcode,
        parentcode;
    if (codelist[index1].range) {
        childcode = codelist[index1].startcode;
    } else {
        childcode = codelist[index1].code;
    }
    if (codelist[index2].range) {
        parentstartcode = codelist[index2].startcode;
        parentendcode = codelist[index2].endcode;
        if (childcode.length < parentstartcode.length) {
            return false;
            // ... children have codes at least as long as their parents
        }
        childcodepart = childcode.substring(0, parentstartcode.length);
        if (childcodepart >= parentstartcode &&
                childcodepart <= parentendcode) {
            return true;
        }
    } else {
        parentcode = codelist[index2].code;
        if (childcode.length < parentcode.length) {
            return false;
            // ... children have codes at least as long as their parents
        }
        childcodepart = childcode.substring(0, parentcode.length);
        if (childcodepart === parentcode) {
            return true;
        }
    }
    return false;
}

function preprocess(codelist) {
    Titanium.API.trace("Preprocessing diagnostic code list...");
    var ncodes = codelist.length,
        i,
        j;
    if (ncodes === 0) {
        return;
    }
    // firstchild
    for (i = 0; i < ncodes; ++i) {
        codelist[i].firstchild = null; // the default
        if (i < ncodes - 1) { // all but the last can have children
            j = i + 1;
            // ... but one's child is always the very next entry,
            // if one has a child
            if (isChild(codelist, j, i)) {
                codelist[i].firstchild = j;
            }
        }
    }
    // parent
    for (i = ncodes - 1; i >= 0; --i) {
        codelist[i].parent = null; // the default
        for (j = i - 1; j >= 0; --j) {
            if (isChild(codelist, i, j)) {
                codelist[i].parent = j;
                break;
            }
        }
        // Titanium.API.trace("i=" + i + ": " + JSON.stringify(codelist[i]));
    }
    Titanium.API.trace("Preprocessing diagnostic code list... done");
}
exports.preprocess = preprocess;

function getFirstSibling(startingIndex, codelist) {
    if (startingIndex === undefined || startingIndex === null) {
        startingIndex = 0;
    }
    if (startingIndex < 0 || startingIndex >= codelist.length) {
        return null;
    }
    var parent = codelist[startingIndex].parent,
        firstsibling = startingIndex,
        i;
    for (i = startingIndex - 1; i >= 0; --i) {
        if (codelist[i].parent === parent) {
            firstsibling = i;
        }
    }
    return firstsibling;
}
exports.getFirstSibling = getFirstSibling;

/*
function makeListStartingWith(startingIndex, codelist) {
    if (startingIndex == null) {
        startingIndex = 0;
    }
    if (startingIndex < 0 || startingIndex >= codelist.length) {
        return [];
    }
    var list = [];
    var parent = codelist[startingIndex].parent;
    for (var i = startingIndex; i < codelist.length; ++i) {
        if (codelist[i].parent == parent) {
            list.push(codelist[i]);
        }
    }
    return list;
}
exports.makeListStartingWith = makeListStartingWith;
*/

function makeIndexListStartingWith(startingIndex, codelist) {
    if (startingIndex === undefined || startingIndex === null) {
        startingIndex = 0;
    }
    if (startingIndex < 0 || startingIndex >= codelist.length) {
        return [];
    }
    var list = [],
        parent = codelist[startingIndex].parent,
        i;
    for (i = startingIndex; i < codelist.length; ++i) {
        if (codelist[i].parent === parent) {
            list.push(i); // NB
        }
    }
    return list;
}
exports.makeIndexListStartingWith = makeIndexListStartingWith;

function getIndex(code, codelist) {
    var i;
    if (code === undefined || code === null) {
        return null;
    }
    for (i = 0; i < codelist.length; ++i) {
        if (codelist[i].code === code) {
            return i;
        }
    }
    return null;
}
exports.getIndex = getIndex;

function makeTableRow(item, selected, indicateChildren, sparse) {
    var UICONSTANTS = require('common/UICONSTANTS'),
        text,
        rowprops,
        row;

    if (item === null) { // special
        return Titanium.UI.createTableViewRow({
            className: 'diagcode_rc1',
            title: L("diagnosis_go_up"),
            leftImage: UICONSTANTS.ICON_TABLE_PARENTARROW,
            font: UICONSTANTS.DIAGNOSTICCODE_GO_UP_FONT,
            color: UICONSTANTS.DIAGNOSTICCODE_TEXT,
            backgroundColor: UICONSTANTS.DIAGNOSTICCODE_BACKGROUND,
        });
    }

    if (item.range) {
        text = item.startcode + "–" + item.endcode + ": " + item.description;
    } else {
        text = item.code + ": " + item.description;
    }

    if (sparse) {
        // no views as children of the row, or it'll get slow
        // the downside is that the text can get truncated, but not the end of
        // the world
        rowprops = {
            className: 'diagcode_rc2',
            title: text,
            textForFilter: text,
            // ... use with filterAttribute for table properties
            font: UICONSTANTS.DIAGNOSTICCODE_TEXT_FONT,
            color: (
                selected ?
                        UICONSTANTS.DIAGNOSTICCODE_TEXT_SELECTED :
                        UICONSTANTS.DIAGNOSTICCODE_TEXT
            ),
            backgroundColor: (
                selected ?
                        UICONSTANTS.DIAGNOSTICCODE_BACKGROUND_SELECTED :
                        UICONSTANTS.DIAGNOSTICCODE_BACKGROUND
            ),
        };
        if (indicateChildren && item.firstchild !== null) {
            rowprops.rightImage = UICONSTANTS.ICON_TABLE_CHILDARROW;
        }
        return Titanium.UI.createTableViewRow(rowprops);
    }

    rowprops = {
        className: 'diagcode_rc3',
        textForFilter: text,
        // ... use with filterAttribute for table properties
        backgroundColor: (
            selected ?
                    UICONSTANTS.DIAGNOSTICCODE_BACKGROUND_SELECTED :
                    UICONSTANTS.DIAGNOSTICCODE_BACKGROUND
        ),
    };
    if (indicateChildren && item.firstchild !== null) {
        rowprops.rightImage = UICONSTANTS.ICON_TABLE_CHILDARROW;
    }
    row = Titanium.UI.createTableViewRow(rowprops);
    // spacer:
    row.add(Titanium.UI.createView({
        height: UICONSTANTS.ICONSIZE,
        width: UICONSTANTS.SPACE,
        left: 0,
        center: {y: '50%'},
    }));
    // label:
    row.add(Titanium.UI.createLabel({
        text: text,
        font: UICONSTANTS.DIAGNOSTICCODE_TEXT_FONT,
        color: (
            selected ?
                    UICONSTANTS.DIAGNOSTICCODE_TEXT_SELECTED :
                    UICONSTANTS.DIAGNOSTICCODE_TEXT
        ),
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        center: {y: '50%'},
        left: 0,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.SIZE,
    }));
    return row;
}
exports.makeTableRow = makeTableRow;
