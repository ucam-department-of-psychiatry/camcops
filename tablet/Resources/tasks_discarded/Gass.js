// Gass.js

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
    tablename = "gass",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 22,
    n_quad_questions = 22,
    list_sedation = [1, 2],
    list_cardiovascular = [3, 4],
    list_epse = [5, 6, 7, 8, 9, 10],
    list_anticholinergic = [11, 12, 13],
    list_gastrointestinal = [14],
    list_genitourinary = [15],
    list_prolactinaemic_female = [17, 18, 19, 21],
    list_prolactinaemic_male = [17, 18, 19, 20],
    list_weightgain = [22];

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER); // rating
dbcommon.appendRepeatedFieldDef(fieldlist, "d", 1, nquestions, DBCONSTANTS.TYPE_INTEGER); // distress
fieldlist.push(
    {name: 'medication', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

module.exports = function Gass(patient_id) {
    var self = this;
    taskcommon.createStandardTaskMembers(self, Gass, {
        tablename: tablename,
        fieldlist: fieldlist,
        patient_id: patient_id
    });

    // Scoring
    function getTotalScore(female) {
        return taskcommon.totalScoreByPrefix(self, "q", 1, 19) +
            (female ? self.q21 : self.q20) +
            self.q22;
    }

    function getGroupScore(list) {
        var total = 0,
            i;
        for (i = 0; i < list.length; ++i) {
            total += self["q" + list[i]];
        }
        return total;
    }

    // Standard task functions
    self.isComplete = function () {
        if (!taskcommon.isCompleteByPrefix(self, "q", 1, 19)) {
            return false;
        }
        if (self.q22 === null) {
            return false;
        }
        var female = self.isFemale();
        if ((female ? self.q21 : self.q20) === null) {
            return false;
        }
        return true;
    };
    self.getSummary = function () {
        var female = self.isFemale();
        return L('total_score') + " " + getTotalScore(female) + "/63" + self.isCompleteSuffix();
    };
    self.getDetail = function () {
        var female = self.isFemale(),
            totalscore = getTotalScore(female),
            severity = (totalscore >= 43 ? L('severe')
                        : (totalscore >= 22 ? L('moderate')
                           : L('absent_or_mild')
                          )
            ),
            msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += L("gass_q" + i + "_s") + " " +
                   self["q" + i] +
                   (self["d" + i] ? (" " + L('gass_distressing')) : "") +
                   "\n(" + severity + ")\n";
        }
        return (
            msg +
            "\n" +
            L("gass_group_sedation") + ": " + getGroupScore(list_sedation) + "/6\n" +
            L("gass_group_cardiovascular") + ": " + getGroupScore(list_cardiovascular) + "/6\n" +
            L("gass_group_epse") + ": " + getGroupScore(list_epse) + "/18\n" +
            L("gass_group_anticholinergic") + ": " + getGroupScore(list_anticholinergic) + "/9\n" +
            L("gass_group_gastrointestinal") + ": " + getGroupScore(list_gastrointestinal) + "/3\n" +
            L("gass_group_genitourinary") + ": " + getGroupScore(list_genitourinary) + "/3\n" +
            L("gass_group_prolactinaemic") + ": " + getGroupScore(female ? list_prolactinaemic_female : list_prolactinaemic_male) + "/15" + "\n" +
            L("gass_group_weightgain") + ": " + getGroupScore(list_weightgain) + "/3\n" +
            "\n" +
            L("gass_medication_s") + " " + self.medication + "\n" +
            "\n" +
            self.getSummary() + "\n"
        );
    };

    self.edit = function (readOnly) {
        var female = self.isFemale(),
            KeyValuePair = require('lib/KeyValuePair'),
            QuestionMCQGridWithSingleBoolean = require('questionnaire/QuestionMCQGridWithSingleBoolean'),
            QuestionTypedVariables = require('questionnaire/QuestionTypedVariables'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            QuestionText = require('questionnaire/QuestionText'),
            // quad
            quad_options = [
                new KeyValuePair(L('gass_option0'), 0),
                new KeyValuePair(L('gass_option1'), 1),
                new KeyValuePair(L('gass_option2'), 2),
                new KeyValuePair(L('gass_option3'), 3)
            ],
            quad_main_fields = [],
            quad_distress_fields = [],
            quad_qs = [],
            // yn
            yn_options = [
                new KeyValuePair(L('No'), 0),
                new KeyValuePair(L('Yes'), 3)  // 3 points for a yes
            ],
            yn_main_fields = [],
            yn_distress_fields = [],
            yn_qs = [],
            // other
            pages,
            questionnaire,
            n;

        for (n = 1; n <= (female ? 19 : 20); ++n) {
            quad_main_fields.push("q" + n);
            quad_distress_fields.push("d" + n);
            quad_qs.push(L("gass_q" + n));
        }
        for (n = (female ? 21 : 22); n <= 22; ++n) {
            yn_main_fields.push("q" + n);
            yn_distress_fields.push("d" + n);
            yn_qs.push(L("gass_q" + n));
        }
        // questionnaire
        pages = [
            {
                title: L("gass_medication_title"),
                elements: [
                    { type: QuestionText, text: L("gass_medication_stem") },
                    {
                        type: QuestionTypedVariables,
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "medication",
                                prompt: L("gass_medication_prompt"),
                                hint: L("gass_medication_hint")
                            }
                        ]
                    }
                ]
            },
            {
                title: L("gass_main_title"),
                elements: [
                    { type: QuestionText, text: L("gass_stem") },
                    {
                        type: QuestionMCQGridWithSingleBoolean,
                        options: quad_options,
                        booleanLabel: L("gass_tick_if_distressing"),
                        questions: quad_qs,
                        mcqFields: quad_main_fields,
                        booleanFields: quad_distress_fields,
                        boolColWidth: '20%',
                        subtitles: [
                            {beforeIndex: 1 - 1, subtitle: L('gass_quad_subtitle') }
                        ]
                    },
                    {
                        type: QuestionMCQGridWithSingleBoolean,
                        options: yn_options,
                        booleanLabel: L("gass_tick_if_distressing"),
                        questions: yn_qs,
                        mcqFields: yn_main_fields,
                        booleanFields: yn_distress_fields,
                        boolColWidth: '20%',
                        subtitles: [
                            {beforeIndex: 1 - 1, subtitle: L('gass_yn_subtitle') }
                        ]
                    }
                ]
            }
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn
        });
        questionnaire.open();
    };

    return self;
};
