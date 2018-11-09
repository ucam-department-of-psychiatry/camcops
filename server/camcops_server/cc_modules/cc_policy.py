#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_policy.py

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

**Represents ID number policies.**

Note that the upload script should NOT attempt to verify patients against the
ID policy, not least because tablets are allowed to upload task data (in a
separate transaction) before uploading patients; referential integrity would be
very hard to police. So the tablet software deals with ID compliance. (Also,
the superuser can change the server's ID policy retrospectively!)

Both the client and the server do policy tokenizing and can check patient info
against policies. The server has additional code to answer questions like "is
this policy valid?" (in general and in the context of the server's
configuration).

"""

import io
from itertools import combinations, product
import logging
import tokenize
from typing import (Generator, Iterable, List, Optional, Sequence, Tuple,
                    TYPE_CHECKING)
import unittest

from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from pendulum import Date

from camcops_server.cc_modules.cc_simpleobjects import (
    BarePatientInfo,
    IdNumReference,
)
from camcops_server.cc_modules.cc_unittest import ExtendedTestCase

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Tokens
# =============================================================================

TOKEN_TYPE = int
TOKENIZED_POLICY_TYPE = List[TOKEN_TYPE]

# http://stackoverflow.com/questions/36932
BAD_TOKEN = 0
TK_LPAREN = -1
TK_RPAREN = -2
TK_AND = -3
TK_OR = -4
TK_NOT = -5
TK_ANY_IDNUM = -6
TK_OTHER_IDNUM = -7
TK_FORENAME = -8
TK_SURNAME = -9
TK_SEX = -10
TK_DOB = -11
TK_ADDRESS = -12
TK_GP = -13
TK_OTHER_DETAILS = -14

# Tokens for ID numbers are from 1 upwards.

POLICY_TOKEN_DICT = {
    "(": TK_LPAREN,
    ")": TK_RPAREN,
    "AND": TK_AND,
    "OR": TK_OR,
    "NOT": TK_NOT,

    "ANYIDNUM": TK_ANY_IDNUM,
    "OTHERIDNUM": TK_OTHER_IDNUM,

    "FORENAME": TK_FORENAME,
    "SURNAME": TK_SURNAME,
    "SEX": TK_SEX,
    "DOB": TK_DOB,
    "ADDRESS": TK_ADDRESS,
    "GP": TK_GP,
    "OTHERDETAILS": TK_OTHER_DETAILS,
}

TOKEN_IDNUM_PREFIX = "IDNUM"


# =============================================================================
# Helper functions for testing policies
# =============================================================================

def gen_test_bpis(which_idnums_present_options: Iterable[Iterable[int]],
                  forename_present_options: Iterable[bool] = None,
                  surname_present_options: Iterable[bool] = None,
                  sex_present_options: Iterable[bool] = None,
                  dob_present_options: Iterable[bool] = None,
                  address_present_options: Iterable[bool] = None,
                  gp_present_options: Iterable[bool] = None,
                  otherdetails_present_options: Iterable[bool] = None) \
        -> Generator[BarePatientInfo, None, None]:
    """
    Generates test `camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo`
    objects.

    Args:
        which_idnums_present_options:
            list of options, where each option is a list of ID number types
            that should be present
        forename_present_options:
            options for "forename" present, e.g. ``[True]``, ``[True, False]``;
            if ``None`` is passed, the default of ``[True, False]`` is used
        surname_present_options:
            as for forename_present_options
        sex_present_options:
            as for forename_present_options
        dob_present_options:
            as for forename_present_options
        address_present_options:
            as for forename_present_options
        gp_present_options:
            as for forename_present_options
        otherdetails_present_options:
            as for forename_present_options

    Yields:
        `camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo` objects,
        for all combinations of the options requested
    """
    def strval(present: bool) -> str:
        return "X" if present else ""

    def dateval(present: bool) -> Optional[Date]:
        return Date.today() if present else None

    default = [True, False]  # "most likely to be happy" first

    forename_present_options = map(strval, forename_present_options or default)
    surname_present_options = map(strval, surname_present_options or default)
    sex_present_options = map(strval, sex_present_options or default)
    # Sex must ALWAYS be present; it's required by the tablet.
    # However, we may want to generate invalid things to test here.
    dob_present_options = map(dateval, dob_present_options or default)
    address_present_options = map(strval, address_present_options or default)
    gp_present_options = map(strval, gp_present_options or default)
    otherdetails_present_options = map(strval,
                                       otherdetails_present_options or default)

    # Most to least plausible, so ID numbers last in loop and "present" before
    # "absent" in default.
    # https://docs.python.org/3/library/itertools.html#itertools.product
    for forename, surname, sex, dob, address, gp, other, which_ids in product(
                forename_present_options,
                surname_present_options,
                sex_present_options,
                dob_present_options,
                address_present_options,
                gp_present_options,
                otherdetails_present_options,
                which_idnums_present_options,
            ):
        bpi = BarePatientInfo(
            forename=forename,
            surname=surname,
            sex=sex,
            dob=dob,
            address=address,
            gp=gp,
            other=other,
            idnum_definitions=[
                IdNumReference(which_idnum=n,
                               idnum_value=1)
                for n in which_ids
            ]
        )
        yield bpi


def gen_all_combinations(x: Sequence[int]) \
        -> Generator[Iterable[int], None, None]:
    """
    Yields all combinations of ``x``, of all lengths, including zero.

    You can apply the ``reversed()`` iterator to get them in reverse order.
    """
    xlen = len(x)
    for r in range(xlen + 1):
        for combo in combinations(x, r):
            yield combo


# =============================================================================
# TokenizedPolicy
# =============================================================================

class TokenizedPolicy(object):
    """
    Represents a tokenized ID policy.

    A tokenized policy is a policy represented by a sequence of integers;
    0 means "bad token"; negative numbers represent fixed things like
    "forename" or "left parenthesis" or "and"; positive numbers represent
    ID number types.
    """
    def __init__(self, policy: str) -> None:
        self.tokens = self.get_tokenized_id_policy(policy)
        self._syntactically_valid = None

    # -------------------------------------------------------------------------
    # Tokenize
    # -------------------------------------------------------------------------

    @staticmethod
    def name_to_token(name: str) -> int:
        """
        Converts an upper-case string token name (such as ``DOB``) to an
        integer token.
        """
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
        Takes a string policy and returns a tokenized policy, meaning a list of
        integer tokens, or ``[]``.
        """
        if policy is None:
            return []
        # http://stackoverflow.com/questions/88613
        string_index = 1
        # single line, upper case:
        policy = " ".join(policy.strip().upper().splitlines())
        try:
            tokenstrings = list(
                token[string_index]
                for token in tokenize.generate_tokens(
                    io.StringIO(policy).readline)
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

    # -------------------------------------------------------------------------
    # Validity checks
    # -------------------------------------------------------------------------

    def is_syntactically_valid(self) -> bool:
        """
        Is the policy syntactically valid? This is a basic check.
        """
        if self._syntactically_valid is None:
            # Cache it
            if not self.tokens:
                self._syntactically_valid = False
            else:
                # Evaluate against a dummy patient info object. If we get None,
                # it's gone wrong.
                ptinfo = BarePatientInfo()
                value = self.id_policy_chunk(self.tokens, ptinfo)
                self._syntactically_valid = value is not None
        return self._syntactically_valid

    def is_valid_from_req(self, req: "CamcopsRequest") -> bool:
        """
        Is the policy valid in the context of the ID types available in our
        database?

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        return self.is_valid(req.valid_which_idnums)

    def is_valid(self, valid_idnums: List[int]) -> bool:
        """
        Is the policy valid, given a list of valid ID number types?

        Checks the following:

        - valid syntax
        - refers only to ID number types defined on the server
        - is compatible with the tablet ID policy

        Args:
            valid_idnums: ID number types that are valid on the server
        """
        # First, syntax:
        if not self.is_syntactically_valid():
            return False
        # Second, all ID numbers referred to by the policy exist:
        for token in self.tokens:
            if token > 0 and token not in valid_idnums:
                return False
        return self.compatible_with_tablet_id_policy(valid_idnums)

    # -------------------------------------------------------------------------
    # Information about the ID number types the policy refers to
    # -------------------------------------------------------------------------

    def relevant_idnums(self, valid_idnums: List[int]) -> List[int]:
        """
        Which ID numbers are relevant to this policy?

        Args:
            valid_idnums: ID number types that are valid on the server

        Returns:
            the subset of ``valid_idnums`` that is mentioned somehow in the
            policy
        """
        if not self.tokens:
            return []
        if TK_ANY_IDNUM in self.tokens or TK_OTHER_IDNUM in self.tokens:
            # all are relevant
            return valid_idnums
        relevant_idnums = []  # type: List[int]
        for which_idnum in valid_idnums:
            assert which_idnum > 0, "Silly ID number types"
            if which_idnum in self.tokens:
                relevant_idnums.append(which_idnum)
        return relevant_idnums

    def specifically_mentioned_idnums(self) -> List[int]:
        return [x for x in self.tokens if x > 0]

    def contains_specific_idnum(self, which_idnum: int) -> bool:
        """
        Does the policy refer specifically to the given ID number type?

        Args:
            which_idnum: ID number type to test
        """
        assert which_idnum > 0
        return which_idnum in self.tokens

    # -------------------------------------------------------------------------
    # More complex attributes
    # -------------------------------------------------------------------------

    def find_critical_single_numerical_id_from_req(
            self, req: "CamcopsRequest") -> Optional[int]:
        """
        Return the single critical required ID number type, if one exists.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        return self.find_critical_single_numerical_id(req.valid_which_idnums)

    def find_critical_single_numerical_id(
            self,
            valid_idnums: List[int]) -> Optional[int]:
        """
        If the policy involves a single mandatory ID number, return that ID
        number; otherwise return None.
        """
        # This method is a bit silly, but it should work.
        if not self.is_valid(valid_idnums):
            return None
        relevant_idnums = self.specifically_mentioned_idnums()
        successes = 0
        critical_idnum = None
        for n in relevant_idnums:
            bpis = gen_test_bpis(which_idnums_present_options=[[n]])
            if any(self.satisfies_id_policy(bpi) for bpi in bpis):
                # Set the idnum of interest
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
            valid_idnums: List[int]) -> bool:
        """
        Is the ID number mandatory in the specified policy?

        Args:
            which_idnum: ID number type to test
            valid_idnums: ID number types that are valid on the server
        """
        if which_idnum is None or which_idnum < 1:
            return False
        if not self.contains_specific_idnum(which_idnum):
            return False
        if not self.is_syntactically_valid():
            return False
        # A hacky way...
        relevant_idnums = self.relevant_idnums(valid_idnums)
        other_idnums = [n for n in relevant_idnums if n != which_idnum]
        for others in reversed(list(gen_all_combinations(other_idnums))):
            # we start with "all other idnums populated", i.e. everthing but
            # the idnum in question is set
            bpis = gen_test_bpis(which_idnums_present_options=[others])
            if any(self.satisfies_id_policy(bpi) for bpi in bpis):
                return False  # because that means it wasn't mandatory
        # That should be it...
        return True

    def less_restrictive_than(self, other: "TokenizedPolicy",
                              valid_idnums: List[int]) -> bool:
        """
        Is this ("self") policy at least as restrictive as the "other" policy?

        Args:
            other: the other policy
            valid_idnums: ID number types that are valid on the server
        """
        # Not elegant, but...
        for which_idnums in gen_all_combinations(valid_idnums):
            for bpi in gen_test_bpis(
                    which_idnums_present_options=[which_idnums]):
                if not other.satisfies_id_policy(bpi):
                    # This bpi does NOT satisfy the others's minimum ID policy.
                    if self.satisfies_id_policy(bpi):
                        # The "self" policy is LESS RESTRICTIVE.
                        return True
        return False

    def compatible_with_tablet_id_policy(self,
                                         valid_idnums: List[int]) -> bool:
        """
        Is this policy compatible with :data:`TABLET_ID_POLICY`?

        The "self" policy may be MORE restrictive than the tablet minimum ID
        policy, but may not be LESS restrictive.

        Args:
            valid_idnums: ID number types that are valid on the server
        """
        return not self.less_restrictive_than(TABLET_ID_POLICY, valid_idnums)

    # -------------------------------------------------------------------------
    # Check if a patient satisfies the policy
    # -------------------------------------------------------------------------

    def satisfies_id_policy(self, ptinfo: BarePatientInfo) -> bool:
        """
        Does the patient information in ptinfo satisfy the specified ID policy?

        Args:
            ptinfo:
                a `camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo`
        """
        return bool(self.id_policy_chunk(self.tokens, ptinfo))
        # ... which is recursive

    # -------------------------------------------------------------------------
    # Functions for the policy to parse itself and compare itself to a patient
    # -------------------------------------------------------------------------

    def id_policy_chunk(self,
                        policy: TOKENIZED_POLICY_TYPE,
                        ptinfo: BarePatientInfo) -> Optional[bool]:
        """
        Applies the policy to the patient info in ``ptinfo``.
        Can be used recursively.

        Args:
            policy:
                a tokenized policy
            ptinfo:
                a `camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo`

        Returns:
            bool: ``True`` if the ``ptinfo`` satisfies the policy; ``False`` if
            it doesn't; ``None`` if there was an error.
        """
        want_content = True
        processing_and = False
        processing_or = False
        index = 0
        value = None
        while index < len(policy):
            if want_content:
                nextchunk, index = self.id_policy_content(policy, ptinfo,
                                                          index)
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
                operator, index = self.id_policy_op(policy, index)
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
        if want_content:
            log.debug("id_policy_chunk: ended wanting content; bad policy")
            return None
        return value

    def id_policy_content(self,
                          policy: TOKENIZED_POLICY_TYPE,
                          ptinfo: BarePatientInfo,
                          start: int) -> Tuple[Optional[bool], int]:
        """
        Applies part of a policy to ``ptinfo``. The part of policy pointed to
        by ``start`` represents something -- "content" -- that should return a
        value (not an operator, for example). Called by :func:`id_policy_chunk`
        (q.v.).

        Args:
            policy:
                a tokenized policy (list of integers)
            ptinfo:
                a `camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo`
            start:
                zero-based index of the first token to check

        Returns:
            tuple: chunk_value, next_index. ``chunk_value`` is ``True`` if the
            specified chunk is satisfied by the ``ptinfo``, ``False`` if it
            isn't, and ``None`` if there was an error. ``next_index`` is the
            index of the next token after this chunk.

        """
        if start >= len(policy):
            log.debug("id_policy_content: beyond end of policy")
            return None, start
        token = policy[start]
        if token in [TK_RPAREN, TK_AND, TK_OR]:
            log.debug("id_policy_content: chunk starts with ), AND, or OR; "
                      "bad policy")
            return None, start
        elif token == TK_LPAREN:
            subchunkstart = start + 1  # exclude the opening bracket
            # Find closing parenthesis
            depth = 1
            searchidx = subchunkstart
            while depth > 0:
                if searchidx >= len(policy):
                    log.debug("id_policy_content: Unmatched left parenthesis; "
                              "bad policy")
                    return None, start
                elif policy[searchidx] == TK_LPAREN:
                    depth += 1
                elif policy[searchidx] == TK_RPAREN:
                    depth -= 1
                searchidx += 1
            subchunkend = searchidx - 1
            # ... to exclude the closing bracket from the analysed subchunk
            chunk_value = self.id_policy_chunk(
                policy[subchunkstart:subchunkend], ptinfo)
            return chunk_value, subchunkend + 1  # to move past the closing bracket  # noqa
        elif token == TK_NOT:
            next_value, next_index = self.id_policy_content(
                policy, ptinfo, start + 1)
            if next_value is None:
                return next_value, start
            return not next_value, next_index
        else:
            # meaningful token
            return self.id_policy_element(ptinfo, token), start + 1

    @classmethod
    def id_policy_op(cls, policy: TOKENIZED_POLICY_TYPE, start: int) \
            -> Tuple[Optional[TOKEN_TYPE], int]:
        """
        Returns an operator from the policy, beginning at index ``start``, or
        ``None`` if there wasn't an operator there.

            policy:
                a tokenized policy (list of integers)
            start:
                zero-based index of the first token to check

        Returns:
            tuple: ``operator, next_index``. ``operator`` is the operator's
            integer token or ``None``. ``next_index`` gives the next index of
            the policy to check at.
        """
        if start >= len(policy):
            log.debug("id_policy_op: beyond end of policy")
            return None, start
        token = policy[start]
        if token in [TK_AND, TK_OR]:
            return token, start + 1
        else:
            log.debug("id_policy_op: not an operator; bad policy")
            # Not an operator
            return None, start

    def id_policy_element(self, ptinfo: BarePatientInfo, token: TOKEN_TYPE) \
            -> Optional[bool]:
        """
        Returns the "value" of a content token as judged against the patient
        information. For example, if the patient information contains a date of
        birth, a ``TK_DOB`` token will evaluate to ``True``.

        Args:
            ptinfo:
                a `camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo`
            token:
                an integer token from the policy

        Returns:
            bool: whether the token's information is present in the ``ptinfo``
            (or ``None`` if it was not a content token)
        """
        if token > 0:  # ID token
            for iddef in ptinfo.idnum_definitions:
                if (iddef.which_idnum == token and
                        iddef.idnum_value is not None):
                    return True
            return False
        elif token == TK_ANY_IDNUM:
            for idnumdef in ptinfo.idnum_definitions:
                if idnumdef.idnum_value is not None:
                    return True
            return False
        elif token == TK_OTHER_IDNUM:
            mentioned_idnums = self.specifically_mentioned_idnums()
            for idnumdef in ptinfo.idnum_definitions:
                if idnumdef.which_idnum not in mentioned_idnums:  # "other"
                    if idnumdef.idnum_value is not None:
                        return True
            return False

        if token == TK_FORENAME:
            return bool(ptinfo.forename)
        elif token == TK_SURNAME:
            return bool(ptinfo.surname)
        elif token == TK_SEX:
            return bool(ptinfo.sex)
        elif token == TK_DOB:
            return ptinfo.dob is not None
        elif token == TK_ADDRESS:
            return bool(ptinfo.address)
        elif token == TK_GP:
            return bool(ptinfo.gp)
        elif token == TK_OTHER_DETAILS:
            return bool(ptinfo.otherdetails)

        else:
            log.debug("id_policy_element: unknown token; bad policy")
            return None


# =============================================================================
# Tablet ID policy
# =============================================================================

TABLET_ID_POLICY_STR = "sex AND ((forename AND surname AND dob) OR anyidnum)"
TABLET_ID_POLICY = TokenizedPolicy(TABLET_ID_POLICY_STR)


# =============================================================================
# Unit tests
# =============================================================================

class PolicyTests(ExtendedTestCase):
    """
    Unit tests.
    """
    def test_policies(self) -> None:
        self.announce("test_policies")

        empty = ""
        bad1 = "sex AND (failure"
        bad2 = "sex AND NOT"
        bad3 = "OR OR"
        bad4 = "idnum99"
        good1 = "sex AND idnum1"
        good2 = "sex AND NOT idnum1"
        good3 = "sex AND NOT idnum2"
        good4 = "sex AND NOT idnum1 AND idnum3"
        good5 = "sex AND NOT idnum2 AND idnum10"
        good6 = "sex AND NOT idnum1 AND NOT idnum2 AND NOT idnum3"
        good7 = "sex AND NOT (idnum1 OR idnum2 OR idnum3)"  # same as previous
        good8 = "NOT (sex OR forename OR surname OR dob OR anyidnum)"
        good9 = """
            NOT (sex OR forename OR surname OR dob OR
                 idnum1 OR idnum2 OR idnum3)
        """
        good10 = "sex AND idnum1 AND otheridnum AND NOT address"
        good11 = (
             "sex AND idnum1 AND NOT (otheridnum OR forename OR surname OR "
             "dob OR address OR gp OR otherdetails)"
        )
        test_idnums = [None, -1, 1, 3]
        all_policies = [
            empty,
            bad1, bad2, bad3, bad4,
            good1, good2, good3, good4, good5, good6, good7, good8, good9,
            good10, good11,
        ]
        valid_idnums = [1, 2, 3]
        bpi = BarePatientInfo(
            forename="forename",
            surname="surname",
            dob=Date.today(),  # random value
            sex="F",
            idnum_definitions=[
                IdNumReference(1, 1),
                IdNumReference(10, 3),
            ],
        )
        for policy_string in all_policies:
            log.info("Testing {!r}".format(policy_string))
            p = TokenizedPolicy(policy_string)

            x = p.is_syntactically_valid()
            self.assertIsInstance(x, bool)
            print("is_syntactically_valid() -> {!r}".format(x))

            x = p.is_valid(valid_idnums=valid_idnums)
            self.assertIsInstance(x, bool)
            print("is_valid(valid_idnums={!r}) -> {!r}".format(
                valid_idnums, x))

            x = p.find_critical_single_numerical_id(valid_idnums=valid_idnums)
            self.assertIsInstanceOrNone(x, int)
            print(
                "find_critical_single_numerical_id(valid_idnums={!r}) "
                "-> {!r}".format(valid_idnums, x)
            )

            x = p.compatible_with_tablet_id_policy(valid_idnums=valid_idnums)
            self.assertIsInstance(x, bool)
            print("compatible_with_tablet_id_policy(valid_idnums={!r}) "
                  "-> {!r}".format(valid_idnums, x))

            for which_idnum in test_idnums:
                x = p.is_idnum_mandatory_in_policy(
                    which_idnum=which_idnum,
                    valid_idnums=valid_idnums
                )
                self.assertIsInstance(x, bool)
                print(
                    "is_idnum_mandatory_in_policy(which_idnum={!r}, "
                    "valid_idnums={!r}) -> {!r}".format(
                        which_idnum, valid_idnums, x))

            x = p.satisfies_id_policy(bpi)
            self.assertIsInstance(x, bool)
            print("satisfies_id_policy(bpi={}) -> {!r}".format(bpi, x))

            if policy_string == good1:
                self.assertEqual(p.find_critical_single_numerical_id(
                    valid_idnums=valid_idnums), 1)
                self.assertEqual(p.satisfies_id_policy(bpi), True)

            if policy_string == good2:
                self.assertEqual(p.satisfies_id_policy(bpi), False)


if __name__ == "__main__":
    # Run with "python cc_policy.py" to test.
    main_only_quicksetup_rootlogger(level=logging.DEBUG)
    unittest.main()
