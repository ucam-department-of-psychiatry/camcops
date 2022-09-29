#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_view_classes_tests.py

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

from cardinal_pythonlib.typing_helpers import with_typehint
from camcops_server.cc_modules.cc_session import CamcopsSession
from camcops_server.cc_modules.cc_unittest import BasicDatabaseTestCase
from camcops_server.cc_modules.cc_view_classes import FormWizardMixin, View


class TestView(FormWizardMixin, View):
    pass


class TestStateMixin(with_typehint(BasicDatabaseTestCase)):
    """
    For testing FormWizardMixin state.
    """

    def assert_state_is_finished(self) -> None:
        """
        Asserts that the state has been marked as "finished", i.e. with the
        finish flag set to true and only selected other parameters present.
        """
        state = self.req.camcops_session.form_state
        self.assertIsNotNone(state, msg="state is None (incorrect)")
        self.assertTrue(
            state[FormWizardMixin.PARAM_FINISHED],
            msg=f"PARAM_FINISHED is "
            f"{state[FormWizardMixin.PARAM_FINISHED]!r} (should be True)",
        )
        expected_finished_params = {
            FormWizardMixin.PARAM_FINISHED,
            FormWizardMixin.PARAM_ROUTE_NAME,
            FormWizardMixin.PARAM_STEP,
        }
        state_params = set(state.keys())
        wrong_params = state_params - expected_finished_params
        missing_params = expected_finished_params - state_params
        self.assertFalse(
            bool(wrong_params),
            msg=f"Inappropriate parameters: {wrong_params!r}",
        )
        self.assertFalse(
            bool(missing_params), msg=f"Missing parameters: {missing_params!r}"
        )

    def assert_state_is_clean(self) -> None:
        """
        Asserts that the state is None or contains only certain permitted
        parameters.
        """
        state = self.req.camcops_session.form_state
        permissible_params = {
            FormWizardMixin.PARAM_FINISHED,
            FormWizardMixin.PARAM_ROUTE_NAME,
            FormWizardMixin.PARAM_STEP,
        }
        state_is_none = bool(state is None)
        state_params = set(state.keys())
        wrong_params = state_params - permissible_params
        state_contains_only_permissible_params = not wrong_params
        self.assertTrue(
            state_is_none or state_contains_only_permissible_params,
            msg=f"State contains inappropriate parameters {wrong_params!r}",
        )


class FormWizardMixinTests(TestStateMixin, BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.req.matched_route.name = "test_route"

    def test_route_name_is_saved_in_existing_session(self) -> None:
        self.req.camcops_session.form_state = {
            FormWizardMixin.PARAM_STEP: "some-previous-step",
            FormWizardMixin.PARAM_ROUTE_NAME: "some_previous_route_name",
        }
        self.req.dbsession.add(self.req.camcops_session)
        self.req.dbsession.commit()

        TestView(self.req)

        self.assertEqual(
            self.req.camcops_session.form_state[
                FormWizardMixin.PARAM_ROUTE_NAME
            ],  # noqa
            "test_route",
        )

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = (
            self.req.dbsession.query(CamcopsSession)
            .filter(CamcopsSession.id == session_id)
            .one()
        )

        self.assertEqual(
            session.form_state[FormWizardMixin.PARAM_ROUTE_NAME], "test_route"
        )

    def test_step_is_saved_in_new_session(self) -> None:
        view = TestView(self.req)
        view.step = "test"
        self.assertEqual(
            self.req.camcops_session.form_state[FormWizardMixin.PARAM_STEP],
            "test",
        )

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = (
            self.req.dbsession.query(CamcopsSession)
            .filter(CamcopsSession.id == session_id)
            .one()
        )

        self.assertEqual(
            session.form_state[FormWizardMixin.PARAM_STEP], "test"
        )

    def test_route_name_is_saved_in_new_session(self) -> None:
        TestView(self.req)

        self.assertEqual(
            self.req.camcops_session.form_state[
                FormWizardMixin.PARAM_ROUTE_NAME
            ],  # noqa
            "test_route",
        )

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = (
            self.req.dbsession.query(CamcopsSession)
            .filter(CamcopsSession.id == session_id)
            .one()
        )

        self.assertEqual(
            session.form_state[FormWizardMixin.PARAM_ROUTE_NAME], "test_route"
        )

    def test_step_is_updated_for_same_route(self) -> None:
        self.req.camcops_session.form_state = {
            FormWizardMixin.PARAM_STEP: "previous_step",
            FormWizardMixin.PARAM_ROUTE_NAME: "test_route",
        }
        self.req.dbsession.add(self.req.camcops_session)
        self.req.dbsession.commit()

        view = TestView(self.req)
        view.step = "next_step"
        self.assertEqual(
            self.req.camcops_session.form_state[FormWizardMixin.PARAM_STEP],
            "next_step",
        )

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = (
            self.req.dbsession.query(CamcopsSession)
            .filter(CamcopsSession.id == session_id)
            .one()
        )

        self.assertEqual(
            session.form_state[FormWizardMixin.PARAM_STEP], "next_step"
        )

    def test_arbitrary_field_is_saved_in_new_session(self) -> None:
        view = TestView(self.req)
        view.state["test_field"] = "test_value"

        self.assertEqual(
            self.req.camcops_session.form_state["test_field"], "test_value"
        )

        self.req.dbsession.flush()
        session_id = self.req.camcops_session.id
        self.assertIsNotNone(session_id)

        self.req.dbsession.commit()

        session = (
            self.req.dbsession.query(CamcopsSession)
            .filter(CamcopsSession.id == session_id)
            .one()
        )

        self.assertEqual(session.form_state["test_field"], "test_value")

    def test_finish_and_finished(self) -> None:
        self.req.camcops_session.form_state = {
            FormWizardMixin.PARAM_STEP: "previous_step",
            FormWizardMixin.PARAM_ROUTE_NAME: "test_route",
        }
        self.req.dbsession.add(self.req.camcops_session)
        self.req.dbsession.commit()

        view = TestView(self.req)
        self.assertFalse(view.finished())

        view.finish()

        self.assertTrue(view.finished())
        self.assert_state_is_finished()
