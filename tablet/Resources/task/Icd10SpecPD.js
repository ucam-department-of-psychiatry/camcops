// Icd10SpecPD.js

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
    tablename = "icd10specpd",
    fieldlist = dbcommon.standardTaskFields(),
    N_GENERAL = 6,
    N_GENERAL_1 = 4,
    N_PARANOID = 7,
    N_SCHIZOID = 9,
    N_DISSOCIAL = 6,
    N_EU = 10,
    N_EUPD_I = 5,
    N_HISTRIONIC = 6,
    N_ANANKASTIC = 8,
    N_ANXIOUS = 5,
    N_DEPENDENT = 6,
    VIRTUALFIELD_HAS_PD = "virtualfield_has_pd",
    TAG_HAS_PD = "has_pd",
    TAG_GENERAL = "general",
    TAG_PARANOID = "paranoid",
    TAG_SCHIZOID = "schizoid",
    TAG_DISSOCIAL = "dissocial",
    TAG_EU = "eu",
    TAG_HISTRIONIC = "histrionic",
    TAG_ANANKASTIC = "anankastic",
    TAG_ANXIOUS = "anxious",
    TAG_DEPENDENT = "dependent";

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'date_pertains_to', type: DBCONSTANTS.TYPE_DATE},
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'skip_paranoid', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'skip_schizoid', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'skip_dissocial', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'skip_eu', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'skip_histrionic', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'skip_anankastic', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'skip_anxious', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'skip_dependent', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'vignette', type: DBCONSTANTS.TYPE_TEXT}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "g", 1, N_GENERAL,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "g1_", 1, N_GENERAL_1,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "paranoid", 1, N_PARANOID,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "schizoid", 1, N_SCHIZOID,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "dissocial", 1, N_DISSOCIAL,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "eu", 1, N_EU,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "histrionic", 1, N_HISTRIONIC,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "anankastic", 1, N_ANANKASTIC,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "anxious", 1, N_ANXIOUS,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "dependent", 1, N_DEPENDENT,
                                DBCONSTANTS.TYPE_BOOLEAN);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Icd10SpecPD(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    var moment = require('lib/moment');
    // Default values
    this.date_pertains_to = moment(); // Default is today
}

lang.inheritPrototype(Icd10SpecPD, taskcommon.BaseTask);
lang.extendPrototype(Icd10SpecPD, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Icd10SpecPD,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Is stuff complete?
    isPDExcluded: function () {
        return (
            lang.falseNotNull(this.g1) ||
            lang.falseNotNull(this.g2) ||
            lang.falseNotNull(this.g3) ||
            lang.falseNotNull(this.g4) ||
            lang.falseNotNull(this.g5) ||
            lang.falseNotNull(this.g6) ||
            (
                    taskcommon.isComplete(this, "g1_", 1, N_GENERAL_1) &&
                    taskcommon.countBooleans(this, "g1_", 1, N_GENERAL_1) <= 1
                )
        );
    },

    isCompleteGeneral: function () {
        return (
            taskcommon.isComplete(this, "g", 1, N_GENERAL) &&
            taskcommon.isComplete(this, "g1_", 1, N_GENERAL_1)
        );
    },

    isCompleteParanoid: function () {
        return taskcommon.isComplete(this, "paranoid", 1, N_PARANOID);
    },

    isCompleteSchizoid: function () {
        return taskcommon.isComplete(this, "schizoid", 1, N_SCHIZOID);
    },

    isCompleteDissocial: function () {
        return taskcommon.isComplete(this, "dissocial", 1, N_DISSOCIAL);
    },

    isCompleteEU: function () {
        return taskcommon.isComplete(this, "eu", 1, N_EU);
    },

    isCompleteHistrionic: function () {
        return taskcommon.isComplete(this, "histrionic", 1, N_HISTRIONIC);
    },

    isCompleteAnankastic: function () {
        return taskcommon.isComplete(this, "anankastic", 1, N_ANANKASTIC);
    },

    isCompleteAnxious: function () {
        return taskcommon.isComplete(this, "anxious", 1, N_ANXIOUS);
    },

    isCompleteDependent: function () {
        return taskcommon.isComplete(this, "dependent", 1, N_DEPENDENT);
    },

    // Meets criteria? These also return null for unknown.
    hasPD: function () {
        if (this.isPDExcluded()) {
            return false;
        }
        if (!this.isCompleteGeneral()) {
            return null;
        }
        return (
            taskcommon.allTrue(this, "g", 1, N_GENERAL) &&
            taskcommon.countBooleans(this, "g1_", 1, N_GENERAL_1) > 1
        );
    },

    hasParanoidPD: function () {
        if (!this.hasPD()) {
            return this.hasPD();
        }
        if (!this.isCompleteParanoid()) {
            return null;
        }
        return (taskcommon.countBooleans(this, "paranoid", 1,
                                         N_PARANOID) >= 4);
    },

    hasSchizoidPD: function () {
        if (!this.hasPD()) {
            return this.hasPD();
        }
        if (!this.isCompleteSchizoid()) { return null; }
        return (taskcommon.countBooleans(this, "schizoid", 1,
                                         N_SCHIZOID) >= 4);
    },

    hasDissocialPD: function () {
        if (!this.hasPD()) { return this.hasPD(); }
        if (!this.isCompleteDissocial()) {
            return null;
        }
        return (taskcommon.countBooleans(this, "dissocial", 1,
                                         N_DISSOCIAL) >= 3);
    },

    hasEUPD_I: function () {
        if (!this.hasPD()) {
            return this.hasPD();
        }
        if (!this.isCompleteEU()) {
            return null;
        }
        return (
            taskcommon.countBooleans(this, "eu", 1, N_EUPD_I) >= 3 &&
            this.eu2
        );
    },

    hasEUPD_B: function () {
        if (!this.hasPD()) {
            return this.hasPD();
        }
        if (!this.isCompleteEU()) {
            return null;
        }
        return (
            taskcommon.countBooleans(this, "eu", 1, N_EUPD_I) >= 3 &&
            taskcommon.countBooleans(this, "eu", N_EUPD_I + 1, N_EU) >= 2
        );
    },

    hasHistrionicPD: function () {
        if (!this.hasPD()) {
            return this.hasPD();
        }
        if (!this.isCompleteHistrionic()) {
            return null;
        }
        return (taskcommon.countBooleans(this, "histrionic", 1,
                                         N_HISTRIONIC) >= 4);
    },

    hasAnankasticPD: function () {
        if (!this.hasPD()) {
            return this.hasPD();
        }
        if (!this.isCompleteAnankastic()) {
            return null;
        }
        return (taskcommon.countBooleans(this, "anankastic", 1,
                                         N_ANANKASTIC) >= 4);
    },

    hasAnxiousPD: function () {
        if (!this.hasPD()) {
            return this.hasPD();
        }
        if (!this.isCompleteAnxious()) {
            return null;
        }
        return (taskcommon.countBooleans(this, "anxious", 1, N_ANXIOUS) >= 4);
    },

    hasDependentPD: function () {
        if (!this.hasPD()) {
            return this.hasPD();
        }
        if (!this.isCompleteDependent()) {
            return null;
        }
        return (taskcommon.countBooleans(this, "dependent", 1,
                                         N_DEPENDENT) >= 4);
    },

    // Standard task functions
    isComplete: function () {
        return (
            this.date_pertains_to !== null && (
                this.isPDExcluded() || (
                    this.isCompleteGeneral() &&
                    (this.skip_paranoid || this.isCompleteParanoid()) &&
                    (this.skip_schizoid || this.isCompleteSchizoid()) &&
                    (this.skip_dissocial || this.isCompleteDissocial()) &&
                    (this.skip_eu || this.isCompleteEU()) &&
                    (this.skip_histrionic || this.isCompleteHistrionic()) &&
                    (this.skip_anankastic || this.isCompleteAnankastic()) &&
                    (this.skip_anxious || this.isCompleteAnxious()) &&
                    (this.skip_dependent || this.isCompleteDependent())
                )
            )
        );
    },

    getSummary: function () {
        var uifunc = require('lib/uifunc');
        return (
            taskcommon.formatDateSimple(this.date_pertains_to) + " " +
            L('icd10pd_meets_general_criteria') + " " +
            uifunc.yesNoUnknown(this.hasPD()) +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc');
        return (
            L('date_pertains_to') + " " +
            taskcommon.formatDateSimple(this.date_pertains_to) + "\n" +
            L('examiners_comments') + ": " + this.comments + "\n" +
            L('icd10pd_meets_general_criteria') + ": " +
            uifunc.yesNoUnknown(this.hasPD()) + "\n" +
            L('icd10_paranoid_pd_title') + ": " +
            uifunc.yesNoUnknown(this.hasParanoidPD()) + "\n" +
            L('icd10_schizoid_pd_title') + ": " +
            uifunc.yesNoUnknown(this.hasSchizoidPD()) + "\n" +
            L('icd10_dissocial_pd_title') + ": " +
            uifunc.yesNoUnknown(this.hasDissocialPD()) + "\n" +
            L('icd10_eu_pd_i_title') + ": " +
            uifunc.yesNoUnknown(this.hasEUPD_I()) + "\n" +
            L('icd10_eu_pd_b_title') + ": " +
            uifunc.yesNoUnknown(this.hasEUPD_B()) + "\n" +
            L('icd10_histrionic_pd_title') + ": " +
            uifunc.yesNoUnknown(this.hasHistrionicPD()) + "\n" +
            L('icd10_anankastic_pd_title') + ": " +
            uifunc.yesNoUnknown(this.hasAnankasticPD()) + "\n" +
            L('icd10_anxious_pd_title') + ": " +
            uifunc.yesNoUnknown(this.hasAnxiousPD()) + "\n" +
            L('icd10_dependent_pd_title') + ": " +
            uifunc.yesNoUnknown(this.hasDependentPD()) + "\n" +
            this.isCompleteSuffix()
        );
    },

    edit: function (readOnly) {
        var self = this,
            uifunc = require('lib/uifunc'),
            UICONSTANTS = require('common/UICONSTANTS'),
            Questionnaire = require('questionnaire/Questionnaire'),
            yes_no_options = taskcommon.OPTIONS_FALSE_TRUE_BOOLEAN,
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        pages = [
            {
                title: L('t_icd10_specific_pd'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionText",
                        text: L('date_pertains_to'),
                        bold: true
                    },
                    {
                        type: "QuestionDateTime",
                        field: "date_pertains_to",
                        showTime: false
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "comments",
                                prompt: L("comments")
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "vignette",
                                prompt: L("icd10_pd_vignette")
                            },
                        ],
                    },
                ],
            },
            {
                pageTag: TAG_GENERAL,
                title: L('icd10pd_general'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general'),
                        bold: true
                    },
                    {
                        elementTag: TAG_GENERAL,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: [ L('icd10pd_G1') ],
                        fields: [ 'g1' ],
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_G1b'),
                        bold: true
                    },
                    {
                        elementTag: TAG_GENERAL,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10pd_G1_",
                            1,
                            N_GENERAL_1
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "g1_",
                            1,
                            N_GENERAL_1
                        ),
                    },
                    {
                        type: "QuestionText",
                        text: L('in_addition'),
                        bold: true
                    },
                    {
                        elementTag: TAG_GENERAL,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10pd_G",
                            2,
                            N_GENERAL
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "g",
                            2,
                            N_GENERAL
                        ),
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_comments'),
                        bold: true
                    },
                ],
            },
            {
                pageTag: TAG_PARANOID,
                title: L('icd10_paranoid_pd_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionBooleanText",
                        text: L('icd10pd_skip_this_pd'),
                        field: "skip_paranoid",
                        bold: true,
                        mandatory: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general_criteria_must_be_met')
                    },
                    {
                        elementTag: TAG_HAS_PD,
                        type: "QuestionText",
                        field: VIRTUALFIELD_HAS_PD,
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10_paranoid_pd_B')
                    },
                    {
                        elementTag: TAG_PARANOID,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_paranoid_pd_",
                            1,
                            N_PARANOID
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "paranoid",
                            1,
                            N_PARANOID
                        ),
                    },
                ],
            },
            {
                pageTag: TAG_SCHIZOID,
                title: L('icd10_schizoid_pd_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionBooleanText",
                        text: L('icd10pd_skip_this_pd'),
                        field: "skip_schizoid",
                        bold: true,
                        mandatory: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general_criteria_must_be_met')
                    },
                    {
                        elementTag: TAG_HAS_PD,
                        type: "QuestionText",
                        field: VIRTUALFIELD_HAS_PD,
                        bold: true
                    },
                    { type: "QuestionText", text: L('icd10_schizoid_pd_B') },
                    {
                        elementTag: TAG_SCHIZOID,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_schizoid_pd_",
                            1,
                            N_SCHIZOID
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "schizoid",
                            1,
                            N_SCHIZOID
                        ),
                    },
                ],
            },
            {
                pageTag: TAG_DISSOCIAL,
                title: L('icd10_dissocial_pd_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionBooleanText",
                        text: L('icd10pd_skip_this_pd'),
                        field: "skip_dissocial",
                        bold: true,
                        mandatory: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general_criteria_must_be_met')
                    },
                    {
                        elementTag: TAG_HAS_PD,
                        type: "QuestionText",
                        field: VIRTUALFIELD_HAS_PD,
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10_dissocial_pd_B')
                    },
                    {
                        elementTag: TAG_DISSOCIAL,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_dissocial_pd_",
                            1,
                            N_DISSOCIAL
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "dissocial",
                            1,
                            N_DISSOCIAL
                        ),
                    },
                ],
            },
            {
                pageTag: TAG_EU,
                title: L('icd10_eu_pd_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionBooleanText",
                        text: L('icd10pd_skip_this_pd'),
                        field: "skip_eu",
                        bold: true,
                        mandatory: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general_criteria_must_be_met')
                    },
                    {
                        elementTag: TAG_HAS_PD,
                        type: "QuestionText",
                        field: VIRTUALFIELD_HAS_PD,
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10_eu_pd_i_title'),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10_eu_pd_i_B')
                    },
                    {
                        elementTag: TAG_EU,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_eu_pd_",
                            1,
                            N_EUPD_I
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "eu",
                            1,
                            N_EUPD_I
                        ),
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10_eu_pd_b_title'),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10_eu_pd_b_B')
                    },
                    {
                        elementTag: TAG_EU,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_eu_pd_",
                            N_EUPD_I + 1,
                            N_EU
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "eu",
                            N_EUPD_I + 1,
                            N_EU
                        ),
                    },
                ],
            },
            {
                pageTag: TAG_HISTRIONIC,
                title: L('icd10_histrionic_pd_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionBooleanText",
                        text: L('icd10pd_skip_this_pd'),
                        field: "skip_histrionic",
                        bold: true,
                        mandatory: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general_criteria_must_be_met')
                    },
                    {
                        elementTag: TAG_HAS_PD,
                        type: "QuestionText",
                        field: VIRTUALFIELD_HAS_PD,
                        bold: true
                    },
                    { type: "QuestionText", text: L('icd10_histrionic_pd_B') },
                    {
                        elementTag: TAG_HISTRIONIC,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_histrionic_pd_",
                            1,
                            N_HISTRIONIC
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "histrionic",
                            1,
                            N_HISTRIONIC
                        ),
                    },
                ],
            },
            {
                pageTag: TAG_ANANKASTIC,
                title: L('icd10_anankastic_pd_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionBooleanText",
                        text: L('icd10pd_skip_this_pd'),
                        field: "skip_anankastic",
                        bold: true,
                        mandatory: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general_criteria_must_be_met')
                    },
                    {
                        elementTag: TAG_HAS_PD,
                        type: "QuestionText",
                        field: VIRTUALFIELD_HAS_PD,
                        bold: true
                    },
                    { type: "QuestionText", text: L('icd10_anankastic_pd_B') },
                    {
                        elementTag: TAG_ANANKASTIC,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_anankastic_pd_",
                            1,
                            N_ANANKASTIC
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "anankastic",
                            1,
                            N_ANANKASTIC
                        ),
                    },
                ],
            },
            {
                pageTag: TAG_ANXIOUS,
                title: L('icd10_anxious_pd_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionBooleanText",
                        text: L('icd10pd_skip_this_pd'),
                        field: "skip_anxious",
                        bold: true,
                        mandatory: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general_criteria_must_be_met')
                    },
                    {
                        elementTag: TAG_HAS_PD,
                        type: "QuestionText",
                        field: VIRTUALFIELD_HAS_PD,
                        bold: true
                    },
                    { type: "QuestionText", text: L('icd10_anxious_pd_B') },
                    {
                        elementTag: TAG_ANXIOUS,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_anxious_pd_",
                            1,
                            N_ANXIOUS
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "anxious",
                            1,
                            N_ANXIOUS
                        ),
                    },
                ],
            },
            {
                pageTag: TAG_DEPENDENT,
                title: L('icd10_dependent_pd_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionBooleanText",
                        text: L('icd10pd_skip_this_pd'),
                        field: "skip_dependent",
                        bold: true,
                        mandatory: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10pd_general_criteria_must_be_met')
                    },
                    {
                        elementTag: TAG_HAS_PD,
                        type: "QuestionText",
                        field: VIRTUALFIELD_HAS_PD,
                        bold: true
                    },
                    { type: "QuestionText", text: L('icd10_dependent_pd_B') },
                    {
                        elementTag: TAG_DEPENDENT,
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10_dependent_pd_",
                            1,
                            N_DEPENDENT
                        ),
                        fields: taskcommon.stringArrayFromSequence(
                            "dependent",
                            1,
                            N_DEPENDENT
                        ),
                    },
                ],
            },
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: function (fieldname, getBlobsAsFilenames) {
                if (fieldname === VIRTUALFIELD_HAS_PD) {
                    return uifunc.yesNoUnknown(self.hasPD());
                }
                return self.defaultGetFieldValueFn(fieldname,
                                                   getBlobsAsFilenames);
            },
            fnSetField: self.defaultSetFieldFn,
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null; // for garbage collection, since we have
                // closures referring to questionnaire
            },
            fnShowNext: function (currentPage, pageTag) {
                switch (pageTag) {
                case TAG_GENERAL:
                    questionnaire.setMandatoryByTag(
                        TAG_GENERAL,
                        !self.isPDExcluded()
                    );
                    break;
                case TAG_PARANOID:
                    questionnaire.setMandatoryByTag(
                        TAG_PARANOID,
                        !(self.isPDExcluded() || self.skip_paranoid)
                    );
                    break;
                case TAG_SCHIZOID:
                    questionnaire.setMandatoryByTag(
                        TAG_SCHIZOID,
                        !(self.isPDExcluded() || self.skip_schizoid)
                    );
                    break;
                case TAG_DISSOCIAL:
                    questionnaire.setMandatoryByTag(
                        TAG_DISSOCIAL,
                        !(self.isPDExcluded() || self.skip_dissocial)
                    );
                    break;
                case TAG_EU:
                    questionnaire.setMandatoryByTag(
                        TAG_EU,
                        !(self.isPDExcluded() || self.skip_eu)
                    );
                    break;
                case TAG_HISTRIONIC:
                    questionnaire.setMandatoryByTag(
                        TAG_HISTRIONIC,
                        !(self.isPDExcluded() || self.skip_histrionic)
                    );
                    break;
                case TAG_ANANKASTIC:
                    questionnaire.setMandatoryByTag(
                        TAG_ANANKASTIC,
                        !(self.isPDExcluded() || self.skip_anankastic)
                    );
                    break;
                case TAG_ANXIOUS:
                    questionnaire.setMandatoryByTag(
                        TAG_ANXIOUS,
                        !(self.isPDExcluded() || self.skip_anxious)
                    );
                    break;
                case TAG_DEPENDENT:
                    questionnaire.setMandatoryByTag(
                        TAG_DEPENDENT,
                        !(self.isPDExcluded() || self.skip_dependent)
                    );
                    break;
                }
                questionnaire.setFromFieldByTag(TAG_HAS_PD);
                return { care: false };
            },
        });
        questionnaire.open();
    },

});

module.exports = Icd10SpecPD;
