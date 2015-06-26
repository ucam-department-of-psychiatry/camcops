// idpolicy.js

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

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var storedvars = require('table/storedvars'),
    TK_LPAREN = 0,
    TK_RPAREN = 1,
    TK_AND    = 2,
    TK_OR     = 3,
    TK_FORENAME = 4,
    TK_SURNAME  = 5,
    TK_DOB      = 6,
    TK_SEX      = 7,
    TK_IDNUM1   = 8,
    TK_IDNUM2   = 9,
    TK_IDNUM3   = 10,
    TK_IDNUM4   = 11,
    TK_IDNUM5   = 12,
    TK_IDNUM6   = 13,
    TK_IDNUM7   = 14,
    TK_IDNUM8   = 15,
    POLICY_TOKEN_DICT = {
        "(": TK_LPAREN,
        ")": TK_RPAREN,
        "AND": TK_AND,
        "OR": TK_OR,

        "FORENAME": TK_FORENAME,
        "SURNAME": TK_SURNAME,
        "DOB": TK_DOB,
        "SEX": TK_SEX,
        "IDNUM1": TK_IDNUM1,
        "IDNUM2": TK_IDNUM2,
        "IDNUM3": TK_IDNUM3,
        "IDNUM4": TK_IDNUM4,
        "IDNUM5": TK_IDNUM5,
        "IDNUM6": TK_IDNUM6,
        "IDNUM7": TK_IDNUM7,
        "IDNUM8": TK_IDNUM8
    },
    TOKENIZE_RE = new RegExp( // tokenizer
        // http://stackoverflow.com/questions/6162600/
        '\\s*' +        // discard leading whitespace
            '(' +           // start capture group
                '\\w+' +        // words
            '|' +           // alternator
                '\\(' +        // left parenthesis
            '|' +           // alternator
                '\\)' +        // right parenthesis
            ')'           // end capture group
    ),
    ID_POLICY_UPLOAD_TOKENIZED = null,
    ID_POLICY_FINALIZE_TOKENIZED = null,
    id_policy_chunk, // FUNCTION declared here to avoid circularity
    TABLET_ID_POLICY_STRING = ("sex AND ( (forename AND surname AND dob) OR " +
                               "(idnum1 OR idnum2 OR idnum3 OR idnum4 OR " +
                               "idnum5 OR idnum6 OR idnum7 OR idnum8))");
    // ... clinical environment: forename/surname/dob/sex, and we can await an
    //     ID number later
    // ... research environment: sex and one ID number for pseudonymised
    //     applications

exports.TABLET_ID_POLICY_STRING = TABLET_ID_POLICY_STRING;

// grep(ary[,filt]) - filters an array
//   note: could use jQuery.grep() instead
// @param {Array}    ary    array of members to filter
// @param {Function} filt   function to test truthiness of member,
//   if omitted, "function(member){ if(member) return member; }" is assumed
// @returns {Array}  all members of ary where result of filter is truthy
function grep(arr, filter) {
    // Original was cryptic!
    var result = [],
        i,
        len,
        member;
    for (i = 0, len = arr.length; i < len; ++i) {
        member = arr[i] || '';
        if (filter && (typeof filter === 'function')) {
            if (filter(member)) {
                result.push(member);
            }
        } else {
            if (member) {
                result.push(member);
            }
        }
    }
    return result;
}

function getTokenizedIdPolicy(policy_string) {
    var token_string_list,
        tokenized_policy = [],
        i;
    if (!policy_string) {
        return null;
    }
    // Convert to upper case
    policy_string = policy_string.toUpperCase();
    // Split on spaces or parent
    token_string_list = grep(policy_string.split(TOKENIZE_RE));
    // Map to numerical tokens
    for (i = 0; i < token_string_list.length; ++i) {
        if (POLICY_TOKEN_DICT.hasOwnProperty(token_string_list[i])) {
            tokenized_policy.push(POLICY_TOKEN_DICT[token_string_list[i]]);
        } else {
            // Syntax error
            Titanium.API.warn("getTokenizedIdPolicy: syntax error in policy: "
                              + policy_string);
            return null;
        }
    }
    //Titanium.API.trace("getTokenizedIdPolicy: from " + policy_string + " to " +
    //                   JSON.stringify(tokenized_policy));
    return tokenized_policy;
}

function tokenizeUploadIdPolicy(policy_string) {
    ID_POLICY_UPLOAD_TOKENIZED = getTokenizedIdPolicy(policy_string);
}
exports.tokenizeUploadIdPolicy = tokenizeUploadIdPolicy;
tokenizeUploadIdPolicy(storedvars.idPolicyUpload.getValue());
// ... at first use of this module

function tokenizeFinalizeIdPolicy(policy_string) {
    ID_POLICY_FINALIZE_TOKENIZED = getTokenizedIdPolicy(policy_string);
}
exports.tokenizeFinalizeIdPolicy = tokenizeFinalizeIdPolicy;
tokenizeFinalizeIdPolicy(storedvars.idPolicyFinalize.getValue());
// ... at first use of this module

var ID_POLICY_TABLET_TOKENIZED = getTokenizedIdPolicy(TABLET_ID_POLICY_STRING);
// ... constant

function id_policy_op(policy, start) {
    if (start >= policy.length) {
        return { operator: null, index: start };
    }
    var token = policy[start];
    if (token === TK_AND || token === TK_OR) {
        return { operator: token, index: start + 1 };
    }
    // Not an operator
    return { operator: null, index: start };
}

function id_policy_element(patient, token) {
    //Titanium.API.trace("id_policy_element, token:" + token);
    if (token === TK_FORENAME) {
        return (patient.forename ? true : false);
    }
    if (token === TK_SURNAME) {
        return (patient.surname ? true : false);
    }
    if (token === TK_DOB) {
        return patient.dob !== undefined && patient.dob !== null;
    }
    if (token === TK_SEX) {
        return (patient.sex ? true : false);
    }
    if (token === TK_IDNUM1) {
        return patient.idnum1 !== undefined && patient.idnum1 !== null;
    }
    if (token === TK_IDNUM2) {
        return patient.idnum2 !== undefined && patient.idnum2 !== null;
    }
    if (token === TK_IDNUM3) {
        return patient.idnum3 !== undefined && patient.idnum3 !== null;
    }
    if (token === TK_IDNUM4) {
        return patient.idnum4 !== undefined && patient.idnum4 !== null;
    }
    if (token === TK_IDNUM5) {
        return patient.idnum5 !== undefined && patient.idnum5 !== null;
    }
    if (token === TK_IDNUM6) {
        return patient.idnum6 !== undefined && patient.idnum6 !== null;
    }
    if (token === TK_IDNUM7) {
        return patient.idnum7 !== undefined && patient.idnum7 !== null;
    }
    if (token === TK_IDNUM8) {
        return patient.idnum8 !== undefined && patient.idnum8 !== null;
    }
    return null;
}

function id_policy_content(patient, policy, start) {
    if (start >= policy.length) {
        return { nextchunk: null, index: start };
    }
    var token = policy[start],
        subchunkstart,
        subchunkend,
        depth,
        searchidx,
        chunk;
    if (token === TK_RPAREN || token === TK_AND || token === TK_OR) {
        // Chunks mustn't start with these; bad policy
        //Titanium.API.trace("id_policy_content: bad chunk start");
        return { nextchunk: null, index: start };
    }
    if (token === TK_LPAREN) {
        //Titanium.API.trace("id_policy_content: subchunk, recursing");
        subchunkstart = start + 1; // exclude the opening bracket
        // Find closing parenthesis
        depth = 1;
        searchidx = subchunkstart;
        while (depth > 0) {
            if (searchidx >= policy.length) {
                // unmatched left parenthesis; bad policy
                return { nextchunk: null, index: start };
            }
            if (policy[searchidx] === TK_LPAREN) {
                depth += 1;
            } else if (policy[searchidx] === TK_RPAREN) {
                depth -= 1;
            }
            searchidx += 1;
        }
        subchunkend = searchidx - 1;
        // ... to exclude the closing bracket from the analysed subchunk
        chunk = id_policy_chunk(patient,
                                policy.slice(subchunkstart,  subchunkend));
        return { nextchunk: chunk, index: subchunkend + 1 };
        // ... to move past the closing bracket
    }
    //Titanium.API.trace("id_policy_content: meaningful token");
    // meaningful token
    return {
        nextchunk: id_policy_element(patient, token),
        index: start + 1
    };
}

id_policy_chunk = function (patient, policy) {
    //Titanium.API.trace("id_policy_chunk: policy=" + policy +
    //                   ", patient=" + patient);
    var want_content = true,
        processing_and = false,
        processing_or = false,
        index = 0,
        value = null,
        result;
    while (index < policy.length) {
        if (want_content) {
            result = id_policy_content(patient, policy, index);
            // ... properties: nextchunk, index
            index = result.index;
            if (result.nextchunk === null) {
                return null; // fail
            }
            if (value === null) {
                value = result.nextchunk;
            } else if (processing_and) {
                value = value && result.nextchunk;
            } else if (processing_or) {
                value = value || result.nextchunk;
            } else {
                // Error; shouldn't get here
                Titanium.API.error("id_policy_chunk: problem, location 1");
                return null;
            }
            processing_and = false;
            processing_or = false;
        } else {
            // Want operator
            result = id_policy_op(policy, index);
            // ... properties: operator, index
            index = result.index;
            if (result.operator === null) {
                return null; // fail
            }
            if (result.operator === TK_AND) {
                processing_and = true;
            } else if (result.operator === TK_OR) {
                processing_or = true;
            } else {
                // Error; shouldn't get here
                Titanium.API.error("id_policy_chunk: problem, location 2");
                return null;
            }
        }
        want_content = !want_content;
    }
    if (value === null || want_content) {
        Titanium.API.warn("id_policy_chunk: returning null");
        return null;
    }
    //Titanium.API.trace("id_policy_chunk returning " + value);
    return value;
};

function satisfies_upload_id_policy(patient) {
    if (ID_POLICY_UPLOAD_TOKENIZED === null) {
        return false;
    }
    return id_policy_chunk(patient, ID_POLICY_UPLOAD_TOKENIZED);
}
exports.satisfies_upload_id_policy = satisfies_upload_id_policy;

function satisfies_finalize_id_policy(patient) {
    if (ID_POLICY_FINALIZE_TOKENIZED === null) {
        return false;
    }
    return id_policy_chunk(patient, ID_POLICY_FINALIZE_TOKENIZED);
}
exports.satisfies_finalize_id_policy = satisfies_finalize_id_policy;

function satisfies_tablet_id_policy(patient) {
    if (ID_POLICY_TABLET_TOKENIZED === null) {
        //Titanium.API.trace("satisfies_tablet_id_policy: no policy");
        return false;
    }
    return id_policy_chunk(patient, ID_POLICY_TABLET_TOKENIZED);
}
exports.satisfies_tablet_id_policy = satisfies_tablet_id_policy;
