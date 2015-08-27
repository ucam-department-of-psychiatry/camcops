// CODES_ICD9CM.js

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
// Preamble (code-processing functions)
//=============================================================================

var diagnosticcodelistfunc = require('lib/diagnosticcodelistfunc'),
    ICD9CMPREFIX = "icd9cm_",
    CODELIST = [];

function gc(code) {
    // generic ICD-9-CM code
    return { code: code, description: L(ICD9CMPREFIX + code) };
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

function processSchizophrenia(code) {
    var sztype = L(ICD9CMPREFIX + code),
        i;
    add_cd(code, sztype);
    for (i = 0; i <= 5; ++i) {
        add_cd(code + i, sztype + ", " + L("icd9cm_schizophrenia_" + i));
    }
}

function processEpisodicAffective(code) {
    var affectivedisorder = L(ICD9CMPREFIX + code),
        i;
    add_cd(code, affectivedisorder);
    for (i = 0; i <= 6; ++i) {
        add_cd(code + i,
               affectivedisorder + ", " + L("icd9cm_affective_" + i));
    }
}

function processSubstanceSub(code, substance_root) {
    // deliberately separate from processSubstance(); may be called separately
    var i;
    for (i = 0; i <= 3; ++i) {
        add_cd(code + i,
               substance_root + ", " + L("icd9cm_substance_" + i));
    }
}

function processSubstance(code) {
    var substance = L(ICD9CMPREFIX + code);
    add_cd(code, substance);
    processSubstanceSub(code, substance);
}

//=============================================================================
// Codes
//=============================================================================

CODELIST.push({
    startcode: "290",
    endcode: "294",
    description: L("icd9cm_range_290_294"),
    range: true
});
add_gc_array([
    "290",
    "290.0",
    "290.1",
    "290.10",
    "290.11",
    "290.12",
    "290.13",
    "290.2",
    "290.20",
    "290.21",
    "290.3",
    "290.4",
    "290.40",
    "290.41",
    "290.42",
    "290.43",
    "290.8",
    "290.9",
    "291",
    "291.0",
    "291.1",
    "291.2",
    "291.3",
    "291.4",
    "291.5",
    "291.8",
    "291.81",
    "291.82",
    "291.89",
    "291.9",
    "292",
    "292.0",
    "292.1",
    "292.11",
    "292.12",
    "292.2",
    "292.8",
    "292.81",
    "292.82",
    "292.83",
    "292.84",
    "292.85",
    "292.89",
    "292.9",
    "293",
    "293.0",
    "293.1",
    "293.8",
    "293.81",
    "293.82",
    "293.83",
    "293.84",
    "293.89",
    "293.9",
    "294",
    "294.0",
    "294.1",
    "294.10",
    "294.11",
    "294.2",
    "294.20",
    "294.21",
    "294.8",
    "294.9"
]);

CODELIST.push({
    startcode: "295",
    endcode: "299",
    description: L("icd9cm_range_295_299"),
    range: true
});

add_gc("295");
processSchizophrenia("295.0");
processSchizophrenia("295.1");
processSchizophrenia("295.2");
processSchizophrenia("295.3");
processSchizophrenia("295.4");
processSchizophrenia("295.5");
processSchizophrenia("295.6");
processSchizophrenia("295.7");
processSchizophrenia("295.8");
processSchizophrenia("295.9");

add_gc("296");
processEpisodicAffective("296.0");
processEpisodicAffective("296.1");
processEpisodicAffective("296.2");
processEpisodicAffective("296.3");
processEpisodicAffective("296.4");
processEpisodicAffective("296.5");
processEpisodicAffective("296.6");

add_gc_array([
    "296.7",
    "296.8",
    "296.80",
    "296.81",
    "296.82",
    "296.89",
    "296.9",
    "296.90",
    "296.99",
    "297",
    "297.0",
    "297.1",
    "297.2",
    "297.3",
    "297.8",
    "297.9",
    "298",
    "298.0",
    "298.1",
    "298.2",
    "298.3",
    "298.4",
    "298.8",
    "298.9",
    "299",
    "299.0",
    "299.00",
    "299.01",
    "299.1",
    "299.10",
    "299.11",
    "299.8",
    "299.80",
    "299.81",
    "299.9",
    "299.90",
    "299.91"
]);

CODELIST.push({
    startcode: "300",
    endcode: "316",
    description: L("icd9cm_range_300_316"),
    range: true
});

add_gc_array([
    "300",
    "300.0",
    "300.00",
    "300.01",
    "300.02",
    "300.09",
    "300.1",
    "300.10",
    "300.11",
    "300.12",
    "300.13",
    "300.14",
    "300.15",
    "300.16",
    "300.19",
    "300.2",
    "300.20",
    "300.21",
    "300.22",
    "300.23",
    "300.29",
    "300.3",
    "300.4",
    "300.5",
    "300.6",
    "300.7",
    "300.8",
    "300.81",
    "300.82",
    "300.89",
    "300.9",
    "301",
    "301.0",
    "301.1",
    "301.10",
    "301.11",
    "301.12",
    "301.13",
    "301.2",
    "301.20",
    "301.21",
    "301.22",
    "301.3",
    "301.4",
    "301.5",
    "301.50",
    "301.51",
    "301.59",
    "301.6",
    "301.7",
    "301.8",
    "301.81",
    "301.82",
    "301.83",
    "301.84",
    "301.89",
    "301.9",
    "302",
    "302.0",
    "302.1",
    "302.2",
    "302.3",
    "302.4",
    "302.5",
    "302.50",
    "302.51",
    "302.52",
    "302.53",
    "302.6",
    "302.7",
    "302.70",
    "302.71",
    "302.72",
    "302.73",
    "302.74",
    "302.75",
    "302.76",
    "302.79",
    "302.8",
    "302.81",
    "302.82",
    "302.83",
    "302.84",
    "302.85",
    "302.89",
    "302.9",
    "303"
]);

add_gc("303.0");
processSubstanceSub("303.0", L("icd9cm_303.0x")); // heading is different

processSubstance("303.9");

add_gc("304");
processSubstance("304.0");
processSubstance("304.1");
processSubstance("304.2");
processSubstance("304.3");
processSubstance("304.4");
processSubstance("304.5");
processSubstance("304.6");
processSubstance("304.7");
processSubstance("304.8");
processSubstance("304.9");

add_gc("305");
// Special: all differ from their higher-level headings
add_gc("305.0");
processSubstanceSub("305.0", L(ICD9CMPREFIX + "305.0x"));
add_gc("305.1");
add_gc("305.2");
processSubstanceSub("305.2", L(ICD9CMPREFIX + "305.2x"));
add_gc("305.3");
processSubstanceSub("305.3", L(ICD9CMPREFIX + "305.3x"));
add_gc("305.4");
processSubstanceSub("305.4", L(ICD9CMPREFIX + "305.4x"));
add_gc("305.5");
processSubstanceSub("305.5", L(ICD9CMPREFIX + "305.5x"));
add_gc("305.6");
processSubstanceSub("305.6", L(ICD9CMPREFIX + "305.6x"));
add_gc("305.7");
processSubstanceSub("305.7", L(ICD9CMPREFIX + "305.7x"));
add_gc("305.8");
processSubstanceSub("305.8", L(ICD9CMPREFIX + "305.8x"));
add_gc("305.9");
processSubstanceSub("305.9", L(ICD9CMPREFIX + "305.9x"));

add_gc_array([
    "306",
    "306.0",
    "306.1",
    "306.2",
    "306.3",
    "306.4",
    "306.50",
    "306.51",
    "306.52",
    "306.53",
    "306.59",
    "306.6",
    "306.7",
    "306.8",
    "306.9",
    "307",
    "307.0",
    "307.1",
    "307.2",
    "307.20",
    "307.21",
    "307.22",
    "307.23",
    "307.3",
    "307.4",
    "307.40",
    "307.41",
    "307.42",
    "307.43",
    "307.44",
    "307.45",
    "307.46",
    "307.47",
    "307.48",
    "307.49",
    "307.5",
    "307.50",
    "307.51",
    "307.52",
    "307.53",
    "307.54",
    "307.59",
    "307.6",
    "307.7",
    "307.8",
    "307.80",
    "307.81",
    "307.89",
    "307.9",
    "308",
    "308.0",
    "308.1",
    "308.2",
    "308.3",
    "308.4",
    "308.9",
    "309",
    "309.0",
    "309.1",
    "309.2",
    "309.21",
    "309.22",
    "309.23",
    "309.24",
    "309.28",
    "309.29",
    "309.3",
    "309.4",
    "309.8",
    "309.81",
    "309.82",
    "309.83",
    "309.89",
    "309.9",
    "310",
    "310.0",
    "310.1",
    "310.2",
    "310.8",
    "310.81",
    "310.89",
    "310.9",
    "311",
    "312",
    "312.0",
    "312.00",
    "312.01",
    "312.02",
    "312.03",
    "312.1",
    "312.10",
    "312.11",
    "312.12",
    "312.13",
    "312.2",
    "312.20",
    "312.21",
    "312.22",
    "312.23",
    "312.3",
    "312.30",
    "312.31",
    "312.32",
    "312.33",
    "312.34",
    "312.35",
    "312.39",
    "312.4",
    "312.8",
    "312.81",
    "312.82",
    "312.89",
    "312.9",
    "313",
    "313.0",
    "313.1",
    "313.2",
    "313.21",
    "313.22",
    "313.23",
    "313.3",
    "313.8",
    "313.81",
    "313.82",
    "313.83",
    "313.89",
    "313.9",
    "314",
    "314.0",
    "314.00",
    "314.01",
    "314.1",
    "314.2",
    "314.8",
    "314.9",
    "315",
    "315.0",
    "315.00",
    "315.01",
    "315.02",
    "315.09",
    "315.1",
    "315.2",
    "315.3",
    "315.31",
    "315.32",
    "315.34",
    "315.35",
    "315.39",
    "315.4",
    "315.5",
    "315.8",
    "315.9",
    "316"
]);

CODELIST.push({
    startcode: "317",
    endcode: "319",
    description: L("icd9cm_range_317_319"),
    range: true
});
add_gc_array([
    "317",
    "318",
    "318.0",
    "318.1",
    "318.2",
    "319"
]);

CODELIST.push({
    startcode: "V71",
    endcode: "V82",
    description: L("icd9cm_range_V71_V82"),
    range: true
});
add_gc("V71.09");

//=============================================================================
// Done
//=============================================================================

diagnosticcodelistfunc.preprocess(CODELIST);
module.exports = CODELIST;
