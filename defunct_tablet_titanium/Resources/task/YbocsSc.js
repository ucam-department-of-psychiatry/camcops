// YbocsSc.js

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
/*global L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "ybocssc",
    fieldlist = dbcommon.standardTaskFields(),
    SC_PREFIX = "sc_",
    SUFFIX_CURRENT = "_current",
    SUFFIX_PAST = "_past",
    SUFFIX_PRINCIPAL = "_principal",
    SUFFIX_OTHER = "_other",
    SUFFIX_DETAIL = "_detail",
    GROUPS = [
        "obs_aggressive",
        "obs_contamination",
        "obs_sexual",
        "obs_hoarding",
        "obs_religious",
        "obs_symmetry",
        "obs_misc",
        "obs_somatic",
        "com_cleaning",
        "com_checking",
        "com_repeat",
        "com_counting",
        "com_arranging",
        "com_hoarding",
        "com_misc"
    ],
    ITEMS = [
        "obs_aggressive_harm_self",
        "obs_aggressive_harm_others",
        "obs_aggressive_imagery",
        "obs_aggressive_obscenities",
        "obs_aggressive_embarrassing",
        "obs_aggressive_impulses",
        "obs_aggressive_steal",
        "obs_aggressive_accident",
        "obs_aggressive_responsible",
        "obs_aggressive_other",

        "obs_contamination_bodily_waste",
        "obs_contamination_dirt",
        "obs_contamination_environmental",
        "obs_contamination_household",
        "obs_contamination_animals",
        "obs_contamination_sticky",
        "obs_contamination_ill",
        "obs_contamination_others_ill",
        "obs_contamination_feeling",
        "obs_contamination_other",

        "obs_sexual_forbidden",
        "obs_sexual_children_incest",
        "obs_sexual_homosexuality",
        "obs_sexual_to_others",
        "obs_sexual_other",

        "obs_hoarding_other",

        "obs_religious_sacrilege",
        "obs_religious_morality",
        "obs_religious_other",

        "obs_symmetry_with_magical",
        "obs_symmetry_without_magical",

        "obs_misc_know_remember",
        "obs_misc_fear_saying",
        "obs_misc_fear_not_saying",
        "obs_misc_fear_losing",
        "obs_misc_intrusive_nonviolent_images",
        "obs_misc_intrusive_sounds",
        "obs_misc_bothered_sounds",
        "obs_misc_numbers",
        "obs_misc_colours",
        "obs_misc_superstitious",
        "obs_misc_other",

        "obs_somatic_illness",
        "obs_somatic_appearance",
        "obs_somatic_other",

        "com_cleaning_handwashing",
        "com_cleaning_toileting",
        "com_cleaning_cleaning_items",
        "com_cleaning_other_contaminant_avoidance",
        "com_cleaning_other",

        "com_checking_locks_appliances",
        "com_checking_not_harm_others",
        "com_checking_not_harm_self",
        "com_checking_nothing_bad_happens",
        "com_checking_no_mistake",
        "com_checking_somatic",
        "com_checking_other",

        "com_repeat_reread_rewrite",
        "com_repeat_routine",
        "com_repeat_other",

        "com_counting_other",

        "com_arranging_other",

        "com_hoarding_other",

        "com_misc_mental_rituals",
        "com_misc_lists",
        "com_misc_tell_ask",
        "com_misc_touch",
        "com_misc_blink_stare",
        "com_misc_prevent_harm_self",
        "com_misc_prevent_harm_others",
        "com_misc_prevent_terrible",
        "com_misc_eating_ritual",
        "com_misc_superstitious",
        "com_misc_trichotillomania",
        "com_misc_self_harm",
        "com_misc_other"
    ],
    tmpindex,
    tmpname;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
for (tmpindex = 0; tmpindex < ITEMS.length; ++tmpindex) {
    tmpname = ITEMS[tmpindex];
    fieldlist.push({
        name: tmpname + SUFFIX_CURRENT,
        type: DBCONSTANTS.TYPE_BOOLEAN
    });
    fieldlist.push({
        name: tmpname + SUFFIX_PAST,
        type: DBCONSTANTS.TYPE_BOOLEAN
    });
    fieldlist.push({
        name: tmpname + SUFFIX_PRINCIPAL,
        type: DBCONSTANTS.TYPE_BOOLEAN
    });
    if (lang.endsWith(tmpname, SUFFIX_OTHER)) {
        fieldlist.push({
            name: tmpname + SUFFIX_DETAIL,
            type: DBCONSTANTS.TYPE_TEXT
        });
    }
}

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function YbocsSc(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(YbocsSc, taskcommon.BaseTask);
lang.extendPrototype(YbocsSc, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: YbocsSc,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "ybocs",  // same as Y-BOCS
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    // Standard task functions
    isComplete: function () {
        return true;
    },

    getSummary: function () {
        return "See facsimile" + this.isCompleteSuffix();
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
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

        elements = [
            {
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('sc_instruction_1')
            },
            {
                type: "QuestionText",
                text: this.XSTRING('sc_instruction_2')
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
                        text: this.XSTRING(SC_PREFIX + itemname)
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L("current"),
                        field: itemname + SUFFIX_CURRENT,
                        mandatory: false
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L("past"),
                        field: itemname + SUFFIX_PAST,
                        mandatory: false
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L("principal"),
                        field: itemname + SUFFIX_PRINCIPAL,
                        mandatory: false
                    }
                );
                if (lang.endsWith(itemname, SUFFIX_OTHER)) {
                    detailelements.push({
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: true,
                        variables: [{
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: itemname + SUFFIX_DETAIL,
                            prompt: L('specify')
                        }]
                    });
                }
            }
            elements.push(
                {
                    type: "QuestionText",
                    bold: true,
                    text: this.XSTRING(SC_PREFIX + groupname)
                },
                {
                    type: "ContainerTable",
                    columns: 4,
                    columnWidths: ["55%", "15%", "15%", "15%"],
                    elements: tableelements
                }
            );
            if (detailelements.length > 0) {
                elements.push.apply(elements, detailelements);
            }
        }

        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        pages.push({
            title: this.XSTRING('sc_title'),
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

module.exports = YbocsSc;
