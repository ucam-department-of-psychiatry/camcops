// ContainerTable.js

/*
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
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

/*jslint node: true, plusplus: true, continue: true */
"use strict";
/*global Titanium */

var MODULE_NAME = "ContainerTable",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function createRowView() {
    return Titanium.UI.createView({
        left: 0,
        top: 0,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE
        // absolute positioning is OK
    });
}

function createCellView(left, width) {
    return Titanium.UI.createView({
        left: left,
        width: width,
        top: 0,
        height: Titanium.UI.SIZE
        // backgroundColor: (i % 2 == 0) ? '#FF0000' : '#00FF00',
        // ... for debugging
    });
}

function ContainerTable(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        viewprops,
        rowView = null,
        n_elements,
        n_columns,
        e,
        c,
        cellView,
        newElement,
        n_rows,
        r;

    qcommon.requireProperty(props, "elements", "ContainerTable");
    // ... sub-properties: as for Questionnaire's elements
    qcommon.setDefaultProperty(props, "columns", props.elements.length);
    qcommon.setDefaultProperty(props, "columnWidths", null);
    // ... array e.g. [ "30%", "70%" ]
    qcommon.setDefaultProperty(props, "populateVertically", false);
    qcommon.setDefaultProperty(props, "top", 0);
    qcommon.setDefaultProperty(props, "left", 0);
    qcommon.setDefaultProperty(props, "space", UICONSTANTS.MEDIUMSPACE);
    qcommon.QuestionElementBase.call(this, props); // call base constructor
    if (props.columnWidths !== null &&
            props.columnWidths.length !== props.columns) {
        throw new Error("ContainerTable created with columnWidths != null " +
                        "and columnWidths.length != columns");
    }

    n_elements = props.elements.length;
    n_columns = props.columns;

    function leftPosition(column) {
        var widthtotal,
            i;
        if (props.columnWidths === null) {
            return (column * 100 / props.columns) + "%";
        }
        if (column === 0) {
            return 0;
        }
        widthtotal = props.columnWidths[column - 1];
        for (i = column - 2; i >= 0; --i) {
            widthtotal = lang.addUnits(widthtotal, props.columnWidths[i]);
        }
        return widthtotal;
    }
    function columWidth(column) {
        if (props.columnWidths === null) {
            return (100 / props.columns) + "%";
        }
        return props.columnWidths[column];
    }

    // The horizontal view screws up on iOS, getting its height wrong
    // (in a way that variably depends on its children).
    // Therefore, rewritten without it.

    // View
    viewprops = {
        top: props.top,
        left: props.left,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        layout: "vertical"
        // backgroundColor: UICONSTANTS.GARISH_DEBUG_COLOUR_3,
    };
    this.tiview = Titanium.UI.createView(viewprops);

    // Iterate through elements property, creating elements
    this.elements = [];
    if (props.populateVertically) {
        n_rows = Math.ceil(n_elements / n_columns);
        for (r = 0; r < n_rows; ++r) {
            // New row
            rowView = createRowView();
            this.tiview.add(rowView);
            for (c = 0; c < n_columns; ++c) {
                e = (c * n_rows) + r;
                // would be (r * n_columns) + c if populating horizontally
                if (e >= n_elements) {
                    continue;
                }
                // New cell
                cellView = createCellView(leftPosition(c), columWidth(c));
                rowView.add(cellView);
                // Cell contents
                qcommon.setDefaultHorizontalPosLeft(props.elements[e],
                                                    c === 0 ? 0 : props.space);
                qcommon.setDefaultVerticalPosTop(props.elements[e],
                                                 r === 0 ? 0 : props.space);
                newElement = qcommon.makeElement(props.elements[e]);
                this.elements.push(newElement);
                cellView.add(newElement.tiview);
            }
        }
    } else {
        for (e = 0; e < n_elements; ++e) {
            c = e % n_columns;
            if (c === 0) {
                // New row
                rowView = createRowView();
                this.tiview.add(rowView);
            }
            // New cell
            cellView = createCellView(leftPosition(c), columWidth(c));
            rowView.add(cellView);
            // Cell contents
            qcommon.setDefaultHorizontalPosLeft(props.elements[e],
                                                c === 0 ? 0 : props.space);
            qcommon.setDefaultVerticalPosTop(props.elements[e],
                                             e < n_columns ? 0 : props.space);
            // ... e < n_columns when we're on the first row
            newElement = qcommon.makeElement(props.elements[e]);
            this.elements.push(newElement);
            cellView.add(newElement.tiview);
        }
    }
}
lang.inheritPrototype(ContainerTable, qcommon.QuestionElementBase);
// lang.extendPrototype(ContainerTable, {});
module.exports = ContainerTable;
