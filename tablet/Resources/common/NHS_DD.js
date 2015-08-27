// NHS_DD.js

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

/*jslint node: true, newcap: true */
/*global L */

var KeyValuePair = require('lib/KeyValuePair');

// http://www.datadictionary.nhs.uk/data_dictionary/attributes/p/person/person_marital_status_code_de.asp?shownav=1
exports.PERSON_MARITAL_STATUS_CODE_OPTIONS = [
    new KeyValuePair(L('nhs_person_marital_status_code_S'), 'S'),
    new KeyValuePair(L('nhs_person_marital_status_code_M'), 'M'),
    new KeyValuePair(L('nhs_person_marital_status_code_D'), 'D'),
    new KeyValuePair(L('nhs_person_marital_status_code_W'), 'W'),
    new KeyValuePair(L('nhs_person_marital_status_code_P'), 'P'),
    new KeyValuePair(L('nhs_person_marital_status_code_N'), 'N')
];

// http://www.datadictionary.nhs.uk/data_dictionary/attributes/e/end/ethnic_category_code_de.asp?shownav=1
exports.ETHNIC_CATEGORY_CODE_OPTIONS = [
    new KeyValuePair(L('nhs_ethnic_category_code_A'), 'A'),
    new KeyValuePair(L('nhs_ethnic_category_code_B'), 'B'),
    new KeyValuePair(L('nhs_ethnic_category_code_C'), 'C'),
    new KeyValuePair(L('nhs_ethnic_category_code_D'), 'D'),
    new KeyValuePair(L('nhs_ethnic_category_code_E'), 'E'),
    new KeyValuePair(L('nhs_ethnic_category_code_F'), 'F'),
    new KeyValuePair(L('nhs_ethnic_category_code_G'), 'G'),
    new KeyValuePair(L('nhs_ethnic_category_code_H'), 'H'),
    new KeyValuePair(L('nhs_ethnic_category_code_J'), 'J'),
    new KeyValuePair(L('nhs_ethnic_category_code_K'), 'K'),
    new KeyValuePair(L('nhs_ethnic_category_code_L'), 'L'),
    new KeyValuePair(L('nhs_ethnic_category_code_M'), 'M'),
    new KeyValuePair(L('nhs_ethnic_category_code_N'), 'N'),
    new KeyValuePair(L('nhs_ethnic_category_code_P'), 'P'),
    new KeyValuePair(L('nhs_ethnic_category_code_R'), 'R'),
    new KeyValuePair(L('nhs_ethnic_category_code_S'), 'S'),
    new KeyValuePair(L('nhs_ethnic_category_code_Z'), 'Z')
];
