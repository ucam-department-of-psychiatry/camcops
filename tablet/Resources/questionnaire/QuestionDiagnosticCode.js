// QuestionDiagnosticCode.js
// Simple text display.

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function diagHeader(instructionText, fnCloseMe) {
    var UICONSTANTS = require('common/UICONSTANTS'),
        uifunc = require('lib/uifunc'),
        view = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL
        }),
        cancelButton = uifunc.createCancelButton({
            left: 0,
            center: {y: '50%'}
        }),
        instruction = Titanium.UI.createLabel({
            text: instructionText,
            font: UICONSTANTS.DIAGNOSTICCODE_INSTRUCTION_FONT,
            color: UICONSTANTS.DIAGNOSTICCODE_INSTRUCTION,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
            center: {y: '50%'},
            left: UICONSTANTS.ICONSIZE,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.SIZE,
            touchEnabled: false
        });
    cancelButton.addEventListener('click', fnCloseMe);
    view.add(cancelButton);
    view.add(instruction);
    return view;
}

function QuestionDiagnosticCode(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        uifunc = require('lib/uifunc'),
        // platform = require('lib/platform'),
        MODULE_NAME = "QuestionDiagnosticCode",
        self = this,
        buttonView = Titanium.UI.createView({
            left: 0,
            top: 0,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.SIZE,
            layout: 'horizontal'
        }),
        searchEnabled = true; // !platform.android;

    qcommon.requireProperty(props, "code_field", MODULE_NAME);
    qcommon.requireProperty(props, "description_field", MODULE_NAME);
    qcommon.requireProperty(props, "codelist_filename", MODULE_NAME);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "offerNullButton", false);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.codelist_filename = props.codelist_filename;
    this.code_field = props.code_field;
    this.description_field = props.description_field;

    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.SIZE,
        layout: 'vertical'
    });
    this.codeLabel = Titanium.UI.createLabel({
        text: "?",
        top: 0,
        left: 0,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.SIZE,
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        font: UICONSTANTS.getQuestionnaireFont(false, /* big */
                                               true, /* bold */
                                               false), /* italic */
        color: UICONSTANTS.READONLY_ANSWER_COLOUR,
        touchEnabled: false
    });
    this.tiview.add(this.codeLabel);
    this.descriptionLabel = Titanium.UI.createLabel({
        text: "?",
        top: 0,
        left: 0,
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.SIZE,
        font: UICONSTANTS.getQuestionnaireFont(false, /* big */
                                               true, /* bold */
                                               false), /* italic */
        color: UICONSTANTS.READONLY_ANSWER_COLOUR,
        touchEnabled: false
    });
    this.tiview.add(this.descriptionLabel);

    this.tiview.add(buttonView);

    this.editButton = Titanium.UI.createButton({
        left: 0,
        top: 0,
        title: qcommon.processButtonTextForIos(
            L("diagnosis_choose_from_tree")
        ),
        color: (
            props.readOnly ?
                    UICONSTANTS.QUESTIONNAIRE_READONLY_BUTTON_TEXT_COLOR :
                    UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR
        )
    });
    this.editListener = null;
    if (!props.readOnly) {
        this.editListener = function () { self.edit(); };
        this.editButton.addEventListener('click', this.editListener);
    }
    buttonView.add(this.editButton);

    buttonView.add(uifunc.createHorizontalSpacer());

    // the large tables currently cause a huge memory leak on Android -- await
    // Titanium SDK 3.2.0 and the ListView -- or was it a "var X" versus "X"
    // bug of mine?
    this.searchButton = Titanium.UI.createButton({
        left: 0,
        top: 0,
        title: qcommon.processButtonTextForIos(L("diagnosis_search")),
        color: (
            (!props.readOnly && searchEnabled) ?
                    UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR :
                    UICONSTANTS.QUESTIONNAIRE_READONLY_BUTTON_TEXT_COLOR
        )
    });
    this.searchListener = null;
    buttonView.add(this.searchButton);
    if (!props.readOnly) {
        if (searchEnabled) {
            this.searchListener = function () { self.search(); };
            this.searchButton.addEventListener('click', this.searchListener);
        } else {
            buttonView.add(uifunc.createInfoLabel(
                "Search disabled on Android at present"
            ));
        }
    }

    if (props.offerNullButton) {
        this.nullButton = Titanium.UI.createButton({
            left: 0,
            top: 0,
            title: qcommon.processButtonTextForIos(L("diagnosis_clear")),
            color: (
                (!props.readOnly) ?
                        UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR :
                        UICONSTANTS.QUESTIONNAIRE_READONLY_BUTTON_TEXT_COLOR
            )
        });
        this.nullListener = function () { self.setNull(); };
        this.nullButton.addEventListener('click', this.nullListener);
        buttonView.add(uifunc.createHorizontalSpacer());
        buttonView.add(this.nullButton);
    } else {
        this.nullButton = null;
        this.nullListener = null;
    }

    // Create the window at this level to save re-use/risk of memory leak
    this.win = null;
    this.indexlist = null; // list of indices to props.codelist
    this.selectedIndex = null; // index to props.codelist
    // What follows is a little convoluted to save memory. All we copy
    // from props.codelist is a list of indices.
}
lang.inheritPrototype(QuestionDiagnosticCode, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionDiagnosticCode, {

    edit_sub: function (startIndex) {
        this.questionnaire.showWait();
        var self = this,
            diagnosticcodelistfunc = require('lib/diagnosticcodelistfunc'),
            codelist = require(this.codelist_filename),
            UICONSTANTS = require('common/UICONSTANTS'),
            uifunc = require('lib/uifunc'),
            // Pickers aren't very good -- width not adjustable under iOS.
            firstindexoflist = diagnosticcodelistfunc.getFirstSibling(
                startIndex,
                codelist
            ),
            isTopList,
            rows = [],
            i,
            table;

        this.indexlist = diagnosticcodelistfunc.makeIndexListStartingWith(
            firstindexoflist,
            codelist
        );
        isTopList = (codelist[this.indexlist[0]].parent === null);

        this.win = uifunc.createDiagnosticCodeWindow(function () {
            self.closeme();
        });

        this.win.add(diagHeader(L("diagnosis_tap_instructions_1"),
                                function () { self.closeme(); }));

        if (!isTopList) {
            rows.push(diagnosticcodelistfunc.makeTableRow(null, false, false));
            // makes a special go-back row
        }
        for (i = 0; i < this.indexlist.length; ++i) {
            rows.push(diagnosticcodelistfunc.makeTableRow(
                codelist[this.indexlist[i]],
                this.indexlist[i] === this.selectedIndex,
                true
            ));
        }
        table = Titanium.UI.createTableView({
            backgroundColor: UICONSTANTS.DIAGNOSTICCODE_BACKGROUND,
            data: rows,
            showVerticalScrollIndicator: true
        });
        rows = null; // for garbage collection

        table.addEventListener('singletap', function (e) {
            self.selectFromEdit(e, false);
        });
        table.addEventListener('doubletap', function (e) {
            self.selectFromEdit(e, true);
        });

        // https://jira.appcelerator.org/browse/TIMOB-15540
        // table.addEventListener('click', function (e) {
        //      self.selectFromEdit(e, false);
        // } );

        this.win.add(table);
        table = null; // try helping garbage collection
        this.win.open({ animated: false });
        this.questionnaire.hideWait(); // don't put it after this.win.open()
        // -- makes it go wrong on Android?

        /*
            TRYING TO NAIL TITANIUM TABLE EVENTS...
            We want >1 type of touch here.

            TABLEVIEW
            click:
                you can attach them to the table
                ... in which case e.index contains the row index
                    (+/- e.row, e.rowData, e.source)
            dblclick:
                ... don't care, because if you have a click and a dblclick,
                    then a double-click fires the click event twice
                    and the double-click event once.
            singletap
                e contains properties of the table, with no row details
                ... whether or not the row components have touchEnabled set
            doubletap
                likewise
            longclick
                can't get it to fire on the iOS 7 simulator

            TABLEVIEWROW
            click supported
            longclick supported
            singletap, doubletap, dblclick: not supported

            See also:
                http://docs.appcelerator.com/titanium/3.0/#!/guide/TableViews
                http://docs.appcelerator.com/titanium/3.0/#!/api/Titanium.UI.TableView
                https://jira.appcelerator.org/browse/TIDOC-164
                https://developer.appcelerator.com/question/152502/swipe-of-tableview-fired-but-rothis.windex-properties-are-missing
            My bug report:
                https://jira.appcelerator.org/browse/TC-3144
                https://jira.appcelerator.org/browse/TIMOB-15540
            fix pending, in Titanium 3.2.0 -- now implemented
        */

    },

    selectFromEdit: function (e, allowBranchSelection) {
        var row_index = e.index;
        Titanium.API.trace("QuestionDiagnosticCode/edit_sub/selectFromEdit: " +
                           "row_index = " + row_index);
        this.closeme();
        // ... as selectFromEditMain may re-use the table/header variables
        if (row_index === undefined) {
            Titanium.API.debug("QuestionDiagnosticCode.selectFromEdit: " +
                               "row_index undefined");
            return;
        }
        this.selectFromEditMain(row_index, allowBranchSelection);
    },

    selectFromEditMain: function (row_index, allowBranchSelection) {
        var codelist = require(this.codelist_filename),
            isTopList = (codelist[this.indexlist[0]].parent === null),
            item;
        if (!isTopList) {
            if (row_index === 0) {
                // go back/up
                this.edit_sub(codelist[this.indexlist[row_index]].parent);
                return;
            }
            row_index -= 1;
            // ... remove effect of the "go back" row for what follows
        }
        item = codelist[this.indexlist[row_index]];
        if (!allowBranchSelection && item.firstchild !== null) {
            // drill down
            this.edit_sub(item.firstchild);
            return;
        }
        if (item.range) {
            // unselectable (range), so drill down if possible
            if (item.firstchild !== null) {
                // drill down
                this.edit_sub(item.firstchild);
            }
            return;
        }
        // set value
        this.storeValue(item.code, item.description);
    },

    closeme: function () {
        if (this.win) {
            this.win.close();
            this.win = null;
        }
    },

    edit: function () { // edit as tree
        var diagnosticcodelistfunc = require('lib/diagnosticcodelistfunc'),
            codelist = require(this.codelist_filename),
            code = this.questionnaire.getFieldValue(this.code_field);
        this.selectedIndex = diagnosticcodelistfunc.getIndex(code, codelist);
        this.edit_sub(this.selectedIndex);
    },

    search: function () { // search and choose
        var self = this,
            diagnosticcodelistfunc = require('lib/diagnosticcodelistfunc'),
            codelist = require(this.codelist_filename),
            UICONSTANTS = require('common/UICONSTANTS'),
            uifunc = require('lib/uifunc'),
            i,
            code,
            data = [],
            item,
            text,
            section = Titanium.UI.createListSection(),
            listView;
        this.questionnaire.showWait();
        this.indexlist = [];
        for (i = 0; i < codelist.length; ++i) {
            if (!codelist[i].range) {
                this.indexlist.push(i);
            }
        }
        code = this.questionnaire.getFieldValue(this.code_field);
        this.selectedIndex = diagnosticcodelistfunc.getIndex(code, codelist);

        this.win = uifunc.createDiagnosticCodeWindow(function () {
            self.closeme();
        });

        this.win.add(diagHeader(L("diagnosis_tap_instructions_2"),
                                function () { self.closeme(); }));

        // LISTVIEW METHOD
        for (i = 0; i < this.indexlist.length; ++i) {
            item = codelist[this.indexlist[i]];
            text = item.code + ": " + item.description;
            data.push({ properties: {
                itemId: i,
                title: text,
                searchableText: text,
                accessoryType: (
                    (this.indexlist[i] === this.selectedIndex) ?
                            Titanium.UI.LIST_ACCESSORY_TYPE_CHECKMARK :
                            Titanium.UI.LIST_ACCESSORY_TYPE_NONE
                ),
                color: UICONSTANTS.DIAGNOSTICCODE_TEXT
            }});
        }
        section.setItems(data);
        listView = Titanium.UI.createListView({
            canScroll: true,
            caseInsensitiveSearch: true,
            searchView: Titanium.UI.createSearchBar({
                top: 0,
                left: 0,
                height: 45,
                showCancel: false,
                backgroundColor: UICONSTANTS.QUESTIONNAIRE_SEARCHBAR_BG_COLOUR
            }),
            sections: [section]
        });
        listView.addEventListener('itemclick', function (e) {
            self.selectFromListViewSearch(e);
        });
        this.win.add(listView);

        this.win.open({ animated: false });
        this.questionnaire.hideWait();

        // https://wiki.appcelerator.org/display/guides/Managing+memory+and+finding+leaks
        // STILL A GARBAGE COLLECTION PROBLEM ON ANDROID.
        // When you open the Search screen a second time, it runs out of
        // memory. TRY DDMS, see link above.
        // Run tools/monitor from within the Android SDK.

        // http://developer.appcelerator.com/question/116867/this-is-a-solution-to-your-memory-woes
        // Profiling/leaks: http://vimeo.com/29804284

        // ListView: http://docs.appcelerator.com/titanium/3.0/#!/guide/ListViews
        // ... will support search from Titanium SDK 3.2.0
        // ... implemented
    },

    selectFromTableSearch: function (e) {
        // Titanium.API.trace("selectFromTableSearch: e = " +
        //                    JSON.stringify(e) );
        this.select(e.index); // raw
    },

    selectFromListViewSearch: function (e) {
        //Titanium.API.trace(
        //    "selectFromListViewSearch: e.itemIndex = " +
        //    JSON.stringify(e.itemIndex) +
        //    ", e.sectionIndex = " + JSON.stringify(e.sectionIndex) +
        //    ", e.itemId = " + JSON.stringify(e.itemId) );
        // Need to use itemId, not itemIndex, when searching. (was my
        // confusion: see bugtest_listview_search_select.jsx).
        this.select(e.itemId);
    },

    select: function (row_index) {
        var codelist = require(this.codelist_filename),
            item = codelist[this.indexlist[row_index]],
            code = item.code,
            description = item.description;
        this.storeValue(code, description);
        this.closeme();
    },

    setNull: function () {
        this.storeValue(null, null);
    },

    storeValue: function (code, description) {
        this.questionnaire.setFieldValue(this.code_field, code);
        this.questionnaire.setFieldValue(this.description_field, description);
        this.setFromField();
    },

    setFromField: function () {
        var code = this.questionnaire.getFieldValue(this.code_field),
            description = this.questionnaire.getFieldValue(
                this.description_field
            );
        if (code === null) {
            this.codeLabel.setText("?");
        } else {
            this.codeLabel.setText(code);
        }
        if (description === null) {
            this.descriptionLabel.setText("?");
        } else {
            this.descriptionLabel.setText(description);
        }
    },

    cleanup: function () {
        if (this.editListener) {
            this.editButton.removeEventListener('click', this.editListener);
            this.editListener = null;
        }
        this.editButton = null;

        if (this.searchListener) {
            this.searchButton.removeEventListener('click',
                                                  this.searchListener);
            this.searchListener = null;
        }
        this.searchButton = null;

        if (this.nullListener) {
            this.nullButton.removeEventListener('click', this.nullListener);
            this.nullListener = null;
        }
        this.nullButton = null;

        this.questionnaire = null;
        this.codeLabel = null;
        this.descriptionLabel = null;
        this.closeme();
    }

});

module.exports = QuestionDiagnosticCode;
