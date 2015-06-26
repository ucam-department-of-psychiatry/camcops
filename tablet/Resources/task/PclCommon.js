// PclCommon.js

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

var taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang');

// TASK

function PclCommon(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(PclCommon, taskcommon.BaseTask);
lang.extendPrototype(PclCommon, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    // _objecttype
    // _tablename
    // _fieldlist

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // WILL ALSO NEED

    // _nquestions
    // _pcltype
    // _specificEvent

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScore(this, "q", 1, this._nquestions);
    },

    getNumSymptomatic: function (start, end) {
        var total = 0,
            i;
        for (i = start; i <= end; ++i) {
            if (this["q" + i] >= 3) {
                // 3 and above scores as "symptomatic": http://www.mirecc.va.gov/docs/visn6/3_PTSD_CheckList_and_Scoring.pdf
                ++total;
            }
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, this._nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/85" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            // totalscore = this.getTotalScore(),
            // PTSD = at least one "B" item
            //        and at least three "C" items
            //        and at least two "D" items:
            // http://www.mirecc.va.gov/docs/visn6/3_PTSD_CheckList_and_Scoring.pdf
            ptsd = (this.getNumSymptomatic(1, 5) >= 1 &&
                    this.getNumSymptomatic(6, 12) >= 3 &&
                    this.getNumSymptomatic(13, 17) >= 2),
            msg = "";

        if (this._specificEvent) {
            msg += L('pcl_s_event_s') + " " + this.event + "\n" +
                   L('pcl_s_eventdate_s') + " " + this.eventdate + "\n";
        }
        return msg + taskcommon.valueDetail(this, "pcl_q", "_s", " ", "q", 1,
                                            this._nquestions) +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('pcl_dsm_criteria_met') + " " + uifunc.yesNo(ptsd);
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            options = [
                new KeyValuePair(L('pcl_option1'), 1),
                new KeyValuePair(L('pcl_option2'), 2),
                new KeyValuePair(L('pcl_option3'), 3),
                new KeyValuePair(L('pcl_option4'), 4),
                new KeyValuePair(L('pcl_option5'), 5),
            ],
            questions = [],
            fields = [],
            i,
            elements = [],
            pages,
            questionnaire;

        for (i = 1; i <= this._nquestions; ++i) {
            if (i <= 8) {
                questions.push(L("pcl_" + this._pcltype + "_q" + i));
            } else {
                questions.push(L("pcl_q" + i));
            }
            fields.push("q" + i);
        }
        if (this._specificEvent) {
            elements.push(
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "event",
                            prompt: L('pcl_s_event_prompt'),
                            hint: L('pcl_s_event_hint')
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "eventdate",
                            prompt: L('pcl_s_eventdate_prompt'),
                            hint: L('pcl_s_eventdate_hint')
                        },
                    ],
                }
            );
        }
        elements.push(
            {
                type: "QuestionText",
                text: L("pcl_" + this._pcltype + "_instructions"),
                bold: true
            },
            {
                type: "QuestionMCQGrid",
                questions: questions,
                fields: fields,
                options: options,
                subtitles: [
                    {beforeIndex: 4, subtitle: "" },
                    {beforeIndex: 8, subtitle: "" },
                    {beforeIndex: 12, subtitle: "" },
                    {beforeIndex: 16, subtitle: "" },
                ],
            }
        );

        pages = [
            {
                title: L("pcl_" + this._pcltype + "_title"),
                elements: elements,
            }
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

module.exports = PclCommon;
