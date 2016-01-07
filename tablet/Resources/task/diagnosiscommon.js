// DiagnosisCommon.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    mainfieldlist = dbcommon.standardTaskFields();

mainfieldlist.push.apply(mainfieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
exports.mainfieldlist = mainfieldlist;

function makeFkField(fkname) {
    return {name: fkname, type: DBCONSTANTS.TYPE_INTEGER, mandatory: true};
}
exports.makeFkField = makeFkField;

function makeItemFieldList(fkname) {
    var ITEMTABLE_FK_FIELD = makeFkField(fkname),
        itemfieldlist = dbcommon.standardAncillaryFields(ITEMTABLE_FK_FIELD);
    itemfieldlist.push(
        {name: "seqnum", type: DBCONSTANTS.TYPE_INTEGER, mandatory: true},
        {name: "code", type: DBCONSTANTS.TYPE_TEXT},
        {name: "description", type: DBCONSTANTS.TYPE_TEXT}
    );
    return itemfieldlist;
}
exports.makeItemFieldList = makeItemFieldList;

function compareItemsBySeqNum(a, b) { // for sorting
    if (a.seqnum < b.seqnum) {
        return -1;
    }
    if (a.seqnum > b.seqnum) {
        return 1;
    }
    return 0;
}

//=============================================================================
// Item
//=============================================================================

function DiagnosisItemBase(props) {
    dbcommon.DatabaseObject.call(this); // call base constructor
    // Instantiate with some combination of IDs, if specified (will read from the database if enough info given)
    dbcommon.loadOrCreateAncillary(this, props, this._fkname, "seqnum");
}
lang.inheritPrototype(DiagnosisItemBase, dbcommon.DatabaseObject);
lang.extendPrototype(DiagnosisItemBase, {
    // KEY DATABASE FIELDS (USED BY DatabaseObject)
    //      _objecttype
    //      _tablename
    //      _fieldlist
    _sortorder: "id",

    // ALSO NEED:
    //      _fkname

    getAllItems: function (fkvalue) {
        return dbcommon.getAllRowsByKey(
            this._fkname,
            fkvalue,
            this._tablename,
            this._fieldlist,
            this._objecttype,
            "seqnum"
        );
    }
});
exports.DiagnosisItemBase = DiagnosisItemBase;

//=============================================================================
// Task
//=============================================================================

function DiagnosisTaskBase(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}
lang.inheritPrototype(DiagnosisTaskBase, taskcommon.BaseTask);
lang.extendPrototype(DiagnosisTaskBase, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _fieldlist: mainfieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Override dbdelete():
    dbdelete: function () {
        // Since we have no BLOBs, we can handle the subsidiary table like this:
        dbcommon.deleteWhere(this._itemtablename, this._itemfkfield, this.id);
        // Then the usual:
        dbcommon.deleteByPK(this._tablename, this._fieldlist[0], this);
        // No BLOBs owned by the main table.
    },

    getMyItems: function () {
        var dummy_sp = new this._itemobjecttype();
        return dummy_sp.getAllItems(this.id);
    },

    numItems: function () {
        return this.getMyItems().length;
    },

    // Standard task functions
    isComplete: function () {
        return (this.numItems() > 0);
    },

    getSummary: function () {
        var my_items = this.getMyItems(),
            s = "",
            i;
        if (my_items.length === 0) {
            return this.isCompleteSuffix();
        }
        for (i = 0; i < my_items.length; ++i) {
            // Human numbering:
            if (my_items[i].description) {
                if (s.length > 0) {
                    s += "\n";
                }
                s += (
                    (i + 1) + ": " +
                    my_items[i].code + " – " +
                    my_items[i].description
                );
            }
        }
        return s;
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            my_items,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3
        self.dbstore(); // generates self.id (needed as FK)
        // ... MUST SET self.id LIKE THIS BEFORE CALLING getMyItems().
        my_items = self.getMyItems();

        function getNumPages() {
            return 1;
        }

        function resequence() {
            var i;
            for (i = 0; i < my_items.length; ++i) {
                my_items[i].seqnum = i;
                my_items[i].dbstore();
            }
        }

        function resort() {
            my_items.sort(compareItemsBySeqNum);
        }

        function quietlyDeleteItem(itemIndex) {
            if (itemIndex < 0 || itemIndex >= my_items.length) {
                return;
            }
            my_items[itemIndex].dbdelete();
            my_items.splice(itemIndex, 1); // remove that one element
            resequence();
            questionnaire.refreshCurrentPage();
        }

        function deleteItem(itemIndex) {
            // Titanium.API.trace("deleteItem: " + itemIndex);
            if (itemIndex < 0 || itemIndex >= my_items.length) {
                return;
            }
            var dlg = Titanium.UI.createAlertDialog({
                title: L('diagnosis_delete_q'),
                message: (
                    L('diagnosis_delete_q') + " " +
                    (itemIndex + 1) + " " +
                    L("of") + " " +
                    my_items.length + "?"
                ),
                buttonNames: [L('cancel'), L('delete')]
            });
            dlg.addEventListener('click', function (e) {
                if (e.index === 1) { // Delete
                    quietlyDeleteItem(itemIndex);
                }
                dlg = null;
            });
            dlg.show();
        }

        function makeDeleteCall(index) { // Beware the Javascript Callback Loop Bug
            // http://stackoverflow.com/questions/3023874/arguments-to-javascript-anonymous-function
            return function () {
                deleteItem(index);
            };
        }

        function moveUp(itemIndex) {
            // Titanium.API.trace("moveUp: " + itemIndex);
            if (itemIndex <= 0 || itemIndex >= my_items.length) {
                return;
            }
            var precedingIndex = itemIndex - 1;
            my_items[precedingIndex].seqnum = itemIndex;
            my_items[precedingIndex].dbstore();
            my_items[itemIndex].seqnum = precedingIndex;
            my_items[itemIndex].dbstore();
            resort();
            questionnaire.refreshCurrentPage();
        }

        function makeUpCall(index) { // Beware the Javascript Callback Loop Bug
            // http://stackoverflow.com/questions/3023874/arguments-to-javascript-anonymous-function
            return function () {
                moveUp(index);
            };
        }

        function moveDown(itemIndex) {
            // Titanium.API.trace("moveDown: " + itemIndex);
            if (itemIndex < 0 || itemIndex >= my_items.length - 1) {
                return;
            }
            var followingIndex = itemIndex + 1;
            my_items[itemIndex].seqnum = followingIndex;
            my_items[itemIndex].dbstore();
            my_items[followingIndex].seqnum = itemIndex;
            my_items[followingIndex].dbstore();
            resort();
            questionnaire.refreshCurrentPage();
        }

        function makeDownCall(index) { // Beware the Javascript Callback Loop Bug
            // http://stackoverflow.com/questions/3023874/arguments-to-javascript-anonymous-function
            return function () {
                moveDown(index);
            };
        }

        function addItem() {
            // adds at the end
            var itemprops = {},
                item;
            itemprops[self._itemfkname] = self.id;
            item = new self._itemobjecttype(itemprops);
            item.seqnum = my_items.length;
            item.dbstore();
            my_items.push(item);
            questionnaire.refreshCurrentPage();
        }

        function makePage() { // ignore all parameters since only one page
            var isFirst,
                isLast,
                index,
                elements = [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionButton",
                        text: L("add"),
                        fnClicked: addItem
                    }
                ];
            for (index = 0; index < my_items.length; ++index) {
                isFirst = (index === 0);
                isLast = (index === my_items.length - 1);
                elements.push(
                    { type: "QuestionHorizontalRule" },
                    {
                        type: "QuestionText",
                        text: L("Diagnosis") + " " + (index + 1),
                        bold: true
                    },
                    {
                        type: "ContainerHorizontal",
                        elements: [
                            {
                                type: "QuestionButton",
                                text: L("delete"),
                                fnClicked: makeDeleteCall(index)
                            },
                            {
                                type: "QuestionButton",
                                text: L("move_up"),
                                inactive: isFirst,
                                fnClicked: makeUpCall(index)
                            },
                            {
                                type: "QuestionButton",
                                text: L("move_down"),
                                inactive: isLast,
                                fnClicked: makeDownCall(index)
                            },
                            {
                                type: "QuestionDiagnosticCode",
                                code_field: "code" + index,
                                description_field: "description" + index,
                                codelist_filename: self._codefilename
                            }
                        ]
                    }
                );
            }
            return {
                title: self._questionnairetitle,
                clinician: true,
                elements: elements
            };
        }

        function parseFieldText(field) {
            var split = 0,
                itemIndex;
            if (field.substring(0, "code".length) === "code") {
                split = "code".length;
            } else if (field.substring(0, "description".length) ===
                     "description") {
                split = "description".length;
            }
            if (split === 0) {
                return { field: field, itemIndex: null };
            }
            itemIndex = parseInt(field.substring(split), 10);
            if (isNaN(itemIndex) || itemIndex < 0 ||
                    itemIndex >= my_items.length) {
                itemIndex = null;
            }
            return { field: field.substring(0, split), itemIndex: itemIndex };
        }

        function setField(field, value) {
            //Titanium.API.trace("setField: " + field + ", " + value);
            var fieldinfo = parseFieldText(field);
            if (fieldinfo.itemIndex !== null) {
                my_items[fieldinfo.itemIndex].defaultSetFieldFn(
                    fieldinfo.field,
                    value
                );
                self.touch(); // IMPORTANT. Otherwise an item might change without creating a new server-side version of the task.
            } else {
                self.defaultSetFieldFn(fieldinfo.field, value);
            }
        }

        function getField(fieldname, getBlobsAsFilenames) {
            //Titanium.API.trace("getField: " + fieldname);
            var fieldinfo = parseFieldText(fieldname);
            if (fieldinfo.itemIndex !== null) {
                return my_items[fieldinfo.itemIndex].defaultGetFieldValueFn(
                    fieldinfo.field,
                    getBlobsAsFilenames
                );
            }
            return self.defaultGetFieldValueFn(fieldinfo.field,
                                               getBlobsAsFilenames);
        }

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            allPagesOnTheFly: true,
            pages: [], // all on the fly
            callbackThis: self,
            fnGetFieldValue: getField,
            fnSetField: setField,
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null; // for garbage collection, since we have closures referring to questionnaire
            },
            fnGetNumPages: getNumPages,
            fnMakePageOnTheFly: makePage
        });
        questionnaire.open();
    }

});

exports.DiagnosisTaskBase = DiagnosisTaskBase;
