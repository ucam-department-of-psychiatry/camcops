#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_pyramid_tests.py

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


from pyramid.security import Authenticated, Everyone

from camcops_server.cc_modules.cc_pyramid import (
    CamcopsAuthenticationPolicy,
    Permission,
)
from camcops_server.cc_modules.cc_unittest import BasicDatabaseTestCase


class CamcopsAuthenticationPolicyTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_principals_for_no_user(self):
        self.req._debugging_user = None
        self.assertEqual(
            CamcopsAuthenticationPolicy.effective_principals(self.req),
            [Everyone]
        )

    def test_principals_for_authenticated_user(self):
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.req._debugging_user = user
        self.assertIn(
            Authenticated,
            CamcopsAuthenticationPolicy.effective_principals(self.req)
        )
        self.assertIn(
            f"u:{user.id}",
            CamcopsAuthenticationPolicy.effective_principals(self.req)
        )

    def test_principals_when_user_must_change_pasword(self):
        user = self.create_user(username="test",
                                must_change_password=True)
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        self.req._debugging_user = user
        self.assertIn(
            Permission.MUST_CHANGE_PASSWORD,
            CamcopsAuthenticationPolicy.effective_principals(self.req)
        )

    def test_principals_when_user_must_agree_terms(self):
        user = self.create_user(username="test",
                                when_agreed_terms_of_use=None)
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        self.req._debugging_user = user
        self.assertIn(
            Permission.MUST_AGREE_TERMS,
            CamcopsAuthenticationPolicy.effective_principals(self.req)
        )

    def test_principals_when_agreed_terms_and_password_ok(self):
        user = self.create_user(username="test")
        user.agree_terms(self.req)
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        self.req._debugging_user = user
        self.assertIn(
            Permission.HAPPY,
            CamcopsAuthenticationPolicy.effective_principals(self.req)
        )

    def test_principals_for_superuser(self):
        user = self.create_user(username="test", superuser=True)
        self.dbsession.flush()

        self.req._debugging_user = user
        self.assertIn(
            Permission.SUPERUSER,
            CamcopsAuthenticationPolicy.effective_principals(self.req)
        )

    def test_principals_for_groupadmin(self):
        user = self.create_user(username="test")
        self.dbsession.flush()
        self.create_membership(user, self.group, groupadmin=True)

        self.req._debugging_user = user
        self.assertIn(
            Permission.GROUPADMIN,
            CamcopsAuthenticationPolicy.effective_principals(self.req)
        )
