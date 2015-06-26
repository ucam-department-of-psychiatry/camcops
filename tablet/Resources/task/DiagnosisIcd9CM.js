// DiagnosisIcd9CM.js

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

/*jslint node: true, newcap: true, nomen: true */
"use strict";
/*global L */

var dbcommon = require('lib/dbcommon'),
    lang = require('lib/lang'),
    diagnosiscommon = require('task/diagnosiscommon'),
    // PER-SET TABLE
    maintablename = "diagnosis_icd9cm",
    // PER-ITEM TABLE
    itemtablename = "diagnosis_icd9cm_item",
    itemfkname = "diagnosis_icd9cm_id", // FK to diagnosis_icd9cm.id
    itemfkfield = diagnosiscommon.makeFkField(itemfkname),
    itemfieldlist = diagnosiscommon.makeItemFieldList(itemfkname);

// CREATE THE TABLES

dbcommon.createTable(maintablename, diagnosiscommon.mainfieldlist);
dbcommon.createTable(itemtablename, itemfieldlist);

//=============================================================================
// Item class
//=============================================================================

function DiagnosisIcd9CMItem(props) {
    diagnosiscommon.DiagnosisItemBase.call(this, props); // call base constructor
}
lang.inheritPrototype(DiagnosisIcd9CMItem, diagnosiscommon.DiagnosisItemBase);
lang.extendPrototype(DiagnosisIcd9CMItem, {
    _objecttype: DiagnosisIcd9CMItem,
    _tablename: itemtablename,
    _fieldlist: itemfieldlist,

    _fkname: itemfkname,
});

//=============================================================================
// TASK
//=============================================================================

function DiagnosisIcd9CM(patient_id) {
    diagnosiscommon.DiagnosisTaskBase.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(DiagnosisIcd9CM, diagnosiscommon.DiagnosisTaskBase);
lang.extendPrototype(DiagnosisIcd9CM, {
    _objecttype: DiagnosisIcd9CM,
    _tablename: maintablename,

    _itemobjecttype: DiagnosisIcd9CMItem,
    _itemtablename: itemtablename,
    _itemfkname: itemfkname,
    _itemfkfield: itemfkfield,

    _codefilename: "common/CODES_ICD9CM",
    _questionnairetitle: L('t_diagnosis_icd9cm'),
});

module.exports = DiagnosisIcd9CM;
