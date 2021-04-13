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

"""
import unittest

from camcops_server.cc_modules.cc_client_api_helpers import is_email_valid


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
