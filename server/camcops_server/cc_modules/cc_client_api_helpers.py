#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_client_api_helpers.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

**Additional helper functions used by the client (tablet device) API and the
webview for special features.**

"""

import re
from typing import Tuple
import unittest

from cardinal_pythonlib.colander_utils import EMAIL_ADDRESS_MAX_LEN
from colander import EMAIL_RE
from sqlalchemy.sql.schema import Table

from camcops_server.cc_modules.cc_all_models import NONTASK_CLIENT_TABLENAMES
from camcops_server.cc_modules.cc_patient import Patient, PatientIdNum


# =============================================================================
# Constants
# =============================================================================

EMAIL_RE_COMPILED = re.compile(EMAIL_RE)


# =============================================================================
# Table sort order
# =============================================================================

def upload_commit_order_sorter(x: Table) -> Tuple[bool, bool, bool, str]:
    """
    Function to sort tables for the commit phase of the upload.
    
    - "patient" must come before "patient_idnum", since ID number indexing
      looks at the associated Patient.
      
    - All of "patient", "blobs", and all ancillary tables must come before task
      tables, because task indexes depend on tasks correctly retrieving their
      subsidiary information to determine their
      :meth:`camcops_server.cc_modules.cc_task.Task.is_complete` status.
      (However, even though ancillary tables can refer to BLOBs, as long as
      both are complete before the task tables are examined, their relative
      order doesn't matter.)

    - Task tables come last.

    Args:
        x: an SQLAlchemy :class:`Table`

    Returns:
        a tuple suitable for use as the key to a ``sort()`` or ``sorted()``
        operation

    Note that ``False`` sorts before ``True``, and see
    https://stackoverflow.com/questions/23090664/sorting-a-list-of-string-in-python-such-that-a-specific-string-if-present-appea.
    """  # noqa
    return (x.name != Patient.__tablename__,
            x.name != PatientIdNum.__tablename__,
            x.name not in NONTASK_CLIENT_TABLENAMES,
            x.name)


# =============================================================================
# Email address validation
# =============================================================================

def is_email_valid(email: str) -> bool:
    """
    Is this a valid e-mail address?

    We use the same validation system as our web form (which uses Colander's
    method plus a length constraint).
    """
    if not isinstance(email, str) or not email:
        return False
    if len(email) > EMAIL_ADDRESS_MAX_LEN:
        return False
    return bool(EMAIL_RE_COMPILED.match(email))


# =============================================================================
# Unit tests
# =============================================================================

class EmailValidatorTests(unittest.TestCase):
    """
    Test our e-mail validator.
    """

    def test_email_validator(self) -> None:
        good = [
            "blah@somewhere.com",
            "r&d@sillydomain.co.uk",
        ]
        bad = [
            "plaintext",
            "plain.domain.com",
            "two@at@symbols.com",
        ]
        for email in good:
            self.assertTrue(is_email_valid(email))
        for email in bad:
            self.assertFalse(is_email_valid(email))
