// CODES_ICD10.js

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global L */

//=============================================================================
// Preamble (code-processing functions) (md = mantissa digit)
//=============================================================================

var diagnosticcodelistfunc = require('lib/diagnosticcodelistfunc'),
    ICD10PREFIX = "icd10_",
    CODELIST = [],
    i;

function gc(code) {
    // generic ICD-10 code
    return { code: code, description: L(ICD10PREFIX + code) };
}

function add_cd(code, description) {
    CODELIST.push({ code: code, description: description });
}

function add_gc(code) {
    CODELIST.push(gc(code));
}

function add_gc_array(a) {
    var i;
    for (i = 0; i < a.length; ++i) {
        CODELIST.push(gc(a[i]));
    }
}

function processDementiaSub(code, dementia, md2) {
    var additional_symptoms_type = ": " + L("icd10_dementia_x" + md2);
    add_cd(code + md2, dementia + additional_symptoms_type);
    add_cd(code + md2 + "0", dementia + additional_symptoms_type + ": " +
           L("icd10_dementia_xx0"));
    add_cd(code + md2 + "1", dementia + additional_symptoms_type + ": " +
           L("icd10_dementia_xx1"));
    add_cd(code + md2 + "2", dementia + additional_symptoms_type + ": " +
           L("icd10_dementia_xx2"));
}

function processDementia(code) {
    var dementia = L(ICD10PREFIX + code),
        i;
    add_cd(code, dementia);
    for (i = 0; i <= 4; ++i) {
        processDementiaSub(code, dementia, i);
    }
}

function processSubstance(code) {
    var alcohol = (code === "F10"),
        substance = L(ICD10PREFIX + code),
        i,
        lastsuffix = alcohol ? 7 : 6,
        code26 = (alcohol ?
                  L("icd10_substance_26_alcohol") :
                  L("icd10_substance_26_other"));
        // ... "dipsomania" seems alcohol-specific!

        // var definition order is fixed:
        // http://benalman.com/news/2012/05/multiple-var-statements-javascript/

    add_cd(code, substance);
    add_cd(code + ".0", substance + ", " + L("icd10_substance_0"));
    for (i = 0; i <= lastsuffix; ++i) {
        add_cd(code + ".0" + i, substance + ", " + L("icd10_substance_0") +
               ": " + L("icd10_substance_0" + i));
    }
    add_cd(code + ".1", substance + ", " + L("icd10_substance_1"));
    add_cd(code + ".2", substance + ", " + L("icd10_substance_2"));
    add_cd(code + ".20", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_20"));
    add_cd(code + ".200", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_200"));
    add_cd(code + ".201", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_201"));
    add_cd(code + ".202", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_202"));
    add_cd(code + ".21", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_21"));
    add_cd(code + ".22", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_22"));
    add_cd(code + ".23", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_23"));
    add_cd(code + ".24", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_24"));
    add_cd(code + ".241", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_241"));
    add_cd(code + ".242", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_242"));
    add_cd(code + ".25", substance + ", " + L("icd10_substance_2") + ": " +
           L("icd10_substance_25"));
    add_cd(code + ".26", substance + ", " + L("icd10_substance_2") + ": " +
           code26);
    add_cd(code + ".3", substance + ", " + L("icd10_substance_3"));
    add_cd(code + ".30", substance + ", " + L("icd10_substance_3") + ": " +
           L("icd10_substance_30"));
    add_cd(code + ".31", substance + ", " + L("icd10_substance_3") + ": " +
           L("icd10_substance_31"));
    add_cd(code + ".4", substance + ", " + L("icd10_substance_4"));
    add_cd(code + ".40", substance + ", " + L("icd10_substance_4") + ": " +
           L("icd10_substance_40"));
    add_cd(code + ".41", substance + ", " + L("icd10_substance_4") + ": " +
           L("icd10_substance_41"));
    add_cd(code + ".5", substance + ", " + L("icd10_substance_5"));
    add_cd(code + ".50", substance + ", " + L("icd10_substance_5") + ": " +
           L("icd10_substance_50"));
    add_cd(code + ".51", substance + ", " + L("icd10_substance_5") + ": " +
           L("icd10_substance_51"));
    add_cd(code + ".52", substance + ", " + L("icd10_substance_5") + ": " +
           L("icd10_substance_52"));
    add_cd(code + ".53", substance + ", " + L("icd10_substance_5") + ": " +
           L("icd10_substance_53"));
    add_cd(code + ".54", substance + ", " + L("icd10_substance_5") + ": " +
           L("icd10_substance_54"));
    add_cd(code + ".55", substance + ", " + L("icd10_substance_5") + ": " +
           L("icd10_substance_55"));
    add_cd(code + ".56", substance + ", " + L("icd10_substance_5") + ": " +
           L("icd10_substance_56"));
    add_cd(code + ".6", substance + ", " + L("icd10_substance_6"));
    add_cd(code + ".7", substance + ", " + L("icd10_substance_7"));
    add_cd(code + ".70", substance + ", " + L("icd10_substance_7") + ": " +
           L("icd10_substance_70"));
    add_cd(code + ".71", substance + ", " + L("icd10_substance_7") + ": " +
           L("icd10_substance_71"));
    add_cd(code + ".72", substance + ", " + L("icd10_substance_7") + ": " +
           L("icd10_substance_72"));
    add_cd(code + ".73", substance + ", " + L("icd10_substance_7") + ": " +
           L("icd10_substance_73"));
    add_cd(code + ".74", substance + ", " + L("icd10_substance_7") + ": " +
           L("icd10_substance_74"));
    add_cd(code + ".75", substance + ", " + L("icd10_substance_7") + ": " +
           L("icd10_substance_75"));
    add_cd(code + ".8", substance + ", " + L("icd10_substance_8"));
    add_cd(code + ".9", substance + ", " + L("icd10_substance_9"));
}

function processSchizophrenia(code) {
    var sztype = L(ICD10PREFIX + code);
    add_cd(code, sztype);
    // Green/Blue Book extras:
    add_cd(code + "0", sztype + ": " + L("icd10_schizophrenia_0"));
    add_cd(code + "1", sztype + ": " + L("icd10_schizophrenia_1"));
    add_cd(code + "2", sztype + ": " + L("icd10_schizophrenia_2"));
    add_cd(code + "3", sztype + ": " + L("icd10_schizophrenia_3"));
    add_cd(code + "4", sztype + ": " + L("icd10_schizophrenia_4"));
    add_cd(code + "5", sztype + ": " + L("icd10_schizophrenia_5"));
    add_cd(code + "8", sztype + ": " + L("icd10_schizophrenia_8"));
    add_cd(code + "9", sztype + ": " + L("icd10_schizophrenia_9"));
}

function processSelfHarmSub(code, method, md1) {
    var location = ", " + L("icd10_selfharm_" + md1);
    add_cd(code + "." + md1, method + location);
    add_cd(code + "." + md1 + "0", method + location + ", " +
           L("icd10_selfharm_x0"));
    add_cd(code + "." + md1 + "1", method + location + ", " +
           L("icd10_selfharm_x1"));
    add_cd(code + "." + md1 + "2", method + location + ", " +
           L("icd10_selfharm_x2"));
    add_cd(code + "." + md1 + "3", method + location + ", " +
           L("icd10_selfharm_x3"));
    add_cd(code + "." + md1 + "4", method + location + ", " +
           L("icd10_selfharm_x4"));
    add_cd(code + "." + md1 + "8", method + location + ", " +
           L("icd10_selfharm_x8"));
    add_cd(code + "." + md1 + "9", method + location + ", " +
           L("icd10_selfharm_x9"));
}

function processSelfHarm(x_number) {
    var code = "X" + x_number,
        method = L("icd10_X" + x_number),
        i;
    add_cd(code, method);
    for (i = 0; i <= 9; ++i) {
        processSelfHarmSub(code, method, i);
    }
}

//=============================================================================
// F
//=============================================================================

CODELIST.push({
    startcode: "F00",
    endcode: "F09",
    description: L("icd10_range_F0"),
    range: true
});

add_gc("F00");
processDementia("F00.0");
processDementia("F00.1");
processDementia("F00.2");
processDementia("F00.9");

add_gc("F01");
processDementia("F01.0");
processDementia("F01.1");
processDementia("F01.2");
processDementia("F01.3");
processDementia("F01.8");
processDementia("F01.9");

add_gc("F02");
processDementia("F02.0");
processDementia("F02.1");
processDementia("F02.2");
processDementia("F02.3");
processDementia("F02.4");
processDementia("F02.8");

add_gc("F03");
processDementia("F03.0");

add_gc_array([
    "F04",
    "F05",
    "F05.0",
    "F05.1",
    "F05.8",
    "F05.9",
    "F06",
    "F06.0",
    "F06.1",
    "F06.2",
    "F06.3",
    "F06.4",
    "F06.5",
    "F06.6",
    "F06.7",
    "F06.8",
    "F06.9",
    "F07",
    "F07.0",
    "F07.1",
    "F07.2",
    "F07.8",
    "F07.9",
    "F09"
]);

CODELIST.push({
    startcode: "F10",
    endcode: "F19",
    description: L("icd10_range_F1"),
    range: true
});
for (i = 10; i <= 19; ++i) {
    processSubstance("F" + i);
}

CODELIST.push({
    startcode: "F20",
    endcode: "F29",
    description: L("icd10_range_F2"),
    range: true
});
add_gc("F20");
processSchizophrenia("F20.0");
processSchizophrenia("F20.1");
processSchizophrenia("F20.2");
processSchizophrenia("F20.3");
processSchizophrenia("F20.4");
processSchizophrenia("F20.5");
processSchizophrenia("F20.6");
processSchizophrenia("F20.8");
processSchizophrenia("F20.9");

add_gc_array([
    "F21",
    "F22",
    "F22.0",
    "F22.8",
    "F22.9",
    "F23",
    "F23.0",
    "F23.1",
    "F23.2",
    "F23.3",
    "F23.8",
    "F23.9",
    "F23.90",
    "F23.91",
    "F24",
    "F25",
    "F25.0",
    "F25.00",
    "F25.01",
    "F25.1",
    "F25.10",
    "F25.11",
    "F25.2",
    "F25.20",
    "F25.21",
    "F25.8",
    "F25.80",
    "F25.81",
    "F25.9",
    "F25.90",
    "F25.91",
    "F28",
    "F29"
]);
CODELIST.push({
    startcode: "F30",
    endcode: "F39",
    description: L("icd10_range_F3"),
    range: true
});
add_gc_array([
    "F30",
    "F30.0",
    "F30.1",
    "F30.2",
    "F30.20",
    "F30.21",
    "F30.8",
    "F30.9",
    "F31",
    "F31.0",
    "F31.1",
    "F31.2",
    "F31.20",
    "F31.21",
    "F31.3",
    "F31.30",
    "F31.31",
    "F31.4",
    "F31.5",
    "F31.50",
    "F31.51",
    "F31.6",
    "F31.7",
    "F31.8",
    "F31.9",
    "F32",
    "F32.0",
    "F32.00",
    "F32.01",
    "F32.1",
    "F32.10",
    "F32.11",
    "F32.2",
    "F32.3",
    "F32.30",
    "F32.31",
    "F32.8",
    "F32.9",
    "F33",
    "F33.0",
    "F33.00",
    "F33.01",
    "F33.1",
    "F33.10",
    "F33.11",
    "F33.2",
    "F33.3",
    "F33.30",
    "F33.31",
    "F33.4",
    "F33.8",
    "F33.9",
    "F34",
    "F34.0",
    "F34.1",
    "F34.8",
    "F34.9",
    "F38",
    "F38.0",
    "F38.00",
    "F38.1",
    "F38.10",
    "F38.8",
    "F39"
]);

CODELIST.push({
    startcode: "F40",
    endcode: "F48",
    description: L("icd10_range_F4"),
    range: true
});
add_gc_array([
    "F40",
    "F40.0",
    "F40.00",
    "F40.01",
    "F40.1",
    "F40.2",
    "F40.8",
    "F40.9",
    "F41",
    "F41.0",
    "F41.00",
    "F41.01",
    "F41.1",
    "F41.2",
    "F41.3",
    "F41.8",
    "F41.9",
    "F42",
    "F42.0",
    "F42.1",
    "F42.2",
    "F42.8",
    "F42.9",
    "F43",
    "F43.0",
    "F43.00",
    "F43.01",
    "F43.02",
    "F43.1",
    "F43.2",
    "F43.20",
    "F43.21",
    "F43.22",
    "F43.23",
    "F43.24",
    "F43.25",
    "F43.28",
    "F43.8",
    "F43.9",
    "F44",
    "F44.0",
    "F44.1",
    "F44.2",
    "F44.3",
    "F44.4",
    "F44.5",
    "F44.6",
    "F44.7",
    "F44.8",
    "F44.80",
    "F44.81",
    "F44.82",
    "F44.88",
    "F44.9",
    "F45",
    "F45.0",
    "F45.1",
    "F45.2",
    "F45.3",
    "F45.30",
    "F45.31",
    "F45.32",
    "F45.33",
    "F45.34",
    "F45.38",
    "F45.4",
    "F45.8",
    "F45.9",
    "F48",
    "F48.0",
    "F48.1",
    "F48.8",
    "F48.9"
]);

CODELIST.push({
    startcode: "F50",
    endcode: "F59",
    description: L("icd10_range_F5"),
    range: true
});
add_gc_array([
    "F50",
    "F50.0",
    "F50.1",
    "F50.2",
    "F50.3",
    "F50.4",
    "F50.5",
    "F50.8",
    "F50.9",
    "F51",
    "F51.0",
    "F51.1",
    "F51.2",
    "F51.3",
    "F51.4",
    "F51.5",
    "F51.8",
    "F51.9",
    "F52",
    "F52.0",
    "F52.1",
    "F52.10",
    "F52.11",
    "F52.2",
    "F52.3",
    "F52.4",
    "F52.5",
    "F52.6",
    "F52.7",
    "F52.8",
    "F52.9",
    "F53",
    "F53.0",
    "F53.1",
    "F53.8",
    "F53.9",
    "F54",
    "F55",
    "F59"
]);

CODELIST.push({
    startcode: "F60",
    endcode: "F69",
    description: L("icd10_range_F6"),
    range: true
});
add_gc_array([
    "F60",
    "F60.0",
    "F60.1",
    "F60.2",
    "F60.3",
    "F60.30",
    "F60.31",
    "F60.4",
    "F60.5",
    "F60.6",
    "F60.7",
    "F60.8",
    "F60.9",
    "F61",
    "F62",
    "F62.0",
    "F62.1",
    "F62.8",
    "F62.9",
    "F63",
    "F63.0",
    "F63.1",
    "F63.2",
    "F63.3",
    "F63.8",
    "F63.9",
    "F64",
    "F64.0",
    "F64.1",
    "F64.2",
    "F64.8",
    "F64.9",
    "F65",
    "F65.0",
    "F65.1",
    "F65.2",
    "F65.3",
    "F65.4",
    "F65.5",
    "F65.6",
    "F65.8",
    "F65.9",
    "F66",
    "F66.0",
    "F66.1",
    "F66.2",
    "F66.8",
    "F66.9",
    "F66.90",
    "F66.91",
    "F66.92",
    "F66.98",
    "F68",
    "F68.0",
    "F68.1",
    "F68.8",
    "F69"
]);

CODELIST.push({
    startcode: "F70",
    endcode: "F79",
    description: L("icd10_range_F7"),
    range: true
});
add_gc_array([
    "F70",
    "F70.0",
    "F70.1",
    "F70.8",
    "F70.9",
    "F71",
    "F71.0",
    "F71.1",
    "F71.8",
    "F71.9",
    "F72",
    "F72.0",
    "F72.1",
    "F72.8",
    "F72.9",
    "F73",
    "F73.0",
    "F73.1",
    "F73.8",
    "F73.9",
    "F78",
    "F78.0",
    "F78.1",
    "F78.8",
    "F78.9",
    "F79",
    "F79.0",
    "F79.1",
    "F79.8",
    "F79.9"
]);

CODELIST.push({
    startcode: "F80",
    endcode: "F89",
    description: L("icd10_range_F8"),
    range: true
});
add_gc_array([
    "F80",
    "F80.0",
    "F80.1",
    "F80.2",
    "F80.3",
    "F80.8",
    "F80.9",
    "F81",
    "F81.0",
    "F81.1",
    "F81.2",
    "F81.3",
    "F81.8",
    "F81.9",
    "F82",
    "F83",
    "F84",
    "F84.0",
    "F84.1",
    "F84.10",
    "F84.11",
    "F84.12",
    "F84.2",
    "F84.3",
    "F84.4",
    "F84.5",
    "F84.8",
    "F84.9",
    "F88",
    "F89"
]);

CODELIST.push({
    startcode: "F90",
    endcode: "F98",
    description: L("icd10_range_F90_F98"),
    range: true
});
add_gc_array([
    "F90",
    "F90.0",
    "F90.1",
    "F90.8",
    "F90.9",
    "F91",
    "F91.0",
    "F91.1",
    "F91.2",
    "F91.3",
    "F91.8",
    "F91.9",
    "F92",
    "F92.0",
    "F92.8",
    "F92.9",
    "F93",
    "F93.0",
    "F93.1",
    "F93.2",
    "F93.3",
    "F93.8",
    "F93.80",
    "F93.9",
    "F94",
    "F94.0",
    "F94.1",
    "F94.2",
    "F94.8",
    "F94.9",
    "F95",
    "F95.0",
    "F95.1",
    "F95.2",
    "F95.8",
    "F95.9",
    "F98",
    "F98.0",
    "F98.00",
    "F98.01",
    "F98.02",
    "F98.1",
    "F98.10",
    "F98.11",
    "F98.12",
    "F98.2",
    "F98.3",
    "F98.4",
    "F98.40",
    "F98.41",
    "F98.42",
    "F98.5",
    "F98.6",
    "F98.8",
    "F98.9"
]);

add_gc("F99");

//=============================================================================
// R
//=============================================================================

CODELIST.push({
    startcode: "R40",
    endcode: "R46",
    description: L("icd10_range_R"),
    range: true
});
add_gc_array([
    "R40",
    "R40.0",
    "R40.1",
    "R40.2",
    "R41",
    "R41.0",
    "R41.1",
    "R41.2",
    "R41.3",
    "R41.8",
    "R42",
    "R43",
    "R43.0",
    "R43.1",
    "R43.2",
    "R43.8",
    "R44",
    "R44.0",
    "R44.1",
    "R44.2",
    "R44.3",
    "R44.8",
    "R45",
    "R45.0",
    "R45.1",
    "R45.2",
    "R45.3",
    "R45.4",
    "R45.5",
    "R45.6",
    "R45.7",
    "R45.8",
    "R46",
    "R46.0",
    "R46.1",
    "R46.2",
    "R46.3",
    "R46.4",
    "R46.5",
    "R46.6",
    "R46.7",
    "R46.8"
]);

//=============================================================================
// X
//=============================================================================

CODELIST.push({
    startcode: "X60",
    endcode: "X84",
    description: L("icd10_range_X"),
    range: true
});
for (i = 60; i <= 84; ++i) {
    processSelfHarm(i);
}

//=============================================================================
// Z
//=============================================================================

CODELIST.push({
    startcode: "Z00",
    endcode: "Z99",
    description: L("icd10_range_Z"),
    range: true
});
add_gc_array([
    "Z00.4",
    "Z03.2",
    "Z71.1"
]);

//=============================================================================
// Done
//=============================================================================

diagnosticcodelistfunc.preprocess(CODELIST);
module.exports = CODELIST;
