// Patient.js

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

/*jslint node: true, nomen: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var dbcommon = require('lib/dbcommon'),
    DBCONSTANTS = require('common/DBCONSTANTS'),
    lang = require('lib/lang'),

    // PATIENT TABLE
    NAME_MAXLENGTH = 255,
    tablename = DBCONSTANTS.PATIENT_TABLE,
    sortorder = "surname, forename, id",
    MAIN_ID_FIELD = {name: 'id', type: DBCONSTANTS.TYPE_PK},
    fieldlist = [
        // (a) SQL field names; (b) object member variables;
        // (c) PK must be first (assumed by dbcommon.js)
        MAIN_ID_FIELD,
        {name: 'forename', type: DBCONSTANTS.TYPE_TEXT},
        {name: 'surname', type: DBCONSTANTS.TYPE_TEXT},
        {name: 'dob', type: DBCONSTANTS.TYPE_DATE},
        {name: 'sex', type: DBCONSTANTS.TYPE_TEXT},
        {name: 'address', type: DBCONSTANTS.TYPE_TEXT},
        {name: 'gp', type: DBCONSTANTS.TYPE_TEXT},
        {name: 'other', type: DBCONSTANTS.TYPE_TEXT}
    ],
    i,
    SEX_MALE = "M",
    SEX_FEMALE = "F",
    SEX_X = "X",
    TAG_WARNING = "warn";

function make_id_field(n) {
    return {name: "idnum" + n, type: DBCONSTANTS.TYPE_BIGINT};
}

for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
    fieldlist.push(make_id_field(i));
    fieldlist.push({
        name: DBCONSTANTS.IDDESC_FIELD_PREFIX + i,
        type: DBCONSTANTS.TYPE_TEXT
    }); // only used at upload
    fieldlist.push({
        name: DBCONSTANTS.IDSHORTDESC_FIELD_PREFIX + i,
        type: DBCONSTANTS.TYPE_TEXT
    }); // only used at upload
}
dbcommon.appendCommonFields(fieldlist);


function otherPatientExistsWithSameIdnum(patient_id, idfield, idnum) {
    if (idnum === null) {
        return false; // that's OK!
    }
    return (
        dbcommon.countWhere(
            tablename,
            [ idfield ], // where
            [ idnum ],
            [ MAIN_ID_FIELD ], // where not
            [ patient_id ]
        ) > 0
    );
}


// PATIENT STRUCTURE

function Patient(optional_id) {
    var storedvars,
        i;
    dbcommon.DatabaseObject.call(this); // call base constructor
    if (optional_id !== undefined && optional_id !== null) {
        this.dbread(optional_id);
    } else {
        // Set default values
        storedvars = require('table/storedvars');
        for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
            this[DBCONSTANTS.IDDESC_FIELD_PREFIX + i] = (
                storedvars["idDescription" + i].getValue()
            );
            this[DBCONSTANTS.IDSHORTDESC_FIELD_PREFIX + i] = (
                storedvars["idShortDescription" + i].getValue()
            );
        }
    }
}

lang.inheritPrototype(Patient, dbcommon.DatabaseObject);
lang.extendPrototype(Patient, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)
    _objecttype: Patient,
    _tablename: tablename,
    _fieldlist: fieldlist,
    _sortorder: sortorder,

    // OTHER

    getAge: function (default_value) {
        if (default_value === undefined) {
            default_value = "?";
        }
        if (this.dob === null) {
            return default_value;
        }
        var moment = require('lib/moment'),
            now = moment();
        return Math.floor(now.diff(this.dob, 'years', true));
    },

    getSummary: function () {
        var UICONSTANTS = require('common/UICONSTANTS'),
            forename = this.forename ? this.forename.toUpperCase() : "?",
            surname = this.surname ? this.surname.toUpperCase() : "?",
            sex = this.sex || "?",
            dob = (this.dob !== null ?
                    this.dob.format(UICONSTANTS.DOB_DATE_FORMAT) :
                    "?"
            ),
            s = (
                surname + ", " + forename +
                    " (" + sex + ", age " + this.getAge() + ", DOB " + dob
            ),
            i;

        for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
            if (this["idnum" + i] !== null) {
                s += (", " + this[DBCONSTANTS.IDSHORTDESC_FIELD_PREFIX + i] +
                      "# " + this["idnum" + i]);
            }
        }
        if (this.address) {
            s += "; address = {" + this.address + "}";
        }
        if (this.gp) {
            s += "; GP = {" + this.gp + "}";
        }
        if (this.other) {
            s += "; " + this.other;
        }
        return s + ")";
    },

    getLine1: function () {
        var forename = this.forename ? this.forename.toUpperCase() : "?",
            surname = this.surname ? this.surname.toUpperCase() : "?";
        return surname + ", " + forename;
    },

    getLine2: function () {
        var UICONSTANTS = require('common/UICONSTANTS'),
            sex = this.sex || "?",
            dob = (this.dob !== null ?
                    this.dob.format(UICONSTANTS.DOB_DATE_FORMAT) :
                    "?"
            ),
            s = sex + ", DOB " + dob,
            i;

        for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
            if (this["idnum" + i] !== null) {
                s += (", " + this[DBCONSTANTS.IDSHORTDESC_FIELD_PREFIX + i] +
                      "# " + this["idnum" + i]);
            }
        }
        // s += " (" + L('internal_patient_id') + ": " + this.id + ")";
        if (this.address) {
            s += "; address = {" + this.address + "}";
        }
        if (this.gp) {
            s += "; GP = {" + this.gp + "}";
        }
        if (this.other) {
            s += "; " + this.other;
        }
        return s;
    },

    getNameForSearch: function () {
        return this.getLine1();
    },

    isMale: function () {
        return this.sex === SEX_MALE;
    },

    isFemale: function () {
        return this.sex === SEX_FEMALE;
    },

    satisfiesTabletIdPolicy: function () {
        var idpolicy = require('lib/idpolicy');
        return idpolicy.satisfies_tablet_id_policy(this);
    },

    satisfiesUploadIdPolicy: function () {
        var idpolicy = require('lib/idpolicy');
        return idpolicy.satisfies_upload_id_policy(this);
    },

    satisfiesFinalizeIdPolicy: function () {
        var idpolicy = require('lib/idpolicy');
        return idpolicy.satisfies_finalize_id_policy(this);
    },

    edit: function () {
        var self = this, // for callbacks
            EVENTS = require('common/EVENTS'),
            storedvars = require('table/storedvars'),
            UICONSTANTS = require('common/UICONSTANTS'),
            uifunc = require('lib/uifunc'),
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            backup = {},
            temp = {
                warning_1: "",
                warning_2: ""
            },
            varlist = [
                "forename",
                "surname",
                "dob",
                "sex",
                "address",
                "gp",
                "other"
            ],
            i,
            v,
            sex_options = [
                new KeyValuePair(L('male'), SEX_MALE),
                new KeyValuePair(L('female'), SEX_FEMALE),
                new KeyValuePair(L('sex_x'), SEX_X)
            ],
            idvariables = [],
            upload_warning = (L('patient_warning_upload_policy') + " [" +
                              storedvars.idPolicyUpload.getValue() + "]."),
            finalize_warning = (L('patient_warning_finalize_policy') + " [" +
                                storedvars.idPolicyFinalize.getValue() + "]."),
            pages,
            questionnaire;

        for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
            varlist.push("idnum" + i);
        }

        function copy_vars(src, dst) {
            for (i = 0; i < varlist.length; ++i) {
                v = varlist[i];
                dst[v] = src[v];
            }
        }

        function finalSave() {
            self.dbstore();
            Titanium.App.fireEvent(EVENTS.PATIENT_EDIT_SAVE, {id: self.id});
        }

        copy_vars(self, backup);
        copy_vars(self, temp);

        for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
            idvariables.push({
                type: UICONSTANTS.TYPEDVAR_BIGINT,
                field: "idnum" + i,
                prompt: this[DBCONSTANTS.IDDESC_FIELD_PREFIX + i],
                hint: "",
                mandatory: false,
                min: 0  // no negative ID numbers
            });
        }
        pages = [
            {
                title: L("edit_patient"),
                config: true,
                elements: [
                    {
                        elementTag: TAG_WARNING,
                        type: "QuestionText",
                        field: "warning_1",
                        warning: true,
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                trim: true,
                                field: "surname",
                                prompt: L("surname"),
                                hint: L('hint_surname'),
                                mandatory: false,
                                autocapitalization: Titanium.UI.TEXT_AUTOCAPITALIZATION_ALL,
                                maxLength: NAME_MAXLENGTH
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                trim: true,
                                field: "forename",
                                prompt: L("forename"),
                                hint: L('hint_forename'),
                                mandatory: false,
                                autocapitalization: Titanium.UI.TEXT_AUTOCAPITALIZATION_ALL,
                                maxLength: NAME_MAXLENGTH
                            }
                        ]
                    },
                    { type: "QuestionText", text: L("dob") },
                    {
                        type: "QuestionDateTime",
                        field: "dob",
                        mandatory: false,
                        showTime: false,
                        offerNowButton: false,
                        offerNullButton: true
                    },
                    {
                        type: "QuestionText",
                        text: L("sex")
                    },
                    {
                        type: "QuestionMCQ",
                        field: "sex",
                        mandatory: true,
                        options: sex_options,
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        elementTag: TAG_WARNING,
                        type: "QuestionText",
                        field: "warning_2",
                        warning: true,
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        variables: idvariables
                    },
                    {
                        type: "QuestionTypedVariables",
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "address",
                                prompt: L("address"),
                                hint: L('hint_address'),
                                mandatory: false
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "gp",
                                prompt: L("gp"),
                                hint: L('hint_gp'),
                                mandatory: false
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "other",
                                prompt: L("other_details"),
                                hint: L('hint_other_details'),
                                mandatory: false
                            }
                        ]
                    }
                ]
            }
        ];

        questionnaire = new Questionnaire({
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: function (fieldname) {
                return temp[fieldname];
            },
            fnSetField: function (field, value) {
                temp[field] = value;
            },
            okIconAtEnd: true,
            fnShowNext: function () { // params ignored
                var ok = true,
                    problems = [],
                    idconflict_problems = [],
                    idproblem;
                copy_vars(temp, self);
                // ... but don't save -- this is just temporary to make it
                // easier to check the policies (because those functions
                // operate by default on self)
                // WARNING SET 1
                if (!self.canSave() || !self.satisfiesTabletIdPolicy()) {
                    ok = false;
                    problems.push(L('patient_warning_tablet_policy'));
                }
                if (!self.satisfiesUploadIdPolicy()) {
                    problems.push(upload_warning);
                    // ... but don't set ok = false; user can proceed
                }
                if (!self.satisfiesFinalizeIdPolicy()) {
                    problems.push(finalize_warning);
                    // ... but don't set ok = false; user can proceed
                }
                temp.warning_1 = problems.join("\n\n");
                // WARNING SET 2
                for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
                    idproblem = otherPatientExistsWithSameIdnum(
                        self.id,
                        make_id_field(i),
                        self["idnum" + i]
                    );
                    if (idproblem) {
                        ok = false;
                        idconflict_problems.push(
                            "idnum" + i + " (" +
                                storedvars["idDescription" + i].getValue() +
                                ")"
                        );
                    }
                }
                if (idconflict_problems.length > 0) {
                    temp.warning_2 = (L('other_patient_same_id') + " " +
                                      idconflict_problems.join(", "));
                } else {
                    temp.warning_2 = "";
                }
                // Proceed...
                copy_vars(backup, self); // restore previous state
                questionnaire.setFromFieldByTag(TAG_WARNING);
                return { care: true, showNext: ok };
            },
            fnFinished: function (result) {
                if (result === UICONSTANTS.FINISHED) {
                    // Save the changes.
                    copy_vars(temp, self);
                    finalSave();
                    // Warnings for minor infringements
                    if (!self.satisfiesUploadIdPolicy()) {
                        uifunc.alert(
                            L('patient_fails_id_policy_upload_1') + "\n\n" +
                                storedvars.idPolicyUpload.getValue() + "\n\n" +
                                L('patient_fails_id_policy_upload_2'),
                            L('patient_fails_id_policy_title')
                        );
                    } else if (!self.satisfiesFinalizeIdPolicy()) {
                        uifunc.alert(
                            L('patient_fails_id_policy_finalize_1') + "\n\n" +
                                storedvars.idPolicyFinalize.getValue() +
                                "\n\n" +
                                L('patient_fails_id_policy_finalize_2'),
                            L('patient_fails_id_policy_title')
                        );
                    }
                } else if (result === UICONSTANTS.ABORTED) {
                    // Drop the changes.
                    // We haven't written to the Patient object and haven't
                    // saved it, so if this was a new Patient, nothing will
                    // have been done.
                    return;
                }
            }
        });

        questionnaire.open();
    }
});

// CREATE THE TABLE
dbcommon.createTable(tablename, fieldlist);

// RETURN THE OBJECT
module.exports = Patient;
