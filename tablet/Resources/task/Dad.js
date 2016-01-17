// Dad.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true, continue:true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "dad",
    fieldlist = dbcommon.standardTaskFields(),
    YES = 1,
    NO = 0,
    NA = -99,
    GROUPS = [
        "hygiene",
        "dressing",
        "continence",
        "eating",
        "mealprep",
        "telephone",
        "outing",
        "finance",
        "medications",
        "leisure"
    ],
    ITEMS = [
        "hygiene_init_wash",
        "hygiene_init_teeth",
        "hygiene_init_hair",
        "hygiene_plan_wash",
        "hygiene_exec_wash",
        "hygiene_exec_hair",
        "hygiene_exec_teeth",

        "dressing_init_dress",
        "dressing_plan_clothing",
        "dressing_plan_order",
        "dressing_exec_dress",
        "dressing_exec_undress",

        "continence_init_toilet",
        "continence_exec_toilet",

        "eating_init_eat",
        "eating_plan_utensils",
        "eating_exec_eat",

        "mealprep_init_meal",
        "mealprep_plan_meal",
        "mealprep_exec_meal",

        "telephone_init_phone",
        "telephone_plan_dial",
        "telephone_exec_conversation",
        "telephone_exec_message",

        "outing_init_outing",
        "outing_plan_outing",
        "outing_exec_reach_destination",
        "outing_exec_mode_transportation",
        "outing_exec_return_with_shopping",

        "finance_init_interest",
        "finance_plan_pay_bills",
        "finance_plan_organise_correspondence",
        "finance_exec_handle_money",

        "medications_init_medication",
        "medications_exec_take_medications",

        "leisure_init_interest_leisure",
        "leisure_init_interest_chores",
        "leisure_plan_chores",
        "leisure_exec_complete_chores",
        "leisure_exec_safe_at_home"
    ],
    tmpindex;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push.apply(fieldlist, dbcommon.RESPONDENT_FIELDSPECS);

for (tmpindex = 0; tmpindex < ITEMS.length; ++tmpindex) {
    fieldlist.push({
        name: ITEMS[tmpindex],
        type: DBCONSTANTS.TYPE_INTEGER
    });
}

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Dad(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Dad, taskcommon.BaseTask);
lang.extendPrototype(Dad, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Dad,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "dad",  // same as Y-BOCS
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, ITEMS);
    },

    getItemsActivity: function (activity) {
        var items = [],
            i,
            value;
        for (i = 0; i < ITEMS.length; ++i) {
            value = ITEMS[i];
            if (lang.startsWith(value, activity)) {
                items.push(value);
            }
        }
        return items;
    },

    getItemsActivities: function (activities) {  // array parameter
        var items = [],
            i,
            j,
            value,
            activity;
        for (i = 0; i < ITEMS.length; ++i) {
            value = ITEMS[i];
            for (j = 0; j < activities.length; ++j) {
                activity = activities[j];
                if (lang.startsWith(value, activity)) {
                    items.push(value);
                }
            }
        }
        return items;
    },

    getItemsPhase: function (phase) {
        var items = [],
            i,
            value;
        for (i = 0; i < ITEMS.length; ++i) {
            value = ITEMS[i];
            if (lang.stringContains(value, phase)) {
                items.push(value);
            }
        }
        return items;
    },

    getScoreIgnoringNA: function (fields) {
        var score = taskcommon.countWhere(this, fields, [YES]),
            possible = taskcommon.countWhereNot(this, fields, [null, NA]);
        return score + "/" + possible;
    },

    getSummary: function () {
        return (
            "Total " + this.getScoreIgnoringNA(ITEMS) +
            ". BADL ACTIVITIES: hygiene " + this.getScoreIgnoringNA(this.getItemsActivity("hygiene")) +
            "; dressing " + this.getScoreIgnoringNA(this.getItemsActivity("dressing")) +
            "; continence " + this.getScoreIgnoringNA(this.getItemsActivity("continence")) +
            "; eating " + this.getScoreIgnoringNA(this.getItemsActivity("eating")) +
            ". BADL OVERALL: " + this.getScoreIgnoringNA(this.getItemsActivities(["hygiene", "dressing", "continence", "eating"])) +
            ". IADL ACTIVITIES: mealprep " + this.getScoreIgnoringNA(this.getItemsActivity("mealprep")) +
            "; telephone " + this.getScoreIgnoringNA(this.getItemsActivity("telephone")) +
            "; outing " + this.getScoreIgnoringNA(this.getItemsActivity("outing")) +
            "; finance " + this.getScoreIgnoringNA(this.getItemsActivity("finance")) +
            "; medications " + this.getScoreIgnoringNA(this.getItemsActivity("medications")) +
            "; leisure " + this.getScoreIgnoringNA(this.getItemsActivity("leisure")) +
            ". IADL OVERALL: " + this.getScoreIgnoringNA(this.getItemsActivities(["mealprep", "telephone", "outing", "finance", "medications", "leisure"])) +
            ". PHASES: initiation " + this.getScoreIgnoringNA(this.getItemsPhase("init")) +
            "; planning/organisation " + this.getScoreIgnoringNA(this.getItemsPhase("plan")) +
            "; execution/performance " + this.getScoreIgnoringNA(this.getItemsPhase("exec")) +
            "." +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            KeyValuePair = require('lib/KeyValuePair'),
            elements,
            tableelements,
            detailelements,
            pages,
            g,
            groupname,
            i,
            itemname,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3
        pages = [self.getClinicianAndRespondentDetailsPage()]; // Clinician info 3/3

        elements = [
            {
                type: "QuestionText",
                bold: true,
                text: (this.XSTRING('instruction_1') + " " +
                       this.getPatientName() + " " +
                       this.XSTRING('instruction_2'))
            }
        ];
        for (g = 0; g < GROUPS.length; ++g) {
            groupname = GROUPS[g];
            tableelements = [];
            detailelements = [];
            for (i = 0; i < ITEMS.length; ++i) {
                itemname = ITEMS[i];
                if (!lang.startsWith(itemname, groupname)) {
                    continue;
                }
                tableelements.push(
                    {
                        type: "QuestionText",
                        text: this.XSTRING(itemname)
                    },
                    {
                        type: "QuestionMCQ",
                        showInstruction: false,
                        horizontal: true,
                        options: [
                            new KeyValuePair(L("Yes"), YES),
                            new KeyValuePair(L("No"), NO),
                            new KeyValuePair(L("not_applicable"), NA)
                        ],
                        field: itemname
                    }
                );
            }
            elements.push(
                {
                    type: "QuestionText",
                    bold: true,
                    italic: true,
                    text: this.XSTRING(groupname)
                },
                {
                    type: "ContainerTable",
                    columns: 2,
                    columnWidths: ["50%", "50%"],
                    elements: tableelements
                }
            );
            if (detailelements.length > 0) {
                elements.push.apply(elements, detailelements);
            }
        }
        pages.push({
            title: L('t_dad'),
            clinician: true,
            elements: elements
        });

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn
        });

        questionnaire.open();
    }

});

module.exports = Dad;
