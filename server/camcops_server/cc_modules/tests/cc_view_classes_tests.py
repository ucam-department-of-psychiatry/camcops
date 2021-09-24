#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_view_classes_tests.py

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

from camcops_server.cc_modules.cc_session import CamcopsSession
from camcops_server.cc_modules.cc_unittest import BasicDatabaseTestCase
from camcops_server.cc_modules.cc_view_classes import FormWizardMixin, View


class TestView(FormWizardMixin, View):
    pass


class FormWizardMixinTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.req.matched_route.name = "test_route"

    def test_route_name_is_saved_in_existing_session(self) -> None:
        self.req.camcops_session.form_state = {
            "step": "some-previous-step",
            "route_name": "some_previous_route_name",
        }
        self.req.dbsession.add(self.req.camcops_session)
        self.req.dbsession.commit()

        TestView(self.req)

        self.assertEqual(self.req.camcops_session.form_state["route_name"],
                         "test_route")

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = self.req.dbsession.query(CamcopsSession).filter(
            CamcopsSession.id == session_id
        ).one()

        self.assertEqual(session.form_state["route_name"], "test_route")

    def test_step_is_saved_in_new_session(self) -> None:
        view = TestView(self.req)
        view.step = "test"
        self.assertEqual(self.req.camcops_session.form_state["step"], "test")

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = self.req.dbsession.query(CamcopsSession).filter(
            CamcopsSession.id == session_id
        ).one()

        self.assertEqual(session.form_state["step"], "test")

    def test_route_name_is_saved_in_new_session(self) -> None:
        TestView(self.req)

        self.assertEqual(self.req.camcops_session.form_state["route_name"],
                         "test_route")

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = self.req.dbsession.query(CamcopsSession).filter(
            CamcopsSession.id == session_id
        ).one()

        self.assertEqual(session.form_state["route_name"], "test_route")

    def test_step_is_updated_for_same_route(self) -> None:
        self.req.camcops_session.form_state = {
            "step": "previous_step",
            "route_name": "test_route",
        }
        self.req.dbsession.add(self.req.camcops_session)
        self.req.dbsession.commit()

        view = TestView(self.req)
        view.step = "next_step"
        self.assertEqual(self.req.camcops_session.form_state["step"],
                         "next_step")

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = self.req.dbsession.query(CamcopsSession).filter(
            CamcopsSession.id == session_id
        ).one()

        self.assertEqual(session.form_state["step"], "next_step")

    def test_arbitrary_field_is_saved_in_new_session(self) -> None:
        view = TestView(self.req)
        view.state["test_field"] = "test_value"

        self.assertEqual(self.req.camcops_session.form_state["test_field"],
                         "test_value")

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = self.req.dbsession.query(CamcopsSession).filter(
            CamcopsSession.id == session_id
        ).one()

        self.assertEqual(session.form_state["test_field"], "test_value")

    def test_finish_and_finished(self) -> None:
        self.req.camcops_session.form_state = {
            "step": "previous_step",
            "route_name": "test_route",
        }
        self.req.dbsession.add(self.req.camcops_session)
        self.req.dbsession.commit()

        view = TestView(self.req)
        self.assertFalse(view.finished())

        view.finish()

        self.assertTrue(view.finished())
        self.assertIsNone(self.req.camcops_session.form_state)
