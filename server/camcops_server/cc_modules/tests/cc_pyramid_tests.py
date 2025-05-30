"""
camcops_server/cc_modules/tests/cc_pyramid_tests.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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

from camcops_server.cc_modules.cc_constants import MfaMethod
from camcops_server.cc_modules.cc_pyramid import (
    CamcopsAuthenticationPolicy,
    Permission,
)
from camcops_server.cc_modules.cc_testfactories import (
    GroupFactory,
    UserFactory,
    UserGroupMembershipFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase


class CamcopsAuthenticationPolicyTests(DemoRequestTestCase):
    def test_principals_for_no_user(self) -> None:
        self.req._debugging_user = None
        self.assertEqual(
            CamcopsAuthenticationPolicy.effective_principals(self.req),
            [Everyone],
        )

    def test_principals_for_authenticated_user(self) -> None:
        user = self.req._debugging_user = UserFactory()
        self.assertIn(
            Authenticated,
            CamcopsAuthenticationPolicy.effective_principals(self.req),
        )
        self.assertIn(
            f"u:{user.id}",
            CamcopsAuthenticationPolicy.effective_principals(self.req),
        )

    def test_principals_when_user_must_change_pasword(self) -> None:
        user = self.req._debugging_user = UserFactory(
            when_agreed_terms_of_use=self.req.now,
            must_change_password=True,
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

        self.assertIn(
            Permission.MUST_CHANGE_PASSWORD,
            CamcopsAuthenticationPolicy.effective_principals(self.req),
        )

    def test_principals_when_user_must_set_up_mfa(self) -> None:
        user = self.req._debugging_user = UserFactory(
            mfa_method=MfaMethod.NO_MFA, when_agreed_terms_of_use=self.req.now
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

        self.req.config.mfa_methods = [MfaMethod.HOTP_EMAIL]
        self.assertIn(
            Permission.MUST_SET_MFA,
            CamcopsAuthenticationPolicy.effective_principals(self.req),
        )

    def test_principals_when_user_must_agree_terms(self) -> None:
        user = self.req._debugging_user = UserFactory(
            when_agreed_terms_of_use=None
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

        self.assertIn(
            Permission.MUST_AGREE_TERMS,
            CamcopsAuthenticationPolicy.effective_principals(self.req),
        )

    def test_principals_when_everything_ok(self) -> None:
        user = self.req._debugging_user = UserFactory(
            mfa_method=MfaMethod.NO_MFA, when_agreed_terms_of_use=self.req.now
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

        self.req.config.mfa_methods = [MfaMethod.NO_MFA]
        self.assertIn(
            Permission.HAPPY,
            CamcopsAuthenticationPolicy.effective_principals(self.req),
        )

    def test_principals_for_superuser(self) -> None:
        self.req._debugging_user = UserFactory(superuser=True)

        self.assertIn(
            Permission.SUPERUSER,
            CamcopsAuthenticationPolicy.effective_principals(self.req),
        )

    def test_principals_for_groupadmin(self) -> None:
        user = self.req._debugging_user = UserFactory()
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, groupadmin=True
        )

        self.req._debugging_user = user
        self.assertIn(
            Permission.GROUPADMIN,
            CamcopsAuthenticationPolicy.effective_principals(self.req),
        )
