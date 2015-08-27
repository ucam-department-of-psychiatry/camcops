// DiagnosisIcd10.js

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
    maintablename = "diagnosis_icd10",
    // PER-ITEM TABLE
    itemtablename = "diagnosis_icd10_item",
    itemfkname = "diagnosis_icd10_id", // FK to diagnosis_icd10.id
    itemfkfield = diagnosiscommon.makeFkField(itemfkname),
    itemfieldlist = diagnosiscommon.makeItemFieldList(itemfkname);

// CREATE THE TABLES

dbcommon.createTable(maintablename, diagnosiscommon.mainfieldlist);
dbcommon.createTable(itemtablename, itemfieldlist);

//=============================================================================
// Item class
//=============================================================================

function DiagnosisIcd10Item(props) {
    diagnosiscommon.DiagnosisItemBase.call(this, props); // call base constructor
}
lang.inheritPrototype(DiagnosisIcd10Item, diagnosiscommon.DiagnosisItemBase);
lang.extendPrototype(DiagnosisIcd10Item, {
    _objecttype: DiagnosisIcd10Item,
    _tablename: itemtablename,
    _fieldlist: itemfieldlist,

    _fkname: itemfkname
});

//=============================================================================
// TASK
//=============================================================================

function DiagnosisIcd10(patient_id) {
    diagnosiscommon.DiagnosisTaskBase.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(DiagnosisIcd10, diagnosiscommon.DiagnosisTaskBase);
lang.extendPrototype(DiagnosisIcd10, {
    _objecttype: DiagnosisIcd10,
    _tablename: maintablename,

    _itemobjecttype: DiagnosisIcd10Item,
    _itemtablename: itemtablename,
    _itemfkname: itemfkname,
    _itemfkfield: itemfkfield,

    _codefilename: "common/CODES_ICD10",
    _questionnairetitle: L('t_diagnosis_icd10')
});

module.exports = DiagnosisIcd10;
