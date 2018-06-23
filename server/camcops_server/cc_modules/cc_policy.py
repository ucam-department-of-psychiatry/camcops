#!/usr/bin/env python
# camcops_server/cc_modules/cc_policy.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

Note that the upload script should NOT attempt to verify patients
against the ID policy, not least because tablets are allowed to upload
task data (in a separate transaction) before uploading patients;
referential integrity would be very hard to police. So the tablet software
deals with ID compliance. (Also, the superuser can change the server's ID
policy retrospectively!)

"""

import io
import logging
import tokenize
from typing import List, Optional, Tuple, TYPE_CHECKING

from cardinal_pythonlib.logs import BraceStyleAdapter
from pendulum import Date

from .cc_simpleobjects import BarePatientInfo, IdNumReference
from .cc_unittest import ExtendedTestCase

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# TokenizedPolicy
# =============================================================================

TOKEN_TYPE = int
TOKENIZED_POLICY_TYPE = List[TOKEN_TYPE]

# http://stackoverflow.com/questions/36932
BAD_TOKEN = 0
TK_LPAREN = -1
TK_RPAREN = -2
TK_AND = -3
TK_OR = -4
TK_FORENAME = -5
TK_SURNAME = -6
TK_DOB = -7
TK_SEX = -8
TK_ANY_IDNUM = -9
# Tokens for ID numbers are from 1 upwards.

POLICY_TOKEN_DICT = {
    "(": TK_LPAREN,
    ")": TK_RPAREN,
    "AND": TK_AND,
    "OR": TK_OR,

    "FORENAME": TK_FORENAME,
    "SURNAME": TK_SURNAME,
    "DOB": TK_DOB,
    "SEX": TK_SEX,
    "ANYIDNUM": TK_ANY_IDNUM,
}

TOKEN_IDNUM_PREFIX = "IDNUM"


class TokenizedPolicy(object):
    def __init__(self, policy: str) -> None:
        self.tokens = self.get_tokenized_id_policy(policy)

    @staticmethod
    def name_to_token(name: str) -> int:
        if name in POLICY_TOKEN_DICT:
            return POLICY_TOKEN_DICT[name]
        if name.startswith(TOKEN_IDNUM_PREFIX):
            nstr = name[len(TOKEN_IDNUM_PREFIX):]
            try:
                return int(nstr)
            except (TypeError, ValueError):
                return BAD_TOKEN
        return BAD_TOKEN

    @classmethod
    def get_tokenized_id_policy(cls, policy: str) \
            -> TOKENIZED_POLICY_TYPE:
        """
        Takes a string policy and returns a tokenized policy, or [].
        """
        if policy is None:
            return []
        # http://stackoverflow.com/questions/88613
        string_index = 1
        try:
            tokenstrings = list(
                token[string_index]
                for token in tokenize.generate_tokens(
                    io.StringIO(policy.upper()).readline)
                if token[string_index]
            )
        except tokenize.TokenError:
            # something went wrong
            return []
        tokens = [cls.name_to_token(k) for k in tokenstrings]
        if any(t == BAD_TOKEN for t in tokens):
            # There's something bad in there.
            return []
        return tokens

    def is_syntactically_valid(self) -> bool:
        return bool(self.tokens)

    def is_valid_from_req(self, req: "CamcopsRequest") -> bool:
        return self.is_valid(req.valid_which_idnums)

    def is_valid(self, valid_idnums: List[int]) -> bool:
        # First, syntax:
        if not self.is_syntactically_valid():
            return False
        # Second, all ID numbers referred to by the policy exist:
        for token in self.tokens:
            if token > 0 and token not in valid_idnums:
                return False
        return True

    def find_critical_single_numerical_id_from_req(
            self, req: "CamcopsRequest") -> Optional[int]:
        return self.find_critical_single_numerical_id(req.valid_which_idnums)

    def find_critical_single_numerical_id(
            self,
            valid_which_idnums: List[int]) -> Optional[int]:
        """
        If the policy involves a single mandatory ID number, return that ID
        number; otherwise return None.
        """
        # This method is a bit silly, but it should work.
        if not self.tokens:
            return None
        successes = 0
        critical_idnum = None
        for n in valid_which_idnums:
            dummyptinfo = BarePatientInfo(
                forename="X",
                surname="X",
                dob=Date.today(),  # random value
                sex="X",
                idnum_definitions=[IdNumReference(which_idnum=n,
                                                  idnum_value=1)]
            )
            # Set the idnum of interest
            if self.satisfies_id_policy(dummyptinfo):
                successes += 1
                critical_idnum = n
        if successes == 1:
            return critical_idnum
        else:
            return None
            # e.g. if no ID numbers are required, or if more than
            # one ID number satisfies the requirement.

    def is_idnum_mandatory_in_policy(
            self,
            which_idnum: int,
            valid_which_idnums: List[int]) -> bool:
        """
        Is the ID number mandatory in the specified policy?
        """
        if which_idnum is None or which_idnum < 1:
            return False
        # A hacky way...
        dummyptinfo = BarePatientInfo(
            forename="X",
            surname="X",
            dob=Date.today(),  # random value
            sex="X",
            idnum_definitions=[
                IdNumReference(which_idnum=n, idnum_value=1)
                for n in valid_which_idnums
                if n != which_idnum
            ]
        )
        # ... so now everything but the idnum in question is set
        if self.satisfies_id_policy(dummyptinfo):
            return False  # because that means it wasn't mandatory
        return True

    def satisfies_id_policy(self, ptinfo: BarePatientInfo) -> bool:
        """
        Does the patient information in ptinfo satisfy the specified ID policy?
        """
        return bool(self.id_policy_chunk(self.tokens, ptinfo))
        # ... which is recursive

    @classmethod
    def id_policy_chunk(cls,
                        policy: TOKENIZED_POLICY_TYPE,
                        ptinfo: BarePatientInfo) -> Optional[bool]:
        """
        Applies the policy to the patient info in ptinfo.
        Can be used recursively.

        Args:
            policy: a tokenized policy
            ptinfo: an instance of BarePatientInfo
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
                (nextchunk, index) = cls.id_policy_content(policy, ptinfo,
                                                           index)
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
                (operator, index) = cls.id_policy_op(policy, index)
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

    @classmethod
    def id_policy_content(cls,
                          policy: TOKENIZED_POLICY_TYPE,
                          ptinfo: BarePatientInfo,
                          start: int) -> Tuple[Optional[bool], int]:
        """
        Applies part of a policy to ptinfo. Called by id_policy_chunk (q.v.).
        """
        if start >= len(policy):
            return None, start
        token = policy[start]
        if token in [TK_RPAREN, TK_AND, TK_OR]:
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
            chunk = cls.id_policy_chunk(policy[subchunkstart:subchunkend],
                                        ptinfo)
            return chunk, subchunkend + 1  # to move past the closing bracket
        else:
            # meaningful token
            return cls.id_policy_element(ptinfo, token), start + 1

    @classmethod
    def id_policy_op(cls, policy: TOKENIZED_POLICY_TYPE, start: int) \
            -> Tuple[Optional[TOKEN_TYPE], int]:
        """Returns an operator from the policy, or None."""
        if start >= len(policy):
            return None, start
        token = policy[start]
        if token in [TK_AND, TK_OR]:
            return token, start + 1
        else:
            # Not an operator
            return None, start

    @classmethod
    def id_policy_element(cls, ptinfo: BarePatientInfo, token: TOKEN_TYPE) \
            -> Optional[bool]:
        """
        Returns a Boolean corresponding to whether the token's information is
        present in the ptinfo.
        """
        if token == TK_FORENAME:
            return ptinfo.forename is not None
        if token == TK_SURNAME:
            return ptinfo.surname is not None
        if token == TK_DOB:
            return ptinfo.dob is not None
        if token == TK_SEX:
            return ptinfo.sex is not None
        if token == TK_ANY_IDNUM:
            for idnumdef in ptinfo.idnum_definitions:
                if idnumdef.idnum_value is not None:
                    return True
            return False
        if token > 0:  # ID token
            for iddef in ptinfo.idnum_definitions:
                if (iddef.which_idnum == token and
                        iddef.idnum_value is not None):
                    return True
            return False
        return None


# =============================================================================
# Unit tests
# =============================================================================

class PolicyTests(ExtendedTestCase):
    def test_policies(self) -> None:
        self.announce("test_policies")

        empty = ""
        bad1 = "sex AND (failure"
        good1 = "sex AND idnum1"
        test_idnums = [
            None,
            -1,
            1
        ]
        valid_which_idnums = [1, 2, 3]
        bpi = BarePatientInfo(
            forename="forename",
            surname="surname",
            dob=Date.today(),  # random value
            sex="sex",
            idnum_definitions=[
                IdNumReference(1, 1),
                IdNumReference(10, 3),
            ],
        )
        for policy_string in [empty, bad1, good1]:
            p = TokenizedPolicy(policy_string)
            self.assertIsInstance(p.is_syntactically_valid(), bool)
            self.assertIsInstance(p.is_valid(valid_idnums=valid_which_idnums),
                                  bool)
            self.assertIsInstanceOrNone(p.find_critical_single_numerical_id(
                valid_which_idnums=valid_which_idnums), int)

            for which_idnum in test_idnums:
                self.assertIsInstance(p.is_idnum_mandatory_in_policy(
                    which_idnum=which_idnum,
                    valid_which_idnums=valid_which_idnums), bool)
            self.assertIsInstance(p.satisfies_id_policy(bpi), bool)

            if policy_string == good1:
                self.assertEqual(p.find_critical_single_numerical_id(
                    valid_which_idnums=valid_which_idnums), 1)
