// Bmi.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TABLE
    tablename = "bmi",
    fieldlist = dbcommon.standardTaskFields(),
    extrafields = [
        {name: "mass_kg", type: DBCONSTANTS.TYPE_REAL},
        {name: "height_m", type: DBCONSTANTS.TYPE_REAL},
        {name: "comment", type: DBCONSTANTS.TYPE_TEXT}
    ],
    // TASK
    PAGE_HEIGHT = "page_height",
    PAGE_MASS = "page_mass",
    BMI_DP = 2;

fieldlist.push.apply(fieldlist, extrafields); // append extrafields to fieldlist

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Bmi(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Bmi, taskcommon.BaseTask);
lang.extendPrototype(Bmi, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Bmi,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    bmi: function () {
        if (!this.isComplete()) {
            return null;
        }
        var bmi = this.mass_kg / (this.height_m * this.height_m);
        return bmi.toFixed(BMI_DP);
    },

    // Standard task functions
    isComplete: function () {
        return (this.mass_kg !== null && this.height_m !== null);
    },

    getSummary: function () {
        var bmi = this.bmi(),
            category = "?",
            commenttext = "";
        if (bmi !== null) {
            if (bmi >= 40) {
                category = L('bmi_obese_3');
            } else if (bmi >= 35) {
                category = L('bmi_obese_2');
            } else if (bmi >= 30) {
                category = L('bmi_obese_1');
            } else if (bmi >= 25) {
                category = L('bmi_overweight');
            } else if (bmi >= 18.5) {
                category = L('bmi_normal');
            } else if (bmi >= 17.5) {
                category = L('bmi_underweight_17.5_18.5');
            } else if (bmi > 17) {
                category = L('bmi_underweight_17_17.5');
            } else if (bmi > 16) {
                category = L('bmi_underweight_16_17');
            } else if (bmi > 15) {
                category = L('bmi_underweight_15_16');
            } else if (bmi > 13) {
                category = L('bmi_underweight_13_15');
            } else {
                category = L('bmi_underweight_under_13');
            }
        }
        if (this.comment) {
            commenttext = " (" + L('comments') + " " + this.comment + ")";
        }
        return (
            this.height_m + " m, " +
            this.mass_kg + " kg; " +
            "BMI = " + bmi + " kg/m^2; " + category +
            commenttext +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire;

        function heightMetricToImperial() {
            var inches = self.height_m * 39.3700787;
            self.impheight = {
                ft: lang.div(inches, 12),
                inches: inches % 12
            };
        }
        function massMetricToImperial() {
            var pounds = self.mass_kg * 2.20462;
            self.impmass = {
                st: lang.div(pounds, 14),
                lb: pounds % 14
            };
        }
        function heightImperialToMetric() {
            self.height_m = (self.impheight.ft * 12 +
                             self.impheight.inches) * 2.54 / 100.0;
            Titanium.API.trace("ft = " + self.impheight.ft +
                               ", inches = " + self.impheight.inches +
                               ", => m = " + self.height_m);
        }
        function massImperialToMetric() {
            self.mass_kg = (self.impmass.st * 14 +
                            self.impmass.lb) * 453.592 / 1000.0;
            Titanium.API.trace("st = " + self.impmass.st +
                               ", lb = " + self.impmass.lb +
                               ", => kg = " + self.mass_kg);
        }

        self.isHeightInImperial = 0;
        self.isMassInImperial = 0;
        heightMetricToImperial();
        massMetricToImperial();

        pages = [
            {
                title: L('bmi_title_1'),
                elements: [
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('bmi_metric_height'), 0),
                            new KeyValuePair(L('bmi_imperial_height'), 1),
                        ],
                        field: 'isHeightInImperial',
                    },
                ],
            },
            {
                onTheFly: true,
                pageTag: PAGE_HEIGHT,
            },
            {
                title: L('bmi_title_3'),
                elements: [
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('bmi_metric_mass'), 0),
                            new KeyValuePair(L('bmi_imperial_mass'), 1),
                        ],
                        field: 'isMassInImperial',
                    },
                ],
            },
            {
                onTheFly: true,
                pageTag: PAGE_MASS,
            },
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: function (field) {
                if (field === "height_m" ||
                        field === "mass_kg" ||
                        field === "isHeightInImperial" ||
                        field === "isMassInImperial") {
                    return self[field];
                }
                if (field === "height_ft") {
                    return self.impheight.ft;
                }
                if (field === "height_in") {
                    return self.impheight.inches;
                }
                if (field === "mass_st") {
                    return self.impmass.st;
                }
                if (field === "mass_lb") {
                    return self.impmass.lb;
                }
                if (field === "comment") {
                    return self.comment;
                }
                throw new Error("BMI: fnGetFieldValue called with " +
                                "invalid field: " + field);
            },
            fnSetField: function (field, value) {
                if (field === "height_m") {
                    self.height_m = value;
                    heightMetricToImperial();
                } else if (field === "mass_kg") {
                    self.mass_kg = value;
                    massMetricToImperial();
                } else if (field === "height_ft") {
                    self.impheight.ft = value;
                    heightImperialToMetric();
                } else if (field === "height_in") {
                    self.impheight.inches = value;
                    heightImperialToMetric();
                } else if (field === "mass_st") {
                    self.impmass.st = value;
                    massImperialToMetric();
                } else if (field === "mass_lb") {
                    self.impmass.lb = value;
                    massImperialToMetric();
                } else if (field === "comment") {
                    self.comment = value;
                } else if (field === "isHeightInImperial" ||
                            field === "isMassInImperial") {
                    self[field] = value;
                } else {
                    throw new Error("BMI: fnSetField called with " +
                                    "invalid field: " + field);
                }
                self.dbstore();
            },
            fnMakePageOnTheFly: function (currentPage, pageTag) {
                var title,
                    elements;
                if (pageTag === PAGE_HEIGHT) {
                    title = L('bmi_title_2');
                    if (self.isHeightInImperial) {
                        elements = [
                            {
                                type: "QuestionTypedVariables",
                                variables: [
                                    {
                                        field: "height_ft",
                                        prompt: L('bmi_ft'),
                                        type: UICONSTANTS.TYPEDVAR_REAL,
                                    },
                                    {
                                        field: "height_in",
                                        prompt: L('bmi_in'),
                                        type: UICONSTANTS.TYPEDVAR_REAL,
                                    },
                                ],
                            }
                        ];
                    } else {
                        elements = [
                            {
                                type: "QuestionTypedVariables",
                                variables: [
                                    {
                                        field: "height_m",
                                        prompt: L('bmi_m'),
                                        type: UICONSTANTS.TYPEDVAR_REAL,
                                    },
                                ],
                            }
                        ];
                    }
                } else if (pageTag === PAGE_MASS) {
                    title = L('bmi_title_4');
                    if (self.isMassInImperial) {
                        elements = [
                            {
                                type: "QuestionTypedVariables",
                                variables: [
                                    {
                                        field: "mass_st",
                                        prompt: L('bmi_st'),
                                        type: UICONSTANTS.TYPEDVAR_REAL,
                                    },
                                    {
                                        field: "mass_lb",
                                        prompt: L('bmi_lb'),
                                        type: UICONSTANTS.TYPEDVAR_REAL,
                                    },
                                ],
                            },
                            {
                                type: "QuestionTypedVariables",
                                useColumns: false,
                                mandatory: false,
                                variables: [
                                    {
                                        field: "comment",
                                        prompt: L('comments'),
                                        type: UICONSTANTS.TYPEDVAR_TEXT,
                                    },
                                ],
                            },
                        ];
                    } else {
                        elements = [
                            {
                                type: "QuestionTypedVariables",
                                variables: [
                                    {
                                        field: "mass_kg",
                                        prompt: L('bmi_kg'),
                                        type: UICONSTANTS.TYPEDVAR_REAL,
                                    },
                                ],
                            },
                            {
                                type: "QuestionTypedVariables",
                                useColumns: false,
                                mandatory: false,
                                variables: [
                                    {
                                        field: "comment",
                                        prompt: L('comments'),
                                        type: UICONSTANTS.TYPEDVAR_TEXT,
                                    },
                                ],
                            },
                        ];
                    }
                } else {
                    throw new Error("BMI: fnMakePageOnTheFly called for " +
                                    "invalid page: " + pageTag);
                }
                return {
                    title: title,
                    elements: elements,
                };
            },
            fnFinished: self.defaultFinishedFn,
        });
        questionnaire.open();
    },
});

module.exports = Bmi;
