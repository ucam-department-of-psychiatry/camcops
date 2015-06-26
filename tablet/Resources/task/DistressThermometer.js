// DistressThermometer.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TABLE
    tablename = "distressthermometer",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 36,
    // TASK
    THERMOMETER_10_UNSEL = '/images/dt/dt_unsel_10.png',
    THERMOMETER_09_UNSEL = '/images/dt/dt_unsel_9.png',
    THERMOMETER_08_UNSEL = '/images/dt/dt_unsel_8.png',
    THERMOMETER_07_UNSEL = '/images/dt/dt_unsel_7.png',
    THERMOMETER_06_UNSEL = '/images/dt/dt_unsel_6.png',
    THERMOMETER_05_UNSEL = '/images/dt/dt_unsel_5.png',
    THERMOMETER_04_UNSEL = '/images/dt/dt_unsel_4.png',
    THERMOMETER_03_UNSEL = '/images/dt/dt_unsel_3.png',
    THERMOMETER_02_UNSEL = '/images/dt/dt_unsel_2.png',
    THERMOMETER_01_UNSEL = '/images/dt/dt_unsel_1.png',
    THERMOMETER_00_UNSEL = '/images/dt/dt_unsel_0.png',
    THERMOMETER_10_SEL = '/images/dt/dt_sel_10.png',
    THERMOMETER_09_SEL = '/images/dt/dt_sel_9.png',
    THERMOMETER_08_SEL = '/images/dt/dt_sel_8.png',
    THERMOMETER_07_SEL = '/images/dt/dt_sel_7.png',
    THERMOMETER_06_SEL = '/images/dt/dt_sel_6.png',
    THERMOMETER_05_SEL = '/images/dt/dt_sel_5.png',
    THERMOMETER_04_SEL = '/images/dt/dt_sel_4.png',
    THERMOMETER_03_SEL = '/images/dt/dt_sel_3.png',
    THERMOMETER_02_SEL = '/images/dt/dt_sel_2.png',
    THERMOMETER_01_SEL = '/images/dt/dt_sel_1.png',
    THERMOMETER_00_SEL = '/images/dt/dt_sel_0.png',
    THERMOMETER_IMAGE_WIDTH = 192;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: 'distress', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'other', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function DistressThermometer(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(DistressThermometer, taskcommon.BaseTask);
lang.extendPrototype(DistressThermometer, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: DistressThermometer,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScore(this, "q", 1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        if (this.distress === null) {
            return false;
        }
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (
            L('distressthermometer_distress_s') + " " +
            this.distress + "/10. " +
            L('total_score') + " " + this.getTotalScore() + "/" + nquestions +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var msg = (
                L('distressthermometer_distress_s') + " " + this.distress + "\n\n"
            ),
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += (
                L("distressthermometer_q" + i) + ": " + this["q" + i] + "\n"
            );
        }
        return (msg +
            "\n" + L('distressthermometer_other_s') + " " + this.other + "\n" +
            "\n" +
            this.getSummary()
        );
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            qs = [],
            fields = [],
            pages,
            questionnaire,
            i;

        for (i = 1; i <= nquestions; ++i) {
            qs.push(L("distressthermometer_q" + i));
            fields.push("q" + i);
        }
        pages = [
            {
                title: L('distressthermometer_section1_title'),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('distressthermometer_distress_question')
                    },
                    {
                        type: "QuestionThermometer",
                        mandatory: true,
                        inactiveImages: [
                            THERMOMETER_10_UNSEL,
                            THERMOMETER_09_UNSEL,
                            THERMOMETER_08_UNSEL,
                            THERMOMETER_07_UNSEL,
                            THERMOMETER_06_UNSEL,
                            THERMOMETER_05_UNSEL,
                            THERMOMETER_04_UNSEL,
                            THERMOMETER_03_UNSEL,
                            THERMOMETER_02_UNSEL,
                            THERMOMETER_01_UNSEL,
                            THERMOMETER_00_UNSEL,
                        ],
                        activeImages: [
                            THERMOMETER_10_SEL,
                            THERMOMETER_09_SEL,
                            THERMOMETER_08_SEL,
                            THERMOMETER_07_SEL,
                            THERMOMETER_06_SEL,
                            THERMOMETER_05_SEL,
                            THERMOMETER_04_SEL,
                            THERMOMETER_03_SEL,
                            THERMOMETER_02_SEL,
                            THERMOMETER_01_SEL,
                            THERMOMETER_00_SEL,
                        ],
                        text: [
                            L('distressthermometer_distress_extreme'),
                            "", "", "", "", "",
                            "", "", "", "",
                            L('distressthermometer_distress_none'),
                        ],
                        imageWidth: THERMOMETER_IMAGE_WIDTH,
                        // imageHeight should be auto-set
                        values: [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
                        field: 'distress',
                    },
                ],
            },
            {
                title: L('distressthermometer_section2_title'),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('distressthermometer_section2_stem')
                    },
                    {
                        type: "QuestionMCQGrid",
                        mandatory: true,
                        options: taskcommon.OPTIONS_YES_NO_INTEGER,
                        questions: qs,
                        subtitles: [
                            {beforeIndex: 1 - 1, subtitle: L('distressthermometer_subtitle1') },
                            {beforeIndex: 6 - 1, subtitle: L('distressthermometer_subtitle2') },
                            {beforeIndex: 9 - 1, subtitle: L('distressthermometer_subtitle3') },
                            {beforeIndex: 15 - 1, subtitle: L('distressthermometer_subtitle4') },
                            {beforeIndex: 16 - 1, subtitle: L('distressthermometer_subtitle5') },
                            {beforeIndex: 20, subtitle: "" },
                            {beforeIndex: 25, subtitle: "" },
                            {beforeIndex: 30, subtitle: "" },
                            {beforeIndex: 35, subtitle: "" },
                        ],
                        fields: fields,
                        optionsWidthTogether: '25%',
                    },
                ],
            },
            {
                title: L("distressthermometer_section3_title"),
                elements: [
                    {
                        type: "QuestionText",
                        text: L("distressthermometer_other_question")
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        colWidthPrompt: '25%',
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "other",
                                prompt: L("distressthermometer_other_prompt")
                            },
                        ],
                    },
                ],
            },
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn,
        });
        questionnaire.open();
    },

});

module.exports = DistressThermometer;
