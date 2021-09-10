#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_request_tests.py

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

"""

from unittest import mock, TestCase

from camcops_server.cc_modules.cc_request import CamcopsRequest


class RequestTests(TestCase):
    def test_gettext_danish(self):
        environ = dict()
        request = CamcopsRequest(environ)
        request._debugging_user = mock.Mock(language="da_DK")

        # Something unlikely to change
        self.assertEqual(request.gettext("Cancel"), "Annuller")
