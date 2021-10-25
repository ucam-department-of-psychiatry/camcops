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
    DEFAULT_LANGUAGE = "da_DK"
    DEFAULT_LANGUAGE_ISO_639_1 = "da"

    def setUp(self):
        super().setUp()

        environ = dict()
        self.request = CamcopsRequest(environ)
        self.request.session = mock.Mock(user=None)
        self.request.config.language = self.DEFAULT_LANGUAGE

    def test_gettext_danish(self):
        self.request._debugging_user = mock.Mock(language="da_DK")

        # Something unlikely to change
        self.assertEqual(self.request.gettext("Cancel"), "Annuller")

    def test_language_returns_default_if_no_user(self):
        self.request._debugging_user = None

        self.assertEqual(self.request.language, self.DEFAULT_LANGUAGE)

    def test_language_returns_users_if_set(self):
        self.request._debugging_user = mock.Mock(language="en_GB")

        self.assertEqual(self.request.language, "en_GB")

    def test_language_returns_default_if_users_not_set(self):
        self.request._debugging_user = mock.Mock(language=None)

        self.assertEqual(self.request.language, self.DEFAULT_LANGUAGE)

    def test_language_returns_default_if_users_not_valid(self):
        self.request._debugging_user = mock.Mock(language="es_ES")

        self.assertEqual(self.request.language, self.DEFAULT_LANGUAGE)

    def test_language_iso_639_1_returns_default_if_no_user(self):
        self.request._debugging_user = None

        self.assertEqual(self.request.language_iso_639_1,
                         self.DEFAULT_LANGUAGE_ISO_639_1)

    def test_language_iso_639_1_returns_users_if_set(self):
        self.request._debugging_user = mock.Mock(language="en_GB")

        self.assertEqual(self.request.language_iso_639_1, "en")

    def test_language_iso_639_1_returns_default_if_users_not_set(self):
        self.request._debugging_user = mock.Mock(language=None)

        self.assertEqual(self.request.language_iso_639_1,
                         self.DEFAULT_LANGUAGE_ISO_639_1)

    def test_language_iso_639_1_returns_default_if_users_not_valid(self):
        self.request._debugging_user = mock.Mock(language="d")

        self.assertEqual(self.request.language_iso_639_1,
                         self.DEFAULT_LANGUAGE_ISO_639_1)
