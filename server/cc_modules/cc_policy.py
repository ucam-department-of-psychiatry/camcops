#!/usr/bin/env python3
# cc_policy.py

"""
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
"""

import io
import tokenize

from .cc_constants import NUMBER_OF_IDNUMS
# from cc_logger import log
from . import cc_namedtuples
from .cc_unittest import unit_test_ignore

# =============================================================================
# Constants
# =============================================================================

# http://stackoverflow.com/questions/36932
TK_LPAREN = 0
TK_RPAREN = 1
TK_AND = 2
TK_OR = 3
TK_FORENAME = 4
TK_SURNAME = 5
TK_DOB = 6
TK_SEX = 7
TK_IDNUM_BASE = 8  # avoid subsequent numbers

POLICY_TOKEN_DICT = {
    "(": TK_LPAREN,
    ")": TK_RPAREN,
    "AND": TK_AND,
    "OR": TK_OR,

    "FORENAME": TK_FORENAME,
    "SURNAME": TK_SURNAME,
    "DOB": TK_DOB,
    "SEX": TK_SEX
}
for n in range(1, NUMBER_OF_IDNUMS + 1):
    POLICY_TOKEN_DICT["IDNUM" + str(n)] = TK_IDNUM_BASE + n

ID_POLICY_UPLOAD_TOKENIZED = None
ID_POLICY_FINALIZE_TOKENIZED = None
UPLOAD_POLICY_PRINCIPAL_NUMERIC_ID = None
FINALIZE_POLICY_PRINCIPAL_NUMERIC_ID = None

# Note that the Perl upload script should NOT attempt to verify patients
# against the ID policy, not least because tablets are allowed to upload
# task data (in a separate transaction) before uploading patients;
# referential integrity would be very hard to police. So the tablet software
# deals with ID compliance. (Also, the user can change the server's ID policy
# retrospectively!)


# =============================================================================
# Patient ID policy functions: specific
# =============================================================================

def tokenize_upload_id_policy(policy):
    """Takes a policy, as a string, and writes it in tokenized format to the
    internal uploading policy."""
    global ID_POLICY_UPLOAD_TOKENIZED
    global UPLOAD_POLICY_PRINCIPAL_NUMERIC_ID
    ID_POLICY_UPLOAD_TOKENIZED = get_tokenized_id_policy(policy)
    dummyptinfo = cc_namedtuples.BarePatientInfo(
        forename=None,
        surname=None,
        dob=None,
        sex=None,
        idnum_array=[None] * NUMBER_OF_IDNUMS
    )
    if satisfies_upload_id_policy(dummyptinfo) is None:
        # Implies syntax error - True/False would mean success
        ID_POLICY_UPLOAD_TOKENIZED = None
        UPLOAD_POLICY_PRINCIPAL_NUMERIC_ID = None
    else:
        UPLOAD_POLICY_PRINCIPAL_NUMERIC_ID = \
            find_critical_single_numerical_id(ID_POLICY_UPLOAD_TOKENIZED)


def tokenize_finalize_id_policy(policy):
    """Takes a policy, as a string, and writes it in tokenized format to the
    internal finalizing policy."""
    global ID_POLICY_FINALIZE_TOKENIZED
    global FINALIZE_POLICY_PRINCIPAL_NUMERIC_ID
    ID_POLICY_FINALIZE_TOKENIZED = get_tokenized_id_policy(policy)
    dummyptinfo = cc_namedtuples.BarePatientInfo(
        forename=None,
        surname=None,
        dob=None,
        sex=None,
        idnum_array=[None] * NUMBER_OF_IDNUMS
    )
    if satisfies_upload_id_policy(dummyptinfo) is None:
        # Implies syntax error - True/False would mean success
        ID_POLICY_FINALIZE_TOKENIZED = None
        FINALIZE_POLICY_PRINCIPAL_NUMERIC_ID = None
    else:
        FINALIZE_POLICY_PRINCIPAL_NUMERIC_ID = \
            find_critical_single_numerical_id(ID_POLICY_FINALIZE_TOKENIZED)


def is_idnum_mandatory_in_upload_policy(idnum):
    """Is the ID number mandatory in the upload policy?"""
    return is_idnum_mandatory_in_policy(
        idnum,
        ID_POLICY_UPLOAD_TOKENIZED
    )


def is_idnum_mandatory_in_finalize_policy(idnum):
    """Is the ID number mandatory in the finalizing policy?"""
    return is_idnum_mandatory_in_policy(
        idnum,
        ID_POLICY_FINALIZE_TOKENIZED
    )


def upload_id_policy_valid():
    """Is the tokenized upload ID policy valid?"""
    return ID_POLICY_UPLOAD_TOKENIZED is not None


def finalize_id_policy_valid():
    """Is the tokenized finalizing ID policy valid?"""
    return ID_POLICY_FINALIZE_TOKENIZED is not None


def id_policies_valid():
    """Are all ID policies tokenized and valid?"""
    return upload_id_policy_valid() and finalize_id_policy_valid()


def get_upload_id_policy_principal_numeric_id():
    """Returns the single critical ID number in the upload policy, or None."""
    return UPLOAD_POLICY_PRINCIPAL_NUMERIC_ID


def get_finalize_id_policy_principal_numeric_id():
    """Returns the single critical ID number in the finalizing policy, or
    None."""
    return FINALIZE_POLICY_PRINCIPAL_NUMERIC_ID


def satisfies_upload_id_policy(ptinfo):
    """Does the patient information in ptinfo satisfy the upload ID policy?

    ptinfo is an instance of cc_namedtuples.BarePatientInfo
    """
    if ID_POLICY_UPLOAD_TOKENIZED is None:
        return False
    return satisfies_id_policy(ID_POLICY_UPLOAD_TOKENIZED, ptinfo)


def satisfies_finalize_id_policy(ptinfo):
    """Does the patient information in ptinfo satisfy the finalizing ID policy?

    ptinfo is an instance of cc_namedtuples.BarePatientInfo
    """
    if ID_POLICY_FINALIZE_TOKENIZED is None:
        return False
    return satisfies_id_policy(ID_POLICY_FINALIZE_TOKENIZED, ptinfo)


# =============================================================================
# Patient ID policy functions: generic
# =============================================================================

def get_tokenized_id_policy(policy):
    """Takes a string policy and returns a tokenized policy, or None."""
    if policy is None:
        return None
    # http://stackoverflow.com/questions/88613
    STRING = 1
    try:
        tokenstrings = list(
            token[STRING]
            for token in tokenize.generate_tokens(
                io.StringIO(policy.upper()).readline)
            if token[STRING]
        )
    except tokenize.TokenError:
        # something went wrong
        return None
    if not all(k in POLICY_TOKEN_DICT for k in tokenstrings):
        # There's something bad in there.
        return None
    return [POLICY_TOKEN_DICT[k] for k in tokenstrings]


def find_critical_single_numerical_id(tokenized_policy):
    """If the policy involves a single mandatory ID number, return that ID
    number; otherwise return None."""
    # This method is a bit silly, but it should work.
    if tokenized_policy is None:
        return None
    successes = 0
    critical_idnum = None
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        dummyptinfo = cc_namedtuples.BarePatientInfo(
            forename="X",
            surname="X",
            dob="X",  # good enough for id_policy_element()
            sex="X",
            idnum_array=[None] * NUMBER_OF_IDNUMS
        )
        # Set the idnum of interest
        dummyptinfo.idnum_array[n - 1] = 1
        if satisfies_id_policy(tokenized_policy, dummyptinfo):
            successes += 1
            critical_idnum = n
    if successes == 1:
        return critical_idnum
    else:
        return None
        # e.g. if no ID numbers are required, or if more than
        # one ID number satisfies the requirement.


def is_idnum_mandatory_in_policy(idnum, tokenized_policy):
    """Is the ID number mandatory in the specified policy?"""
    if idnum is None or idnum < 1 or idnum > NUMBER_OF_IDNUMS:
        return False
    # A hacky way...
    dummyptinfo = cc_namedtuples.BarePatientInfo(
        forename="X",
        surname="X",
        dob="X",  # good enough for id_policy_element()
        sex="X",
        idnum_array=[1] * NUMBER_OF_IDNUMS
    )
    # Blank the idnum of interest
    dummyptinfo.idnum_array[idnum - 1] = None
    # ... so now everything but the idnum in question is set
    if satisfies_id_policy(tokenized_policy, dummyptinfo):
        return False  # because that means it wasn't mandatory
    return True


def satisfies_id_policy(policy, ptinfo):
    """Does the patient information in ptinfo satisfy the specified ID policy?

    ptinfo is an instance of cc_namedtuples.BarePatientInfo
    """
    return id_policy_chunk(policy, ptinfo)
    # ... which is recursive


def id_policy_chunk(policy, ptinfo):
    """Applies the policy to the patient info in ptinfo.

    Args:
        policy: a tokenized policy
        ptinfo: an instance of cc_namedtuples.BarePatientInfo
    """
    want_content = True
    processing_and = False
    processing_or = False
    index = 0
    value = None
    while index < len(policy):
        # log.debug("index:" + str(index) + ", want_content:"
        #              + str(want_content) + ", policy:" + str(policy))
        if want_content:
            (nextchunk, index) = id_policy_content(policy, ptinfo, index)
            # log.debug("nextchunk:" + str(nextchunk))
            if nextchunk is None:
                return None  # fail
            if value is None:
                value = nextchunk
            elif processing_and:
                value = value and nextchunk
            elif processing_or:
                value = value or nextchunk
            else:
                # Error; shouldn't get here
                return None
            processing_and = False
            processing_or = False
        else:
            # Want operator
            (operator, index) = id_policy_op(policy, index)
            # log.debug("operator:" + str(operator))
            if operator is None:
                return None  # fail
            if operator == TK_AND:
                processing_and = True
            elif operator == TK_OR:
                processing_or = True
            else:
                # Error; shouldn't get here
                return None
        want_content = not want_content
    if value is None or want_content:
        # log.debug("id_policy_chunk returning None")
        return None
    # log.debug("id_policy_chunk returning " + str(value))
    return value


def id_policy_content(policy, ptinfo, start):
    """Applies part of a policy to ptinfo. Called by id_policy_chunk (q.v.)."""
    if start >= len(policy):
        return None, start
    token = policy[start]
    if token == TK_RPAREN or token == TK_AND or token == TK_OR:
        # Chunks mustn't start with these; bad policy
        return None, start
    elif token == TK_LPAREN:
        subchunkstart = start + 1  # exclude the opening bracket
        # Find closing parenthesis
        depth = 1
        searchidx = subchunkstart
        while depth > 0:
            if searchidx >= len(policy):
                # unmatched left parenthesis; bad policy
                return None, start
            elif policy[searchidx] == TK_LPAREN:
                depth += 1
            elif policy[searchidx] == TK_RPAREN:
                depth -= 1
            searchidx += 1
        subchunkend = searchidx - 1
        # ... to exclude the closing bracket from the analysed subchunk
        chunk = id_policy_chunk(policy[subchunkstart:subchunkend], ptinfo)
        return chunk, subchunkend + 1  # to move past the closing bracket
    else:
        # meaningful token
        return id_policy_element(ptinfo, token), start + 1


def id_policy_op(policy, start):
    """Returns an operator from the policy, or None."""
    if start >= len(policy):
        return None, start
    token = policy[start]
    if token == TK_AND or token == TK_OR:
        return token, start + 1
    else:
        # Not an operator
        return None, start


def id_policy_element(ptinfo, token):
    """Returns a Boolean corresponding to whether the token's information is
    present in the ptinfo."""
    if token == TK_FORENAME:
        return ptinfo.forename is not None
    if token == TK_SURNAME:
        return ptinfo.surname is not None
    if token == TK_DOB:
        return ptinfo.dob is not None
    if token == TK_SEX:
        return ptinfo.sex is not None
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        i = n - 1
        if token == TK_IDNUM_BASE + n:
            return ptinfo.idnum_array[i] is not None
    return None


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests():
    """Unit tests for cc_policy module."""
    test_policies = [
        "",
        "sex AND (failure",
        "sex AND idnum1",
    ]
    test_idnums = [
        None,
        -1,
        1
    ]
    bpi = cc_namedtuples.BarePatientInfo(
        forename="forename",
        surname="surname",
        dob="dob",
        sex="sex",
        idnum_array=[5] * NUMBER_OF_IDNUMS,
    )
    for p in test_policies:
        unit_test_ignore("", tokenize_upload_id_policy, p)
        unit_test_ignore("", tokenize_finalize_id_policy, p)
        unit_test_ignore("", get_tokenized_id_policy, p)
    unit_test_ignore("", find_critical_single_numerical_id,
                     ID_POLICY_UPLOAD_TOKENIZED)
    for i in test_idnums:
        unit_test_ignore("", is_idnum_mandatory_in_upload_policy, i)
        unit_test_ignore("", is_idnum_mandatory_in_finalize_policy, i)
        unit_test_ignore("", is_idnum_mandatory_in_policy, i,
                         ID_POLICY_UPLOAD_TOKENIZED)
    unit_test_ignore("", upload_id_policy_valid)
    unit_test_ignore("", finalize_id_policy_valid)
    unit_test_ignore("", get_upload_id_policy_principal_numeric_id)
    unit_test_ignore("", get_finalize_id_policy_principal_numeric_id)
    unit_test_ignore("", satisfies_upload_id_policy, bpi)
    unit_test_ignore("", satisfies_finalize_id_policy, bpi)
    unit_test_ignore("", satisfies_id_policy, bpi,
                     ID_POLICY_UPLOAD_TOKENIZED)

    # id_policy_chunk tested implicitly
    # id_policy_content tested implicitly
    # id_policy_op tested implicitly
    # id_policy_element tested implicitly
