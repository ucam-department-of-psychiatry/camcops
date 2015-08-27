// CecaQ3.js

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
    tablename = "cecaq3",
    fieldlist = dbcommon.standardTaskFields(),
    extrafields = [
        {name: "s1a_motherfigure_birthmother", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_motherfigure_stepmother", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_motherfigure_femalerelative", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_motherfigure_femalerelative_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s1a_motherfigure_familyfriend", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_motherfigure_fostermother", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_motherfigure_adoptivemother", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_motherfigure_other", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_motherfigure_other_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s1a_fatherfigure_birthfather", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_fatherfigure_stepfather", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_fatherfigure_malerelative", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_fatherfigure_malerelative_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s1a_fatherfigure_familyfriend", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_fatherfigure_fosterfather", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_fatherfigure_adoptivefather", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_fatherfigure_other", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1a_fatherfigure_other_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s1b_institution", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1b_institution_time_years", type: DBCONSTANTS.TYPE_REAL},
        {name: "s1c_mother_died", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1c_father_died", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1c_mother_died_subject_aged", type: DBCONSTANTS.TYPE_REAL},
        {name: "s1c_father_died_subject_aged", type: DBCONSTANTS.TYPE_REAL},
        {name: "s1c_separated_from_mother", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1c_separated_from_father", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s1c_first_separated_from_mother_aged", type: DBCONSTANTS.TYPE_REAL},
        {name: "s1c_first_separated_from_father_aged", type: DBCONSTANTS.TYPE_REAL},
        {name: "s1c_mother_how_long_first_separation_years", type: DBCONSTANTS.TYPE_REAL},
        {name: "s1c_father_how_long_first_separation_years", type: DBCONSTANTS.TYPE_REAL},
        {name: "s1c_mother_separation_reason", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s1c_father_separation_reason", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s1c_describe_experience", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s2a_which_mother_figure", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_which_mother_figure_other_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s2a_q1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q3", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q4", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q5", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q6", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q7", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q8", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q9", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q10", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q11", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q12", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q13", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q14", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q15", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_q16", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2a_extra", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s2b_q1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q3", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q4", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q5", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q6", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q7", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q8", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q9", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q10", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q11", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q12", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q13", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q14", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q15", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q16", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q17", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q1_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q2_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q3_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q4_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q5_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q6_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q7_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q8_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q9_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q10_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q11_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q12_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q13_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q14_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q15_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q16_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_q17_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s2b_age_began", type: DBCONSTANTS.TYPE_REAL},
        {name: "s2b_extra", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s3a_which_father_figure", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_which_father_figure_other_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s3a_q1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q3", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q4", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q5", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q6", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q7", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q8", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q9", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q10", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q11", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q12", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q13", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q14", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q15", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_q16", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3a_extra", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s3b_q1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q3", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q4", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q5", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q6", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q7", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q8", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q9", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q10", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q11", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q12", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q13", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q14", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q15", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q16", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q17", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q1_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q2_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q3_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q4_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q5_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q6_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q7_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q8_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q9_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q10_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q11_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q12_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q13_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q14_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q15_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q16_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_q17_frequency", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3b_age_began", type: DBCONSTANTS.TYPE_REAL},
        {name: "s3b_extra", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s3c_q1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q3", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q4", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q5", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q6", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q7", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q8", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q9", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q10", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q11", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q12", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q13", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q14", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q15", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q16", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_q17", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_which_parent_cared_for", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_parent_mental_problem", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s3c_parent_physical_problem", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s4a_adultconfidant", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4a_adultconfidant_mother", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4a_adultconfidant_father", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4a_adultconfidant_otherrelative", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4a_adultconfidant_familyfriend", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4a_adultconfidant_responsibleadult", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4a_adultconfidant_other", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4a_adultconfidant_other_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s4a_adultconfidant_additional", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s4b_childconfidant", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4b_childconfidant_sister", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4b_childconfidant_brother", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4b_childconfidant_otherrelative", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4b_childconfidant_closefriend", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4b_childconfidant_otherfriend", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4b_childconfidant_other", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4b_childconfidant_other_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s4b_childconfidant_additional", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s4c_closest_mother", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4c_closest_father", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4c_closest_sibling", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4c_closest_otherrelative", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4c_closest_adultfriend", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4c_closest_childfriend", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4c_closest_other", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s4c_closest_other_detail", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s4c_closest_additional", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s5c_physicalabuse", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s5c_abused_by_mother", type: DBCONSTANTS.TYPE_BOOLEAN}, // RNC extra
        {name: "s5c_abused_by_father", type: DBCONSTANTS.TYPE_BOOLEAN}, // RNC extra
        {name: "s5c_mother_abuse_age_began", type: DBCONSTANTS.TYPE_REAL},
        {name: "s5c_father_abuse_age_began", type: DBCONSTANTS.TYPE_REAL},
        {name: "s5c_mother_hit_more_than_once", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s5c_father_hit_more_than_once", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s5c_mother_hit_how", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s5c_father_hit_how", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "s5c_mother_injured", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s5c_father_injured", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s5c_mother_out_of_control", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s5c_father_out_of_control", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s5c_parental_abuse_description", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s5c_abuse_by_nonparent", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s5c_nonparent_abuse_description", type: DBCONSTANTS.TYPE_TEXT},
        {name: "s6_any_unwanted_sexual_experience", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_unwanted_intercourse", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_upsetting_sexual_adult_authority", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_first_age", type: DBCONSTANTS.TYPE_REAL},
        {name: "s6_other_age", type: DBCONSTANTS.TYPE_REAL},
        {name: "s6_first_person_known", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_other_person_known", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_first_relative", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_other_relative", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_first_in_household", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_other_in_household", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_first_more_than_once", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_other_more_than_once", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_first_touch_privates_subject", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_other_touch_privates_subject", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_first_touch_privates_other", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_other_touch_privates_other", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_first_intercourse", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_other_intercourse", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "s6_unwanted_sexual_description", type: DBCONSTANTS.TYPE_TEXT},
        {name: "any_other_comments", type: DBCONSTANTS.TYPE_TEXT}
    ],
    // TASK
    PAGETAG_1A = "1A",
    PAGETAG_1B = "1B",
    PAGETAG_1C = "1C",
    PAGETAG_2A = "2A",
    PAGETAG_2B = "2B",
    PAGETAG_3A = "3A",
    PAGETAG_3B = "3B",
    PAGETAG_3C = "3C",
    PAGETAG_4A = "4A",
    PAGETAG_4B = "4B",
    PAGETAG_4C = "4C",
    PAGETAG_5  = "5",
    PAGETAG_6  = "6",
    ELEMENTTAG_1A_MOTHERTEXT = "1a_mothertext",
    ELEMENTTAG_1A_FATHERTEXT = "1a_fathertext",
    ELEMENTTAG_1A_PEOPLE = "1a_people",
    ELEMENTTAG_1B = "1b",
    ELEMENTTAG_1C_M_DIED = "1c_m_died",
    ELEMENTTAG_1C_F_DIED = "1c_f_died",
    ELEMENTTAG_1C_M_SEP = "1c_m_sep",
    ELEMENTTAG_1C_F_SEP = "1c_f_sep",
    ELEMENTTAG_2A_OTHER = "2a_other",
    ELEMENTTAG_2A_CHOSEN = "2a_chosen",
    ELEMENTTAG_3A_OTHER = "3a_other",
    ELEMENTTAG_3A_CHOSEN = "3a_chosen",
    ELEMENTTAG_2B = "2b",
    ELEMENTTAG_2B_AGE = "2b_age",
    ELEMENTTAG_3B = "3b",
    ELEMENTTAG_3B_AGE = "3b_age",
    ELEMENTTAG_4A_CHOSEN = "4a_chosen",
    ELEMENTTAG_4A_OTHER = "4a_other",
    ELEMENTTAG_4B_CHOSEN = "4b_chosen",
    ELEMENTTAG_4B_OTHER = "4b_other",
    ELEMENTTAG_4C_OTHER = "4c_other",
    ELEMENTTAG_5A_SOMEONE = "5a_someone",
    ELEMENTTAG_5A_MOTHER = "5a_mother",
    ELEMENTTAG_5A_FATHER = "5a_father",
    ELEMENTTAG_6 = "6";

fieldlist.push.apply(fieldlist, extrafields); // append extrafields to fieldlist


// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function CecaQ3(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(CecaQ3, taskcommon.BaseTask);
lang.extendPrototype(CecaQ3, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: CecaQ3,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (
            this.complete_1A() &&
            this.complete_1B() &&
            this.complete_1C() &&
            this.complete_2A() &&
            this.complete_2B() &&
            this.complete_3A() &&
            this.complete_3B() &&
            this.complete_3C() &&
            this.complete_4A() &&
            this.complete_4B() &&
            this.complete_4C() &&
            this.complete_5() &&
            this.complete_6()
        );
    },

    complete_1A_somebody_selected: function () {
        return taskcommon.atLeastOneTrueByFieldnameArray(this, [
            "s1a_motherfigure_birthmother",
            "s1a_motherfigure_stepmother",
            "s1a_motherfigure_femalerelative",
            "s1a_motherfigure_familyfriend",
            "s1a_motherfigure_fostermother",
            "s1a_motherfigure_adoptivemother",
            "s1a_motherfigure_other",
            "s1a_fatherfigure_birthfather",
            "s1a_fatherfigure_stepfather",
            "s1a_fatherfigure_malerelative",
            "s1a_fatherfigure_familyfriend",
            "s1a_fatherfigure_fosterfather",
            "s1a_fatherfigure_adoptivefather",
            "s1a_fatherfigure_other"
        ]);
    },

    complete_1A: function () {
        if (!this.complete_1A_somebody_selected()) {
            return false;
        }
        if (this.s1a_motherfigure_other &&
                !this.s1a_motherfigure_other_detail) {
            return false;
        }
        if (this.s1a_motherfigure_femalerelative &&
                !this.s1a_motherfigure_femalerelative_detail) {
            return false;
        }
        if (this.s1a_fatherfigure_other &&
                !this.s1a_fatherfigure_other_detail) {
            return false;
        }
        if (this.s1a_fatherfigure_malerelative &&
                !this.s1a_fatherfigure_malerelative_detail) {
            return false;
        }
        return true;
    },

    complete_1B: function () {
        if (this.s1b_institution === null) {
            return false;
        }
        if (this.s1b_institution && this.s1b_institution_time_years === null) {
            return false;
        }
        return true;
    },

    complete_1C: function () {
        if (this.s1c_mother_died === null || this.s1c_father_died === null) {
            return false;
        }
        if (this.s1c_mother_died &&
                this.s1c_mother_died_subject_aged === null) {
            return false;
        }
        if (this.s1c_father_died &&
                this.s1c_father_died_subject_aged === null) {
            return false;
        }
        if (this.s1c_separated_from_mother === null ||
                this.s1c_separated_from_father === null) {
            return false;
        }
        if (this.s1c_separated_from_mother) {
            if (
                !taskcommon.isCompleteByFieldnameArray(this, [
                    "s1c_first_separated_from_mother_aged",
                    "s1c_mother_how_long_first_separation_years",
                    "s1c_mother_separation_reason"
                ])
            ) {
                return false;
            }
        }
        if (this.s1c_separated_from_father) {
            if (
                !taskcommon.isCompleteByFieldnameArray(this, [
                    "s1c_first_separated_from_father_aged",
                    "s1c_father_how_long_first_separation_years",
                    "s1c_father_separation_reason"
                ])
            ) {
                return false;
            }
        }
        return true;
    },

    complete_2A: function () {
        var i;
        if (this.s2a_which_mother_figure === null) {
            return false;
        }
        if (this.s2a_which_mother_figure === 0) { // "skip this section"
            return true;
        }
        if (this.s2a_which_mother_figure === 5 &&
                this.s2a_which_mother_figure_other_detail === null) {
            return false;
        }
        for (i = 1; i <= 15; ++i) { // not q16 (siblings)
            if (this["s2a_q" + i] === null) {
                return false;
            }
        }
        return true;
    },

    complete_2B: function () {
        var abuse = false,
            i;
        if (this.s2a_which_mother_figure === 0) {
            return true;
        }
        for (i = 1; i <= 17; ++i) {
            if (this["s2b_q" + i] === null) {
                return false;
            }
            if (this["s2b_q" + i] !== 0) {
                abuse = true;
                if (this["s2b_q" + i + "_frequency"] === null) {
                    return false;
                }
            }
        }
        if (abuse && this.s2b_age_began === null) {
            return false;
        }
        return true;
    },

    complete_3A: function () {
        var i;
        if (this.s3a_which_father_figure === null) {
            return false;
        }
        if (this.s3a_which_father_figure === 0) { // "skip this section"
            return true;
        }
        if (this.s3a_which_father_figure === 5 &&
                this.s3a_which_father_figure_other_detail === null) {
            return false;
        }
        for (i = 1; i <= 15; ++i) { // not q16 (siblings)
            if (this["s3a_q" + i] === null) {
                return false;
            }
        }
        return true;
    },

    complete_3B: function () {
        var abuse = false,
            i;
        if (this.s3a_which_father_figure === 0) {
            return true;
        }
        for (i = 1; i <= 17; ++i) {
            if (this["s3b_q" + i] === null) {
                return false;
            }
            if (this["s3b_q" + i] !== 0) {
                abuse = true;
                if (this["s3b_q" + i + "_frequency"] === null) {
                    return false;
                }
            }
        }
        if (abuse && this.s3b_age_began === null) {
            return false;
        }
        return true;
    },

    complete_3C: function () {
        return taskcommon.isCompleteByFieldnameArray(this, [
            "s3c_q1",
            "s3c_q2",
            "s3c_q3",
            "s3c_q4",
            "s3c_q5",
            "s3c_q6",
            "s3c_q7",
            "s3c_q8",
            "s3c_q9",
            "s3c_q10",
            "s3c_q11",
            "s3c_q12",
            "s3c_q13",
            "s3c_q14",
            "s3c_q15",
            "s3c_q16",
            "s3c_q17",
            "s3c_which_parent_cared_for",
            "s3c_parent_mental_problem",
            "s3c_parent_physical_problem"
        ]);
    },

    complete_4A: function () {
        if (this.s4a_adultconfidant === null) {
            return false;
        }
        if (!this.s4a_adultconfidant) {
            return true;
        }
        if (
            !taskcommon.atLeastOneTrueByFieldnameArray(this, [
                "s4a_adultconfidant_mother",
                "s4a_adultconfidant_father",
                "s4a_adultconfidant_otherrelative",
                "s4a_adultconfidant_familyfriend",
                "s4a_adultconfidant_responsibleadult",
                "s4a_adultconfidant_other"
            ])
        ) {
            return false;
        }
        if (this.s4a_adultconfidant_other &&
                !this.s4a_adultconfidant_other_detail) {
            return false;
        }
        return true;
    },

    complete_4B: function () {
        if (this.s4b_childconfidant === null) {
            return false;
        }
        if (!this.s4b_childconfidant) {
            return true;
        }
        if (
            !taskcommon.atLeastOneTrueByFieldnameArray(this, [
                "s4b_childconfidant_sister",
                "s4b_childconfidant_brother",
                "s4b_childconfidant_otherrelative",
                "s4b_childconfidant_closefriend",
                "s4b_childconfidant_otherfriend",
                "s4b_childconfidant_other"
            ])
        ) {
            return false;
        }
        if (this.s4b_childconfidant_other &&
                !this.s4b_childconfidant_other_detail) {
            return false;
        }
        return true;
    },

    complete_4C: function () {
        var n = 0;
        if (this.s4c_closest_mother) { ++n; }
        if (this.s4c_closest_father) { ++n; }
        if (this.s4c_closest_sibling) { ++n; }
        if (this.s4c_closest_otherrelative) { ++n; }
        if (this.s4c_closest_adultfriend) { ++n; }
        if (this.s4c_closest_childfriend) { ++n; }
        if (this.s4c_closest_other) { ++n; }
        if (n < 2) {
            return false;
        }
        if (this.s4c_closest_other && !this.s4c_closest_other_detail) {
            return false;
        }
        return true;
    },

    complete_5: function () {
        if (this.s5c_physicalabuse === null) {
            return false;
        }
        if (!this.s5c_physicalabuse) {
            return true;
        }
        if (this.s5c_abused_by_mother === null ||
                this.s5c_abused_by_father === null ||
                this.s5c_abuse_by_nonparent === null) {
            return false;
        }
        if (this.s5c_abused_by_mother) {
            if (
                !taskcommon.isCompleteByFieldnameArray(this, [
                    "s5c_mother_abuse_age_began",
                    "s5c_mother_hit_more_than_once",
                    "s5c_mother_hit_how",
                    "s5c_mother_injured",
                    "s5c_mother_out_of_control"
                ])
            ) {
                return false;
            }
        }
        if (this.s5c_abused_by_father) {
            if (
                !taskcommon.isCompleteByFieldnameArray(this, [
                    "s5c_father_abuse_age_began",
                    "s5c_father_hit_more_than_once",
                    "s5c_father_hit_how",
                    "s5c_father_injured",
                    "s5c_father_out_of_control"
                ])
            ) {
                return false;
            }
        }
        return true;
    },

    complete_6: function () {
        if (this.s6_any_unwanted_sexual_experience === null ||
                this.s6_unwanted_intercourse === null ||
                this.s6_upsetting_sexual_adult_authority === null) {
            return false;
        }
        if (!this.s6_any_unwanted_sexual_experience &&
                !this.s6_unwanted_intercourse &&
                !this.s6_upsetting_sexual_adult_authority) {
            return true;
        }
        if (
            !taskcommon.isCompleteByFieldnameArray(this, [
                "s6_first_age",
                "s6_first_person_known",
                "s6_first_relative",
                "s6_first_in_household",
                "s6_first_more_than_once",
                "s6_first_touch_privates_subject",
                "s6_first_touch_privates_other",
                "s6_first_intercourse"
            ])
        ) {
            return false;
        }
        // no checks for "other experience"
        return true;
    },

    getSummary: function () {
        return L('no_summary_see_facsimile') + this.isCompleteSuffix();
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            KeyValuePair = require('lib/KeyValuePair'),
            options_yesno = taskcommon.OPTIONS_NO_YES_BOOLEAN,
            options_separation = [
                new KeyValuePair(L('cecaq3_1c_separation_reason1'), 1),
                new KeyValuePair(L('cecaq3_1c_separation_reason2'), 2),
                new KeyValuePair(L('cecaq3_1c_separation_reason3'), 3),
                new KeyValuePair(L('cecaq3_1c_separation_reason4'), 4),
                new KeyValuePair(L('cecaq3_1c_separation_reason5'), 5),
                new KeyValuePair(L('cecaq3_1c_separation_reason6'), 6)
            ],
            options_2a_whichmotherfigure = [
                new KeyValuePair(L('cecaq3_2a_which_option1'), 1),
                new KeyValuePair(L('cecaq3_2a_which_option2'), 2),
                new KeyValuePair(L('cecaq3_2a_which_option3'), 3),
                new KeyValuePair(L('cecaq3_2a_which_option4'), 4),
                new KeyValuePair(L('cecaq3_2a_which_option5'), 5),
                new KeyValuePair(L('cecaq3_2a_which_option0'), 0)
            ],
            options_3a_whichfatherfigure = [
                new KeyValuePair(L('cecaq3_3a_which_option1'), 1),
                new KeyValuePair(L('cecaq3_3a_which_option2'), 2),
                new KeyValuePair(L('cecaq3_3a_which_option3'), 3),
                new KeyValuePair(L('cecaq3_3a_which_option4'), 4),
                new KeyValuePair(L('cecaq3_3a_which_option5'), 5),
                new KeyValuePair(L('cecaq3_3a_which_option0'), 0)
            ],
            options_5way_no_to_yes = [ // presented in yes-to-no order
                new KeyValuePair(L('cecaq3_options5way_notoyes_5'), 5),
                new KeyValuePair("", 4),
                new KeyValuePair(L('cecaq3_options5way_notoyes_3'), 3),
                new KeyValuePair("", 2),
                new KeyValuePair(L('cecaq3_options5way_notoyes_1'), 1)
            ],
            options3way_noto_yes = [ // presented in yes-to-no order
                new KeyValuePair(L('cecaq3_options3way_noto_yes_2'), 2),
                new KeyValuePair(L('cecaq3_options3way_noto_yes_1'), 1),
                new KeyValuePair(L('cecaq3_options3way_noto_yes_0'), 0)
            ],
            optionsfrequency = [
                new KeyValuePair(L('cecaq3_optionsfrequency0'), 0),
                new KeyValuePair(L('cecaq3_optionsfrequency1'), 1),
                new KeyValuePair(L('cecaq3_optionsfrequency2'), 2),
                new KeyValuePair(L('cecaq3_optionsfrequency3'), 3)
            ],
            options_whichparentcaredfor = [
                new KeyValuePair(L('cecaq3_3c_whichparentcaredfor_option1'), 1),
                new KeyValuePair(L('cecaq3_3c_whichparentcaredfor_option2'), 2),
                new KeyValuePair(L('cecaq3_3c_whichparentcaredfor_option3'), 3),
                new KeyValuePair(L('cecaq3_3c_whichparentcaredfor_option4'), 4),
                new KeyValuePair(L('cecaq3_3c_whichparentcaredfor_option0'), 0)
            ],
            options_hit = [
                new KeyValuePair(L('cecaq3_5_hit_option_1'), 1),
                new KeyValuePair(L('cecaq3_5_hit_option_2'), 2),
                new KeyValuePair(L('cecaq3_5_hit_option_3'), 3),
                new KeyValuePair(L('cecaq3_5_hit_option_4'), 4)
            ],
            generic_subtitles = [
                { beforeIndex:  0, subtitle: "" },
                { beforeIndex:  4, subtitle: "" },
                { beforeIndex:  9, subtitle: "" },
                { beforeIndex: 14, subtitle: "" },
                { beforeIndex: 19, subtitle: "" },
                { beforeIndex: 24, subtitle: "" }
            ],
            pages,
            questionnaire;

        pages = [
            { title: "CECA-Q3", elements: [
                { type: "QuestionHeading", text: L('cecaq3_title'), bold: true },
                { type: "QuestionText", text: L('cecaq3_instruction1') },
                { type: "QuestionText", text: L('cecaq3_instruction2') }
            ] },
            { title: "CECA-Q3 (1A)", pageTag: PAGETAG_1A, elements: [
                { type: "QuestionHeading", text: L('cecaq3_1a_q'), bold: true },
                { type: "QuestionText", text: L('cecaq3_1a_instruction') },
                { type: "ContainerTable", columns: 2, elements: [
                    { type: "ContainerVertical", elements: [
                        {
                            type: "QuestionText",
                            text: L('cecaq3_1a_motherfigures'),
                            bold: true
                        },
                        {
                            elementTag: ELEMENTTAG_1A_PEOPLE,
                            type: "QuestionMultipleResponse",
                            mandatory: false,
                            min_answers: 1, // for when mandatory!
                            showInstruction: false,
                            options: [
                                L('cecaq3_1a_mf_birthmother'),
                                L('cecaq3_1a_mf_stepmother'),
                                L('cecaq3_1a_mf_femalerelative') + " (*)",
                                L('cecaq3_1a_mf_familyfriend'),
                                L('cecaq3_1a_mf_fostermother'),
                                L('cecaq3_1a_mf_adoptivemother'),
                                L('cecaq3_other') + " (*)"
                            ],
                            fields: [
                                's1a_motherfigure_birthmother',
                                's1a_motherfigure_stepmother',
                                's1a_motherfigure_femalerelative',
                                's1a_motherfigure_familyfriend',
                                's1a_motherfigure_fostermother',
                                's1a_motherfigure_adoptivemother',
                                's1a_motherfigure_other'
                            ]
                        },
                        {
                            type: "QuestionText",
                            text: L('cecaq3_rnc_1a_femalerelative_or_other')
                        },
                        {
                            elementTag: ELEMENTTAG_1A_MOTHERTEXT,
                            type: "QuestionTypedVariables",
                            mandatory: false,
                            useColumns: false,
                            variables: [
                                {
                                    type: UICONSTANTS.TYPEDVAR_TEXT,
                                    field: "s1a_motherfigure_femalerelative_detail",
                                    prompt: L('cecaq3_1a_mf_femalerelative')
                                },
                                {
                                    type: UICONSTANTS.TYPEDVAR_TEXT,
                                    field: "s1a_motherfigure_other_detail",
                                    prompt: L('cecaq3_other')
                                }
                            ]
                        }
                    ] },
                    { type: "ContainerVertical", elements: [
                        {
                            type: "QuestionText",
                            text: L('cecaq3_1a_fatherfigures'),
                            bold: true
                        },
                        {
                            elementTag: ELEMENTTAG_1A_PEOPLE,
                            type: "QuestionMultipleResponse",
                            mandatory: false,
                            min_answers: 1, // for when mandatory!
                            showInstruction: false,
                            options: [
                                L('cecaq3_1a_ff_birthfather'),
                                L('cecaq3_1a_ff_stepfather'),
                                L('cecaq3_1a_ff_malerelative') + " (*)",
                                L('cecaq3_1a_ff_familyfriend'),
                                L('cecaq3_1a_ff_fosterfather'),
                                L('cecaq3_1a_ff_adoptivefather'),
                                L('cecaq3_other') + " (*)"
                            ],
                            fields: [
                                's1a_fatherfigure_birthfather',
                                's1a_fatherfigure_stepfather',
                                's1a_fatherfigure_malerelative',
                                's1a_fatherfigure_familyfriend',
                                's1a_fatherfigure_fosterfather',
                                's1a_fatherfigure_adoptivefather',
                                's1a_fatherfigure_other'
                            ]
                        },
                        {
                            type: "QuestionText",
                            text: L('cecaq3_rnc_1a_malerelative_or_other')
                        },
                        {
                            elementTag: ELEMENTTAG_1A_FATHERTEXT,
                            type: "QuestionTypedVariables",
                            mandatory: false,
                            useColumns: false,
                            variables: [
                                {
                                    type: UICONSTANTS.TYPEDVAR_TEXT,
                                    field: "s1a_fatherfigure_malerelative_detail",
                                    prompt: L('cecaq3_1a_ff_malerelative')
                                },
                                {
                                    type: UICONSTANTS.TYPEDVAR_TEXT,
                                    field: "s1a_fatherfigure_other_detail",
                                    prompt: L('cecaq3_other')
                                }
                            ]
                        }
                    ] }
                ] }
            ] },
            { title: "CECA-Q3 (1B)", pageTag: PAGETAG_1B, elements: [
                {
                    type: "QuestionHeading",
                    text: L('cecaq3_1b_q'),
                    bold: true
                },
                {
                    type: "QuestionMCQ",
                    options: options_yesno,
                    field: "s1b_institution",
                    showInstruction: false,
                    horizontal: true
                },
                {
                    type: "QuestionText",
                    text: L('cecaq3_1b_q_how_long'),
                    bold: true
                },
                {
                    elementTag: ELEMENTTAG_1B,
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_REAL,
                            field: "s1b_institution_time_years",
                            hint: L('cecaq3_1b_how_long_prompt')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (1C)", pageTag: PAGETAG_1C, elements: [
                { type: "QuestionHeading", text: L('cecaq3_1c_heading'), bold: true },
                { type: "ContainerTable", columns: 3, elements: [
                    { type: "QuestionText", text: "" },
                    { type: "QuestionText", text: L('cecaq3_mother'), bold: true },
                    { type: "QuestionText", text: L('cecaq3_father'), bold: true },
                    //
                    { type: "QuestionText", text: L('cecaq3_1c_parentdied'), bold: true },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        options: options_yesno,
                        field: "s1c_mother_died",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        options: options_yesno,
                        field: "s1c_father_died",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_1c_parentdiedage') },
                    {
                        elementTag: ELEMENTTAG_1C_M_DIED,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s1c_mother_died_subject_aged",
                                hint: L('cecaq3_age_years')
                            }
                        ]
                    },
                    {
                        elementTag: ELEMENTTAG_1C_F_DIED,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s1c_father_died_subject_aged",
                                hint: L('cecaq3_age_years')
                            }
                        ]
                    },
                    //
                    { type: "QuestionHorizontalRule" },
                    { type: "QuestionHorizontalRule" },
                    { type: "QuestionHorizontalRule" },
                    //
                    { type: "QuestionText", text: L('cecaq3_1c_separated'), bold: true },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        options: options_yesno,
                        field: "s1c_separated_from_mother",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        options: options_yesno,
                        field: "s1c_separated_from_father",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_1c_if_separated') },
                    { type: "QuestionText", text: L('cecaq3_mother'), bold: true },
                    { type: "QuestionText", text: L('cecaq3_father'), bold: true },
                    //
                    { type: "QuestionText", text: L('cecaq3_1c_age_first_separated') },
                    {
                        elementTag: ELEMENTTAG_1C_M_SEP,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s1c_first_separated_from_mother_aged",
                                hint: L('cecaq3_age_years')
                            }
                        ]
                    },
                    {
                        elementTag: ELEMENTTAG_1C_F_SEP,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s1c_first_separated_from_father_aged",
                                hint: L('cecaq3_age_years')
                            }
                        ]
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_1c_how_long_separation') },
                    {
                        elementTag: ELEMENTTAG_1C_M_SEP,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s1c_mother_how_long_first_separation_years",
                                hint: L('cecaq3_1c_years')
                            }
                        ]
                    },
                    {
                        elementTag: ELEMENTTAG_1C_F_SEP,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s1c_father_how_long_first_separation_years",
                                hint: L('cecaq3_1c_years')
                            }
                        ]
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_1c_separation_reason') },
                    {
                        elementTag: ELEMENTTAG_1C_M_SEP,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_separation,
                        field: "s1c_mother_separation_reason",
                        showInstruction: false
                    },
                    {
                        elementTag: ELEMENTTAG_1C_F_SEP,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_separation,
                        field: "s1c_father_separation_reason",
                        showInstruction: false
                    }
                ] },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s1c_describe_experience",
                            prompt: L('cecaq3_please_describe_experience')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (2A)", pageTag: PAGETAG_2A, elements: [
                { type: "QuestionHeading", text: L('cecaq3_2a_heading'), bold: true },
                { type: "QuestionText", text: L('cecaq3_2a_instruction') },
                { type: "QuestionText", text: L('cecaq3_2a_which'), bold: true },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options_2a_whichmotherfigure,
                    field: "s2a_which_mother_figure",
                    showInstruction: false
                },
                {
                    elementTag: ELEMENTTAG_2A_OTHER,
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "s2a_which_mother_figure_other_detail",
                            prompt: L('cecaq3_rnc_if_other_describe'),
                            hint: L('cecaq3_hint_description')
                        }
                    ]
                },
                {
                    elementTag: ELEMENTTAG_2A_CHOSEN,
                    type: "QuestionMCQGrid",
                    mandatory: false,
                    options: options_5way_no_to_yes,
                    subtitles: generic_subtitles,
                    questions: [
                        L('cecaq3_2a_q1'),
                        L('cecaq3_2a_q2'),
                        L('cecaq3_2a_q3'),
                        L('cecaq3_2a_q4'),
                        L('cecaq3_2a_q5'),
                        L('cecaq3_2a_q6'),
                        L('cecaq3_2a_q7'),
                        L('cecaq3_2a_q8'),
                        L('cecaq3_2a_q9'),
                        L('cecaq3_2a_q10'),
                        L('cecaq3_2a_q11'),
                        L('cecaq3_2a_q12'),
                        L('cecaq3_2a_q13'),
                        L('cecaq3_2a_q14'),
                        L('cecaq3_2a_q15'),
                        L('cecaq3_2a_q16')
                    ],
                    fields: [
                        "s2a_q1",
                        "s2a_q2",
                        "s2a_q3",
                        "s2a_q4",
                        "s2a_q5",
                        "s2a_q6",
                        "s2a_q7",
                        "s2a_q8",
                        "s2a_q9",
                        "s2a_q10",
                        "s2a_q11",
                        "s2a_q12",
                        "s2a_q13",
                        "s2a_q14",
                        "s2a_q15",
                        "s2a_q16"
                    ]
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s2a_extra",
                            prompt: L('cecaq3_2a_add_anything')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (2B)", pageTag: PAGETAG_2B, elements: [
                { type: "QuestionHeading", text: L('cecaq3_2b_heading'), bold: true },
                { type: "QuestionText", text: L('cecaq3_2b_instruction') },
                {
                    elementTag: ELEMENTTAG_2B,
                    type: "QuestionMCQGridDouble",
                    mandatory_1: false,
                    mandatory_2: false,
                    options_1: options3way_noto_yes,
                    options_2: optionsfrequency,
                    subtitles: generic_subtitles,
                    questions: [
                        L('cecaq3_2b_q1'),
                        L('cecaq3_2b_q2'),
                        L('cecaq3_2b_q3'),
                        L('cecaq3_2b_q4'),
                        L('cecaq3_2b_q5'),
                        L('cecaq3_2b_q6'),
                        L('cecaq3_2b_q7'),
                        L('cecaq3_2b_q8'),
                        L('cecaq3_2b_q9'),
                        L('cecaq3_2b_q10'),
                        L('cecaq3_2b_q11'),
                        L('cecaq3_2b_q12'),
                        L('cecaq3_2b_q13'),
                        L('cecaq3_2b_q14'),
                        L('cecaq3_2b_q15'),
                        L('cecaq3_2b_q16'),
                        L('cecaq3_2b_q17')
                    ],
                    stem_1: "",
                    stem_2: L('cecaq3_how_frequent'),
                    fields_1: [
                        "s2b_q1",
                        "s2b_q2",
                        "s2b_q3",
                        "s2b_q4",
                        "s2b_q5",
                        "s2b_q6",
                        "s2b_q7",
                        "s2b_q8",
                        "s2b_q9",
                        "s2b_q10",
                        "s2b_q11",
                        "s2b_q12",
                        "s2b_q13",
                        "s2b_q14",
                        "s2b_q15",
                        "s2b_q16",
                        "s2b_q17"
                    ],
                    fields_2: [
                        "s2b_q1_frequency",
                        "s2b_q2_frequency",
                        "s2b_q3_frequency",
                        "s2b_q4_frequency",
                        "s2b_q5_frequency",
                        "s2b_q6_frequency",
                        "s2b_q7_frequency",
                        "s2b_q8_frequency",
                        "s2b_q9_frequency",
                        "s2b_q10_frequency",
                        "s2b_q11_frequency",
                        "s2b_q12_frequency",
                        "s2b_q13_frequency",
                        "s2b_q14_frequency",
                        "s2b_q15_frequency",
                        "s2b_q16_frequency",
                        "s2b_q17_frequency"
                    ]
                },
                {
                    elementTag: ELEMENTTAG_2B_AGE,
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_REAL,
                            field: "s2b_age_began",
                            prompt: L('cecaq3_if_any_what_age'),
                            hint: L('cecaq3_age_years')
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s2b_extra",
                            prompt: L('cecaq3_is_there_more_you_want_to_say')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (3A)", pageTag: PAGETAG_3A, elements: [
                { type: "QuestionHeading", text: L('cecaq3_3a_heading'), bold: true },
                { type: "QuestionText", text: L('cecaq3_3a_instruction') },
                { type: "QuestionText", text: L('cecaq3_3a_which'), bold: true },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options_3a_whichfatherfigure,
                    field: "s3a_which_father_figure",
                    showInstruction: false,
                    hint: L('cecaq3_hint_description')
                },
                {
                    elementTag: ELEMENTTAG_3A_OTHER,
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "s3a_which_father_figure_other_detail",
                            prompt: L('cecaq3_rnc_if_other_describe')
                        }
                    ]
                },
                {
                    elementTag: ELEMENTTAG_3A_CHOSEN,
                    type: "QuestionMCQGrid",
                    options: options_5way_no_to_yes,
                    subtitles: generic_subtitles,
                    mandatory: false,
                    questions: [
                        L('cecaq3_3a_q1'),
                        L('cecaq3_3a_q2'),
                        L('cecaq3_3a_q3'),
                        L('cecaq3_3a_q4'),
                        L('cecaq3_3a_q5'),
                        L('cecaq3_3a_q6'),
                        L('cecaq3_3a_q7'),
                        L('cecaq3_3a_q8'),
                        L('cecaq3_3a_q9'),
                        L('cecaq3_3a_q10'),
                        L('cecaq3_3a_q11'),
                        L('cecaq3_3a_q12'),
                        L('cecaq3_3a_q13'),
                        L('cecaq3_3a_q14'),
                        L('cecaq3_3a_q15'),
                        L('cecaq3_3a_q16')
                    ],
                    fields: [
                        "s3a_q1",
                        "s3a_q2",
                        "s3a_q3",
                        "s3a_q4",
                        "s3a_q5",
                        "s3a_q6",
                        "s3a_q7",
                        "s3a_q8",
                        "s3a_q9",
                        "s3a_q10",
                        "s3a_q11",
                        "s3a_q12",
                        "s3a_q13",
                        "s3a_q14",
                        "s3a_q15",
                        "s3a_q16"
                    ]
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s3a_extra",
                            prompt: L('cecaq3_3a_add_anything')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (3B)", pageTag: PAGETAG_3B, elements: [
                { type: "QuestionHeading", text: L('cecaq3_3b_heading'), bold: true },
                { type: "QuestionText", text: L('cecaq3_3b_rnc_nofather') },
                { type: "QuestionText", text: L('cecaq3_3b_instruction') },
                {
                    elementTag: ELEMENTTAG_3B,
                    type: "QuestionMCQGridDouble",
                    mandatory_1: false,
                    mandatory_2: false,
                    options_1: options3way_noto_yes,
                    options_2: optionsfrequency,
                    subtitles: generic_subtitles,
                    questions: [
                        L('cecaq3_3b_q1'),
                        L('cecaq3_3b_q2'),
                        L('cecaq3_3b_q3'),
                        L('cecaq3_3b_q4'),
                        L('cecaq3_3b_q5'),
                        L('cecaq3_3b_q6'),
                        L('cecaq3_3b_q7'),
                        L('cecaq3_3b_q8'),
                        L('cecaq3_3b_q9'),
                        L('cecaq3_3b_q10'),
                        L('cecaq3_3b_q11'),
                        L('cecaq3_3b_q12'),
                        L('cecaq3_3b_q13'),
                        L('cecaq3_3b_q14'),
                        L('cecaq3_3b_q15'),
                        L('cecaq3_3b_q16'),
                        L('cecaq3_3b_q17')
                    ],
                    stem_1: "",
                    stem_2: L('cecaq3_how_frequent'),
                    fields_1: [
                        "s3b_q1",
                        "s3b_q2",
                        "s3b_q3",
                        "s3b_q4",
                        "s3b_q5",
                        "s3b_q6",
                        "s3b_q7",
                        "s3b_q8",
                        "s3b_q9",
                        "s3b_q10",
                        "s3b_q11",
                        "s3b_q12",
                        "s3b_q13",
                        "s3b_q14",
                        "s3b_q15",
                        "s3b_q16",
                        "s3b_q17"
                    ],
                    fields_2: [
                        "s3b_q1_frequency",
                        "s3b_q2_frequency",
                        "s3b_q3_frequency",
                        "s3b_q4_frequency",
                        "s3b_q5_frequency",
                        "s3b_q6_frequency",
                        "s3b_q7_frequency",
                        "s3b_q8_frequency",
                        "s3b_q9_frequency",
                        "s3b_q10_frequency",
                        "s3b_q11_frequency",
                        "s3b_q12_frequency",
                        "s3b_q13_frequency",
                        "s3b_q14_frequency",
                        "s3b_q15_frequency",
                        "s3b_q16_frequency",
                        "s3b_q17_frequency"
                    ]
                },
                {
                    elementTag: ELEMENTTAG_3B_AGE,
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_REAL,
                            field: "s3b_age_began",
                            prompt: L('cecaq3_if_any_what_age'),
                            hint: L('cecaq3_age_years')
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s3b_extra",
                            prompt: L('cecaq3_is_there_more_you_want_to_say')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (3C)", pageTag: PAGETAG_3C, elements: [
                { type: "QuestionHeading", text: L('cecaq3_3c_heading'), bold: true },
                {
                    type: "QuestionMCQGrid",
                    options: options_5way_no_to_yes,
                    mandatory: true,
                    subtitles: generic_subtitles,
                    questions: [
                        L('cecaq3_3c_q1'),
                        L('cecaq3_3c_q2'),
                        L('cecaq3_3c_q3'),
                        L('cecaq3_3c_q4'),
                        L('cecaq3_3c_q5'),
                        L('cecaq3_3c_q6'),
                        L('cecaq3_3c_q7'),
                        L('cecaq3_3c_q8'),
                        L('cecaq3_3c_q9'),
                        L('cecaq3_3c_q10'),
                        L('cecaq3_3c_q11'),
                        L('cecaq3_3c_q12'),
                        L('cecaq3_3c_q13'),
                        L('cecaq3_3c_q14'),
                        L('cecaq3_3c_q15'),
                        L('cecaq3_3c_q16'),
                        L('cecaq3_3c_q17')
                    ],
                    fields: [
                        "s3c_q1",
                        "s3c_q2",
                        "s3c_q3",
                        "s3c_q4",
                        "s3c_q5",
                        "s3c_q6",
                        "s3c_q7",
                        "s3c_q8",
                        "s3c_q9",
                        "s3c_q10",
                        "s3c_q11",
                        "s3c_q12",
                        "s3c_q13",
                        "s3c_q14",
                        "s3c_q15",
                        "s3c_q16",
                        "s3c_q17"
                    ]
                },
                {
                    type: "QuestionText",
                    text: L('cecaq3_3c_which_parent_cared_for'),
                    bold: true
                },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options_whichparentcaredfor,
                    field: "s3c_which_parent_cared_for",
                    showInstruction: false,
                    horizontal: true
                },
                {
                    type: "QuestionText",
                    text: L('cecaq3_3c_parent_mental_problem'),
                    bold: true
                },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options3way_noto_yes,
                    field: "s3c_parent_mental_problem",
                    showInstruction: false,
                    horizontal: true
                },
                {
                    type: "QuestionText",
                    text: L('cecaq3_3c_parent_physical_problem'),
                    bold: true
                },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options3way_noto_yes,
                    field: "s3c_parent_physical_problem",
                    showInstruction: false,
                    horizontal: true
                }
            ] },
            { title: "CECA-Q3 (4A)", pageTag: PAGETAG_4A, elements: [
                { type: "QuestionHeading", text: L('cecaq3_4_heading') },
                { type: "QuestionText", text: L('cecaq3_4a_q'), bold: true },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options_yesno,
                    field: "s4a_adultconfidant",
                    showInstruction: false,
                    horizontal: true
                },
                { type: "QuestionText", text: L('cecaq3_4_if_so_who'), bold: true },
                {
                    elementTag: ELEMENTTAG_4A_CHOSEN,
                    type: "QuestionMultipleResponse",
                    mandatory: false,
                    min_answers: 1,
                    showInstruction: true,
                    options: [
                        L('cecaq3_4a_option_mother'),
                        L('cecaq3_4a_option_father'),
                        L('cecaq3_4a_option_relative'),
                        L('cecaq3_4a_option_friend'),
                        L('cecaq3_4a_option_responsibleadult'),
                        L('cecaq3_4a_option_other')
                    ],
                    fields: [
                        's4a_adultconfidant_mother',
                        's4a_adultconfidant_father',
                        's4a_adultconfidant_otherrelative',
                        's4a_adultconfidant_familyfriend',
                        's4a_adultconfidant_responsibleadult',
                        's4a_adultconfidant_other'
                    ]
                },
                {
                    elementTag: ELEMENTTAG_4A_OTHER,
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s4a_adultconfidant_other_detail",
                            prompt: L('cecaq3_rnc_if_other_describe')
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s4a_adultconfidant_additional",
                            prompt: L('cecaq3_4_note_anything')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (4B)", pageTag: PAGETAG_4B, elements: [
                { type: "QuestionHeading", text: L('cecaq3_4_heading') },
                { type: "QuestionText", text: L('cecaq3_4b_q'), bold: true },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options_yesno,
                    field: "s4b_childconfidant",
                    showInstruction: false,
                    horizontal: true
                },
                { type: "QuestionText", text: L('cecaq3_4_if_so_who'), bold: true },
                {
                    elementTag: ELEMENTTAG_4B_CHOSEN,
                    type: "QuestionMultipleResponse",
                    mandatory: false,
                    min_answers: 1,
                    showInstruction: true,
                    options: [
                        L('cecaq3_4b_option_sister'),
                        L('cecaq3_4b_option_brother'),
                        L('cecaq3_4b_option_relative'),
                        L('cecaq3_4b_option_closefriend'),
                        L('cecaq3_4b_option_otherfriend'),
                        L('cecaq3_4b_option_other')
                    ],
                    fields: [
                        's4b_childconfidant_sister',
                        's4b_childconfidant_brother',
                        's4b_childconfidant_otherrelative',
                        's4b_childconfidant_closefriend',
                        's4b_childconfidant_otherfriend',
                        's4b_childconfidant_other'
                    ]
                },
                {
                    elementTag: ELEMENTTAG_4B_OTHER,
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s4b_childconfidant_other_detail",
                            prompt: L('cecaq3_rnc_if_other_describe')
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s4b_childconfidant_additional",
                            prompt: L('cecaq3_4_note_anything')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (4C)", pageTag: PAGETAG_4C, elements: [
                { type: "QuestionHeading", text: L('cecaq3_4_heading') },
                { type: "QuestionText", text: L('cecaq3_4c_q'), bold: true },
                {
                    type: "QuestionMultipleResponse",
                    mandatory: true,
                    showInstruction: true,
                    min_answers: 2,
                    max_answers: 2,
                    options: [
                        L('cecaq3_4c_option_mother'),
                        L('cecaq3_4c_option_father'),
                        L('cecaq3_4c_option_sibling'),
                        L('cecaq3_4c_option_relative'),
                        L('cecaq3_4c_option_adultfriend'),
                        L('cecaq3_4c_option_youngfriend'),
                        L('cecaq3_4c_option_other')
                    ],
                    fields: [
                        's4c_closest_mother',
                        's4c_closest_father',
                        's4c_closest_sibling',
                        's4c_closest_otherrelative',
                        's4c_closest_adultfriend',
                        's4c_closest_childfriend',
                        's4c_closest_other'
                    ]
                },
                {
                    elementTag: ELEMENTTAG_4C_OTHER,
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s4c_closest_other_detail",
                            prompt: L('cecaq3_rnc_if_other_describe')
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s4c_closest_additional",
                            prompt: L('cecaq3_4_note_anything')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (5)", pageTag: PAGETAG_5, elements: [
                { type: "QuestionHeading", text: L('cecaq3_5_heading'), bold: true },
                { type: "QuestionText", text: L('cecaq3_5_mainq'), bold: true },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options_yesno,
                    field: "s5c_physicalabuse",
                    showInstruction: false,
                    horizontal: true
                },
                { type: "QuestionText", text: L('cecaq3_if_no_move_on'), bold: true },
                { type: "ContainerTable", columns: 3, elements: [
                    { type: "QuestionText", text: L('cecaq3_if_yes'), bold: true },
                    { type: "QuestionText", text: L('cecaq3_5_motherfigure'), bold: true },
                    { type: "QuestionText", text: L('cecaq3_5_fatherfigure'), bold: true },
                    // RNC extra bit:
                    { type: "QuestionText", text: L('cecaq3_5_did_this_person_hurt_you') },
                    {
                        elementTag: ELEMENTTAG_5A_SOMEONE,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s5c_abused_by_mother",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        elementTag: ELEMENTTAG_5A_SOMEONE,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s5c_abused_by_father",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_5_how_old') },
                    {
                        elementTag: ELEMENTTAG_5A_MOTHER,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s5c_mother_abuse_age_began",
                                hint: L('cecaq3_age_years')
                            }
                        ]
                    },
                    {
                        elementTag: ELEMENTTAG_5A_FATHER,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s5c_father_abuse_age_began",
                                hint: L('cecaq3_age_years')
                            }
                        ]
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_5_hit_more_than_once') },
                    {
                        elementTag: ELEMENTTAG_5A_MOTHER,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s5c_mother_hit_more_than_once",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        elementTag: ELEMENTTAG_5A_FATHER,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s5c_father_hit_more_than_once",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_5_how_hit') },
                    {
                        elementTag: ELEMENTTAG_5A_MOTHER,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_hit,
                        field: "s5c_mother_hit_how",
                        showInstruction: false
                    },
                    {
                        elementTag: ELEMENTTAG_5A_FATHER,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_hit,
                        field: "s5c_father_hit_how",
                        showInstruction: false
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_5_injured') },
                    {
                        elementTag: ELEMENTTAG_5A_MOTHER,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s5c_mother_injured",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        elementTag: ELEMENTTAG_5A_FATHER,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s5c_father_injured",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_5_outofcontrol') },
                    {
                        elementTag: ELEMENTTAG_5A_MOTHER,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s5c_mother_out_of_control",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        elementTag: ELEMENTTAG_5A_FATHER,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s5c_father_out_of_control",
                        showInstruction: false,
                        horizontal: true
                    }
                ] },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s5c_parental_abuse_description",
                            prompt: L('cecaq3_5_can_you_describe_1')
                        }
                    ]
                },
                { type: "QuestionText", text: L('cecaq3_5_anyone_else') },
                {
                    elementTag: ELEMENTTAG_5A_SOMEONE,
                    type: "QuestionMCQ",
                    mandatory: false,
                    options: options_yesno,
                    field: "s5c_abuse_by_nonparent",
                    showInstruction: false,
                    horizontal: true
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s5c_nonparent_abuse_description",
                            prompt: L('cecaq3_5_can_you_describe_2')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (6)", pageTag: PAGETAG_6, elements: [
                { type: "QuestionHeading", text: L('cecaq3_6_heading'), bold: true },
                { type: "QuestionText", text: L('cecaq3_6_any_unwanted'), bold: true },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options3way_noto_yes,
                    field: "s6_any_unwanted_sexual_experience",
                    showInstruction: false,
                    horizontal: true
                },
                { type: "QuestionText", text: L('cecaq3_6_intercourse'), bold: true },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options3way_noto_yes,
                    field: "s6_unwanted_intercourse",
                    showInstruction: false,
                    horizontal: true
                },
                { type: "QuestionText", text: L('cecaq3_6_upset_adult_authority'), bold: true },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    options: options3way_noto_yes,
                    field: "s6_upsetting_sexual_adult_authority",
                    showInstruction: false,
                    horizontal: true
                },
                { type: "QuestionText", text: L('cecaq3_6_if_none_move_on'), bold: true },
                { type: "QuestionText", text: L('cecaq3_6_if_yes_or_unsure'), bold: true },
                { type: "ContainerTable", columns: 3, elements: [
                    { type: "QuestionText", text: "" },
                    { type: "QuestionText", text: L('cecaq3_6_first_experience'), bold: true },
                    { type: "QuestionText", text: L('cecaq3_6_other_experience'), bold: true },
                    //
                    { type: "QuestionText", text: L('cecaq3_6_q1') },
                    {
                        elementTag: ELEMENTTAG_6,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s6_first_age",
                                hint: L('cecaq3_age_years')
                            }
                        ]
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "s6_other_age",
                                hint: L('cecaq3_age_years')
                            }
                        ]
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_6_q2') },
                    {
                        elementTag: ELEMENTTAG_6,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_first_person_known",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_other_person_known",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_6_q3') },
                    {
                        elementTag: ELEMENTTAG_6,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_first_relative",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_other_relative",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_6_q4') },
                    {
                        elementTag: ELEMENTTAG_6,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_first_in_household",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_other_in_household",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_6_q5') },
                    {
                        elementTag: ELEMENTTAG_6,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_first_more_than_once",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_other_more_than_once",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_6_q6') },
                    {
                        elementTag: ELEMENTTAG_6,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_first_touch_privates_subject",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_other_touch_privates_subject",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_6_q7') },
                    {
                        elementTag: ELEMENTTAG_6,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_first_touch_privates_other",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_other_touch_privates_other",
                        showInstruction: false,
                        horizontal: true
                    },
                    //
                    { type: "QuestionText", text: L('cecaq3_6_q8') },
                    {
                        elementTag: ELEMENTTAG_6,
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_first_intercourse",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: false,
                        options: options_yesno,
                        field: "s6_other_intercourse",
                        showInstruction: false,
                        horizontal: true
                    }
                ] },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "s6_unwanted_sexual_description",
                            prompt: L('cecaq3_5_can_you_describe_1')
                        }
                    ]
                }
            ] },
            { title: "CECA-Q3 (end)", elements: [
                { type: "QuestionHeading", text: L('thank_you'), bold: true },
                { type: "QuestionText", text: L('cecaq3_final_1') },
                { type: "QuestionText", text: L('cecaq3_final_2') },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "any_other_comments",
                            prompt: L('cecaq3_any_other_comments')
                        }
                    ]
                }
            ] }
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null; // for garbage collection, since we have closures referring to questionnaire
            },
            fnShowNext: function (currentPage, pageTag) {
                var i,
                    v,
                    abuse,
                    somesex;
                switch (pageTag) {
                case PAGETAG_1A:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1A_PEOPLE,
                        !self.complete_1A_somebody_selected()
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1A_MOTHERTEXT,
                        self.s1a_motherfigure_femalerelative,
                        "s1a_motherfigure_femalerelative_detail"
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1A_MOTHERTEXT,
                        self.s1a_motherfigure_other,
                        "s1a_motherfigure_other_detail"
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1A_FATHERTEXT,
                        self.s1a_fatherfigure_malerelative,
                        "s1a_fatherfigure_malerelative_detail"
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1A_FATHERTEXT,
                        self.s1a_fatherfigure_other,
                        "s1a_fatherfigure_other_detail"
                    );
                    return { care: true, showNext: self.complete_1A() };

                case PAGETAG_1B:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1B,
                        self.s1b_institution,
                        "s1b_institution_time_years"
                    );
                    return { care: true, showNext: self.complete_1B() };

                case PAGETAG_1C:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1C_M_DIED,
                        self.s1c_mother_died
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1C_F_DIED,
                        self.s1c_father_died
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1C_M_SEP,
                        self.s1c_separated_from_mother
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_1C_F_SEP,
                        self.s1c_separated_from_father
                    );
                    return { care: true, showNext: self.complete_1C() };

                case PAGETAG_2A:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_2A_OTHER,
                        self.s2a_which_mother_figure === 5
                    );
                    for (i = 1; i <= 15; ++i) {
                        questionnaire.setMandatoryByTag(
                            ELEMENTTAG_2A_CHOSEN,
                            self.s2a_which_mother_figure !== null &&
                                self.s2a_which_mother_figure !== 0,
                            "s2a_q" + i
                        );
                        // q16 never mandatory
                    }
                    return { care: true, showNext: self.complete_2A() };

                case PAGETAG_2B:
                    abuse = false;
                    for (i = 1; i <= 17; ++i) {
                        questionnaire.setMandatoryByTag(
                            ELEMENTTAG_2B,
                            true,
                            "s2b_q" + i
                        );
                        v = self["s2b_q" + i];
                        if (v) {
                            abuse = true;
                        }
                        questionnaire.setMandatoryByTag(
                            ELEMENTTAG_2B,
                            v, // not null and not zero
                            "s2b_q" + i + "_frequency"
                        );
                    }
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_2B_AGE,
                        abuse,
                        "s2b_age_began"
                    );
                    return { care: true, showNext: self.complete_2B() };

                case PAGETAG_3A:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_3A_OTHER,
                        self.s3a_which_father_figure === 5
                    );
                    for (i = 1; i <= 15; ++i) {
                        questionnaire.setMandatoryByTag(
                            ELEMENTTAG_3A_CHOSEN,
                            self.s3a_which_father_figure !== null &&
                                self.s3a_which_father_figure !== 0,
                            "s3a_q" + i
                        );
                        // q16 never mandatory
                    }
                    return { care: true, showNext: self.complete_3A() };

                case PAGETAG_3B:
                    abuse = false;
                    for (i = 1; i <= 17; ++i) {
                        questionnaire.setMandatoryByTag(
                            ELEMENTTAG_3B,
                            true,
                            "s3b_q" + i
                        );
                        v = self["s3b_q" + i];
                        if (v) {
                            abuse = true;
                        }
                        questionnaire.setMandatoryByTag(
                            ELEMENTTAG_3B,
                            v, // not null and not zero
                            "s3b_q" + i + "_frequency"
                        );
                    }
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_3B_AGE,
                        abuse,
                        "s3b_age_began"
                    );
                    return { care: true, showNext: self.complete_3B() };

                case PAGETAG_3C:
                    return { care: true, showNext: self.complete_3C() };

                case PAGETAG_4A:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_4A_CHOSEN,
                        self.s4a_adultconfidant
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_4A_OTHER,
                        self.s4a_adultconfidant_other,
                        "s4a_adultconfidant_other_detail"
                    );
                    return { care: true, showNext: self.complete_4A() };

                case PAGETAG_4B:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_4B_CHOSEN,
                        self.s4b_childconfidant
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_4B_OTHER,
                        self.s4b_childconfidant_other,
                        "s4b_childconfidant_other_detail"
                    );
                    return { care: true, showNext: self.complete_4B() };

                case PAGETAG_4C:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_4C_OTHER,
                        self.s4c_closest_other,
                        "s4c_closest_other_detail"
                    );
                    return { care: true, showNext: self.complete_4C() };

                case PAGETAG_5:
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_5A_SOMEONE,
                        self.s5c_physicalabuse
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_5A_MOTHER,
                        self.s5c_abused_by_mother
                    );
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_5A_FATHER,
                        self.s5c_abused_by_father
                    );
                    return { care: true, showNext: self.complete_5() };

                case PAGETAG_6:
                    somesex = (
                        self.s6_any_unwanted_sexual_experience ||
                        self.s6_unwanted_intercourse ||
                        self.s6_upsetting_sexual_adult_authority
                    );
                    questionnaire.setMandatoryByTag(ELEMENTTAG_6, somesex);
                    return { care: true, showNext: self.complete_6() };

                default:
                    return { care: false, showNext: false };
                }
            },
            fnNextPage: function (sourcePageId, pageTag) {
                if (pageTag === PAGETAG_2A &&
                        self.s2a_which_mother_figure === 0) {
                    return sourcePageId + 2;
                }
                if (pageTag === PAGETAG_3A &&
                        self.s3a_which_father_figure === 0) {
                    return sourcePageId + 2;
                }
                return sourcePageId + 1;
            },
            fnPreviousPage: function (sourcePageId, pageTag) {
                if (pageTag === PAGETAG_3A &&
                        self.s2a_which_mother_figure === 0) {
                    return sourcePageId - 2;
                }
                if (pageTag === PAGETAG_3C &&
                        self.s3a_which_father_figure === 0) {
                    return sourcePageId - 2;
                }
                return sourcePageId - 1;
            }
        });
        questionnaire.open();
    }

});

module.exports = CecaQ3;
