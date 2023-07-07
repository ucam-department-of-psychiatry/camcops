#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/webview_tests.py

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

from collections import OrderedDict
import datetime
import json
import logging
import time
from typing import cast
import unittest
from unittest import mock

from cardinal_pythonlib.classes import class_attribute_names
from cardinal_pythonlib.httpconst import MimeType
from cardinal_pythonlib.nhs import generate_random_nhs_number
from pendulum import local
import phonenumbers
import pyotp
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from webob.multidict import MultiDict

from camcops_server.cc_modules.cc_constants import (
    ERA_NOW,
    MfaMethod,
    SmsBackendNames,
)
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_membership import UserGroupMembership
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
from camcops_server.cc_modules.cc_pyramid import (
    FlashQueue,
    FormAction,
    Routes,
    ViewArg,
    ViewParam,
)
from camcops_server.cc_modules.cc_sms import ConsoleSmsBackend, get_sms_backend
from camcops_server.cc_modules.cc_taskindex import PatientIdNumIndexEntry
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    TaskSchedule,
    TaskScheduleItem,
)
from camcops_server.cc_modules.cc_unittest import (
    BasicDatabaseTestCase,
    DemoDatabaseTestCase,
)
from camcops_server.cc_modules.cc_user import (
    SecurityAccountLockout,
    SecurityLoginFailure,
    User,
)
from camcops_server.cc_modules.cc_validators import (
    validate_alphanum_underscore,
)
from camcops_server.cc_modules.cc_view_classes import FormWizardMixin
from camcops_server.cc_modules.tests.cc_view_classes_tests import (
    TestStateMixin,
)
from camcops_server.cc_modules.webview import (
    add_patient,
    AddPatientView,
    AddTaskScheduleItemView,
    AddTaskScheduleView,
    any_records_use_group,
    change_own_password,
    ChangeOtherPasswordView,
    ChangeOwnPasswordView,
    DeleteServerCreatedPatientView,
    DeleteTaskScheduleItemView,
    DeleteTaskScheduleView,
    edit_finalized_patient,
    edit_group,
    edit_server_created_patient,
    edit_user,
    edit_user_group_membership,
    EditFinalizedPatientView,
    EditGroupView,
    EditOtherUserMfaView,
    EditOwnUserMfaView,
    EditServerCreatedPatientView,
    EditTaskScheduleItemView,
    EditTaskScheduleView,
    EditUserGroupAdminView,
    EraseTaskEntirelyView,
    EraseTaskLeavingPlaceholderView,
    LoginView,
    MfaMixin,
    SendEmailFromPatientTaskScheduleView,
)

log = logging.getLogger(__name__)


# =============================================================================
# Unit testing
# =============================================================================

UTF8 = "utf-8"

TEST_NHS_NUMBER_1 = generate_random_nhs_number()
TEST_NHS_NUMBER_2 = generate_random_nhs_number()

# https://www.ofcom.org.uk/phones-telecoms-and-internet/information-for-industry/numbering/numbers-for-drama  # noqa: E501
# 07700 900000 to 900999 reserved for TV and Radio drama purposes
# but unfortunately phonenumbers considers these invalid. However, it offers
# some examples:
TEST_PHONE_NUMBER = "+{ctry}{tel}".format(
    ctry=phonenumbers.PhoneMetadata.metadata_for_region("GB").country_code,
    tel=phonenumbers.PhoneMetadata.metadata_for_region(
        "GB"
    ).personal_number.example_number,
)


class WebviewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def test_any_records_use_group_true(self) -> None:
        # All tasks created in DemoDatabaseTestCase will be in this group
        self.announce("test_any_records_use_group_true")
        self.assertTrue(any_records_use_group(self.req, self.group))

    def test_any_records_use_group_false(self) -> None:
        """
        If this fails with:
        sqlalchemy.exc.InvalidRequestError: SQL expression, column, or mapped
        entity expected - got <name of task base class>
        then the base class probably needs to be declared __abstract__. See
        DiagnosisItemBase as an example.
        """
        self.announce("test_any_records_use_group_false")
        group = Group()
        self.dbsession.add(self.group)
        self.dbsession.commit()

        self.assertFalse(any_records_use_group(self.req, group))

    def test_webview_constant_validators(self) -> None:
        self.announce("test_webview_constant_validators")
        for x in class_attribute_names(ViewArg):
            try:
                validate_alphanum_underscore(x, self.req)
            except ValueError:
                self.fail(f"Operations.{x} fails validate_alphanum_underscore")


class AddTaskScheduleViewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def test_schedule_form_displayed(self) -> None:
        view = AddTaskScheduleView(self.req)

        response = view.dispatch()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body.decode(UTF8).count("<form"), 1)

    def test_schedule_is_created(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.NAME, "MOJO"),
                (ViewParam.GROUP_ID, self.group.id),
                (ViewParam.EMAIL_FROM, "server@example.com"),
                (ViewParam.EMAIL_CC, "cc@example.com"),
                (ViewParam.EMAIL_BCC, "bcc@example.com"),
                (ViewParam.EMAIL_SUBJECT, "Subject"),
                (ViewParam.EMAIL_TEMPLATE, "Email template"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = AddTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound) as e:
            view.dispatch()

        schedule = self.dbsession.query(TaskSchedule).one()

        self.assertEqual(schedule.name, "MOJO")
        self.assertEqual(schedule.email_from, "server@example.com")
        self.assertEqual(schedule.email_bcc, "bcc@example.com")
        self.assertEqual(schedule.email_subject, "Subject")
        self.assertEqual(schedule.email_template, "Email template")

        self.assertEqual(e.exception.status_code, 302)
        self.assertIn(
            Routes.VIEW_TASK_SCHEDULES, e.exception.headers["Location"]
        )


class EditTaskScheduleViewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def setUp(self) -> None:
        super().setUp()

        self.schedule = TaskSchedule()
        self.schedule.group_id = self.group.id
        self.schedule.name = "Test"
        self.dbsession.add(self.schedule)
        self.dbsession.commit()

    def test_schedule_name_can_be_updated(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.NAME, "MOJO"),
                (ViewParam.GROUP_ID, self.group.id),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.SCHEDULE_ID: str(self.schedule.id)},
            set_method_get=False,
        )

        view = EditTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound) as e:
            view.dispatch()

        schedule = self.dbsession.query(TaskSchedule).one()

        self.assertEqual(schedule.name, "MOJO")

        self.assertEqual(e.exception.status_code, 302)
        self.assertIn(
            Routes.VIEW_TASK_SCHEDULES, e.exception.headers["Location"]
        )

    def test_group_a_schedule_cannot_be_edited_by_group_b_admin(self) -> None:
        group_a = Group()
        group_a.name = "Group A"
        self.dbsession.add(group_a)

        group_b = Group()
        group_b.name = "Group B"
        self.dbsession.add(group_b)
        self.dbsession.commit()

        group_a_schedule = TaskSchedule()
        group_a_schedule.group_id = group_a.id
        group_a_schedule.name = "Group A schedule"
        self.dbsession.add(group_a_schedule)
        self.dbsession.commit()

        self.user = User()
        self.user.upload_group_id = group_b.id
        self.user.username = "group b admin"
        self.user.set_password(self.req, "secret123")
        self.dbsession.add(self.user)
        self.dbsession.commit()
        self.req._debugging_user = self.user

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.NAME, "Something else"),
                (ViewParam.GROUP_ID, self.group.id),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.SCHEDULE_ID: str(self.schedule.id)},
            set_method_get=False,
        )

        view = EditTaskScheduleView(self.req)

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("not a group administrator", cm.exception.message)


class DeleteTaskScheduleViewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def setUp(self) -> None:
        super().setUp()

        self.schedule = TaskSchedule()
        self.schedule.group_id = self.group.id
        self.schedule.name = "Test"
        self.dbsession.add(self.schedule)
        self.dbsession.commit()

    def test_schedule_item_is_deleted(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                ("confirm_1_t", "true"),
                ("confirm_2_t", "true"),
                ("confirm_4_t", "true"),
                ("__start__", "danger:mapping"),
                ("target", "7176"),
                ("user_entry", "7176"),
                ("__end__", "danger:mapping"),
                ("delete", "delete"),
                (FormAction.DELETE, "delete"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.SCHEDULE_ID: str(self.schedule.id)},
            set_method_get=False,
        )
        view = DeleteTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound) as e:
            view.dispatch()

        self.assertEqual(e.exception.status_code, 302)
        self.assertIn(
            Routes.VIEW_TASK_SCHEDULES, e.exception.headers["Location"]
        )

        item = self.dbsession.query(TaskScheduleItem).one_or_none()

        self.assertIsNone(item)


class AddTaskScheduleItemViewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def setUp(self) -> None:
        super().setUp()

        self.schedule = TaskSchedule()
        self.schedule.group_id = self.group.id
        self.schedule.name = "Test"

        self.dbsession.add(self.schedule)
        self.dbsession.commit()

    def test_schedule_item_form_displayed(self) -> None:
        view = AddTaskScheduleItemView(self.req)

        self.req.add_get_params({ViewParam.SCHEDULE_ID: str(self.schedule.id)})

        response = view.dispatch()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body.decode(UTF8).count("<form"), 1)

    def test_schedule_item_is_created(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SCHEDULE_ID, self.schedule.id),
                (ViewParam.TABLE_NAME, "ace3"),
                (ViewParam.CLINICIAN_CONFIRMATION, "true"),
                ("__start__", "due_from:mapping"),
                ("months", "1"),
                ("weeks", "2"),
                ("days", "3"),
                ("__end__", "due_from:mapping"),
                ("__start__", "due_within:mapping"),
                ("months", "2"),  # 60 days
                ("weeks", "3"),  # 21 days
                ("days", "15"),  # 15 days
                ("__end__", "due_within:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = AddTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPFound) as e:
            view.dispatch()

        item = self.dbsession.query(TaskScheduleItem).one()

        self.assertEqual(item.schedule_id, self.schedule.id)
        self.assertEqual(item.task_table_name, "ace3")
        self.assertEqual(item.due_from.in_days(), 47)
        self.assertEqual(item.due_by.in_days(), 143)

        self.assertEqual(e.exception.status_code, 302)
        self.assertIn(
            f"{Routes.VIEW_TASK_SCHEDULE_ITEMS}"
            f"?{ViewParam.SCHEDULE_ID}={self.schedule.id}",
            e.exception.headers["Location"],
        )

    def test_schedule_item_is_not_created_on_cancel(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SCHEDULE_ID, self.schedule.id),
                (ViewParam.TABLE_NAME, "ace3"),
                ("__start__", "due_from:mapping"),
                ("months", "1"),
                ("weeks", "2"),
                ("days", "3"),
                ("__end__", "due_from:mapping"),
                ("__start__", "due_within:mapping"),
                ("months", "4"),
                ("weeks", "3"),
                ("days", "2"),
                ("__end__", "due_within:mapping"),
                (FormAction.CANCEL, "cancel"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = AddTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        item = self.dbsession.query(TaskScheduleItem).one_or_none()

        self.assertIsNone(item)

    def test_non_existent_schedule_handled(self) -> None:
        self.req.add_get_params({ViewParam.SCHEDULE_ID: "99999"})

        view = AddTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPBadRequest):
            view.dispatch()


class EditTaskScheduleItemViewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def setUp(self) -> None:
        from pendulum import Duration

        super().setUp()

        self.schedule = TaskSchedule()
        self.schedule.group_id = self.group.id
        self.schedule.name = "Test"
        self.dbsession.add(self.schedule)
        self.dbsession.commit()

        self.item = TaskScheduleItem()
        self.item.schedule_id = self.schedule.id
        self.item.task_table_name = "ace3"
        self.item.due_from = Duration(days=30)
        self.item.due_by = Duration(days=60)
        self.dbsession.add(self.item)
        self.dbsession.commit()

    def test_schedule_item_is_updated(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SCHEDULE_ID, self.schedule.id),
                (ViewParam.TABLE_NAME, "bmi"),
                ("__start__", "due_from:mapping"),
                ("months", "0"),
                ("weeks", "0"),
                ("days", "30"),
                ("__end__", "due_from:mapping"),
                ("__start__", "due_within:mapping"),
                ("months", "0"),
                ("weeks", "0"),
                ("days", "60"),
                ("__end__", "due_within:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.SCHEDULE_ITEM_ID: str(self.item.id)},
            set_method_get=False,
        )
        view = EditTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPFound) as cm:
            view.dispatch()

        self.assertEqual(self.item.task_table_name, "bmi")
        self.assertEqual(cm.exception.status_code, 302)
        self.assertIn(
            f"{Routes.VIEW_TASK_SCHEDULE_ITEMS}"
            f"?{ViewParam.SCHEDULE_ID}={self.item.schedule_id}",
            cm.exception.headers["Location"],
        )

    def test_schedule_item_is_not_updated_on_cancel(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SCHEDULE_ID, self.schedule.id),
                (ViewParam.TABLE_NAME, "bmi"),
                ("__start__", "due_from:mapping"),
                ("months", "0"),
                ("weeks", "0"),
                ("days", "30"),
                ("__end__", "due_from:mapping"),
                ("__start__", "due_within:mapping"),
                ("months", "0"),
                ("weeks", "0"),
                ("days", "60"),
                ("__end__", "due_within:mapping"),
                (FormAction.CANCEL, "cancel"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.SCHEDULE_ITEM_ID: str(self.item.id)},
            set_method_get=False,
        )
        view = EditTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        self.assertEqual(self.item.task_table_name, "ace3")

    def test_non_existent_item_handled(self) -> None:
        self.req.add_get_params({ViewParam.SCHEDULE_ITEM_ID: "99999"})

        view = EditTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPBadRequest):
            view.dispatch()

    def test_null_item_handled(self) -> None:
        view = EditTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPBadRequest):
            view.dispatch()

    def test_get_form_values(self) -> None:
        view = EditTaskScheduleItemView(self.req)
        view.object = self.item

        form_values = view.get_form_values()

        self.assertEqual(form_values[ViewParam.SCHEDULE_ID], self.schedule.id)
        self.assertEqual(
            form_values[ViewParam.TABLE_NAME], self.item.task_table_name
        )
        self.assertEqual(form_values[ViewParam.DUE_FROM], self.item.due_from)

        due_within = self.item.due_by - self.item.due_from
        self.assertEqual(form_values[ViewParam.DUE_WITHIN], due_within)

    def test_group_a_item_cannot_be_edited_by_group_b_admin(self) -> None:
        from pendulum import Duration

        group_a = Group()
        group_a.name = "Group A"
        self.dbsession.add(group_a)

        group_b = Group()
        group_b.name = "Group B"
        self.dbsession.add(group_b)
        self.dbsession.commit()

        group_a_schedule = TaskSchedule()
        group_a_schedule.group_id = group_a.id
        group_a_schedule.name = "Group A schedule"
        self.dbsession.add(group_a_schedule)
        self.dbsession.commit()

        group_a_item = TaskScheduleItem()
        group_a_item.schedule_id = group_a_schedule.id
        group_a_item.task_table_name = "ace3"
        group_a_item.due_from = Duration(days=30)
        group_a_item.due_by = Duration(days=60)
        self.dbsession.add(group_a_item)
        self.dbsession.commit()

        self.user = User()
        self.user.upload_group_id = group_b.id
        self.user.username = "group b admin"
        self.user.set_password(self.req, "secret123")
        self.dbsession.add(self.user)
        self.dbsession.commit()
        self.req._debugging_user = self.user

        view = EditTaskScheduleItemView(self.req)
        view.object = group_a_item

        with self.assertRaises(HTTPBadRequest) as cm:
            view.get_schedule()

        self.assertIn("not a group administrator", cm.exception.message)


class DeleteTaskScheduleItemViewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def setUp(self) -> None:
        super().setUp()

        self.schedule = TaskSchedule()
        self.schedule.group_id = self.group.id
        self.schedule.name = "Test"
        self.dbsession.add(self.schedule)
        self.dbsession.commit()

        self.item = TaskScheduleItem()
        self.item.schedule_id = self.schedule.id
        self.item.task_table_name = "ace3"
        self.dbsession.add(self.item)
        self.dbsession.commit()

    def test_delete_form_displayed(self) -> None:
        view = DeleteTaskScheduleItemView(self.req)

        self.req.add_get_params(
            {ViewParam.SCHEDULE_ITEM_ID: str(self.item.id)}
        )

        response = view.dispatch()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body.decode(UTF8).count("<form"), 1)

    def test_errors_displayed_when_deletion_validation_fails(self) -> None:
        self.req.fake_request_post_from_dict({FormAction.DELETE: "delete"})

        self.req.add_get_params(
            {ViewParam.SCHEDULE_ITEM_ID: str(self.item.id)},
            set_method_get=False,
        )
        view = DeleteTaskScheduleItemView(self.req)

        response = view.dispatch()
        self.assertIn(
            "Errors have been highlighted", response.body.decode(UTF8)
        )

    def test_schedule_item_is_deleted(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                ("confirm_1_t", "true"),
                ("confirm_2_t", "true"),
                ("confirm_4_t", "true"),
                ("__start__", "danger:mapping"),
                ("target", "7176"),
                ("user_entry", "7176"),
                ("__end__", "danger:mapping"),
                ("delete", "delete"),
                (FormAction.DELETE, "delete"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.SCHEDULE_ITEM_ID: str(self.item.id)},
            set_method_get=False,
        )
        view = DeleteTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPFound) as e:
            view.dispatch()

        self.assertEqual(e.exception.status_code, 302)
        self.assertIn(
            f"{Routes.VIEW_TASK_SCHEDULE_ITEMS}"
            f"?{ViewParam.SCHEDULE_ID}={self.item.schedule_id}",
            e.exception.headers["Location"],
        )

        item = self.dbsession.query(TaskScheduleItem).one_or_none()

        self.assertIsNone(item)

    def test_schedule_item_not_deleted_on_cancel(self) -> None:
        self.req.fake_request_post_from_dict({FormAction.CANCEL: "cancel"})

        self.req.add_get_params(
            {ViewParam.SCHEDULE_ITEM_ID: str(self.item.id)},
            set_method_get=False,
        )
        view = DeleteTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        item = self.dbsession.query(TaskScheduleItem).one_or_none()

        self.assertIsNotNone(item)


class EditFinalizedPatientViewTests(BasicDatabaseTestCase):
    """
    Unit tests.
    """

    def test_raises_when_patient_does_not_exists(self) -> None:
        with self.assertRaises(HTTPBadRequest) as cm:
            edit_finalized_patient(self.req)

        self.assertEqual(
            str(cm.exception), "Cannot find Patient with _pk:None"
        )

    @unittest.skip("Can't save patient in database without group")
    def test_raises_when_patient_not_in_a_group(self) -> None:
        patient = self.create_patient(_group_id=None)

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_finalized_patient(self.req)

        self.assertEqual(str(cm.exception), "Bad patient: not in a group")

    def test_raises_when_not_authorized(self) -> None:
        patient = self.create_patient()

        self.req._debugging_user = User()

        with mock.patch.object(
            self.req._debugging_user,
            "may_administer_group",
            return_value=False,
        ):
            self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

            with self.assertRaises(HTTPBadRequest) as cm:
                edit_finalized_patient(self.req)

        self.assertEqual(
            str(cm.exception), "Not authorized to edit this patient"
        )

    def test_raises_when_patient_not_finalized(self) -> None:
        device = Device(name="Not the server device")
        self.req.dbsession.add(device)
        self.req.dbsession.commit()

        patient = self.create_patient(id=1, _device_id=device.id, _era=ERA_NOW)

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_finalized_patient(self.req)

        self.assertIn("Patient is not editable", str(cm.exception))

    def test_patient_updated(self) -> None:
        patient = self.create_patient()

        self.req.add_get_params(
            {ViewParam.SERVER_PK: str(patient.pk)}, set_method_get=False
        )

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SERVER_PK, str(patient.pk)),
                (ViewParam.GROUP_ID, str(patient.group.id)),
                (ViewParam.FORENAME, "Jo"),
                (ViewParam.SURNAME, "Patient"),
                ("__start__", "dob:mapping"),
                ("date", "1958-04-19"),
                ("__end__", "dob:mapping"),
                ("__start__", "sex:rename"),
                ("deformField7", "X"),
                ("__end__", "sex:rename"),
                (ViewParam.ADDRESS, "New address"),
                (ViewParam.EMAIL, "newjopatient@example.com"),
                (ViewParam.GP, "New GP"),
                (ViewParam.OTHER, "New other"),
                ("__start__", "id_references:sequence"),
                ("__start__", "idnum_sequence:mapping"),
                (ViewParam.WHICH_IDNUM, self.nhs_iddef.which_idnum),
                (ViewParam.IDNUM_VALUE, str(TEST_NHS_NUMBER_1)),
                ("__end__", "idnum_sequence:mapping"),
                ("__end__", "id_references:sequence"),
                ("__start__", "danger:mapping"),
                ("target", "7836"),
                ("user_entry", "7836"),
                ("__end__", "danger:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound):
            edit_finalized_patient(self.req)

        self.dbsession.commit()

        self.assertEqual(patient.forename, "Jo")
        self.assertEqual(patient.surname, "Patient")
        self.assertEqual(patient.dob.isoformat(), "1958-04-19")
        self.assertEqual(patient.sex, "X")
        self.assertEqual(patient.address, "New address")
        self.assertEqual(patient.email, "newjopatient@example.com")
        self.assertEqual(patient.gp, "New GP")
        self.assertEqual(patient.other, "New other")

        idnum = patient.get_idnum_objects()[0]
        self.assertEqual(idnum.patient_id, patient.id)
        self.assertEqual(idnum.which_idnum, self.nhs_iddef.which_idnum)
        self.assertEqual(idnum.idnum_value, TEST_NHS_NUMBER_1)

        self.assertEqual(len(patient.special_notes), 1)
        note = patient.special_notes[0].note

        self.assertIn("Patient details edited", note)
        self.assertIn("forename", note)
        self.assertIn("Jo", note)

        self.assertIn("surname", note)
        self.assertIn("Patient", note)

        self.assertIn("idnum1", note)
        self.assertIn(str(TEST_NHS_NUMBER_1), note)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)

        self.assertIn(
            f"Amended patient record with server PK {patient.pk}", messages[0]
        )
        self.assertIn("forename", messages[0])
        self.assertIn("Jo", messages[0])

        self.assertIn("surname", messages[0])
        self.assertIn("Patient", messages[0])

        self.assertIn("idnum1", messages[0])
        self.assertIn(str(TEST_NHS_NUMBER_1), messages[0])

    def test_message_when_no_changes(self) -> None:
        patient = self.create_patient(
            forename="Jo",
            surname="Patient",
            dob=datetime.date(1958, 4, 19),
            sex="F",
            address="Address",
            gp="GP",
            other="Other",
        )
        patient_idnum = self.create_patient_idnum(
            patient_id=patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER_1,
        )
        schedule1 = TaskSchedule()
        schedule1.group_id = self.group.id
        schedule1.name = "Test 1"
        self.dbsession.add(schedule1)
        self.dbsession.commit()

        patient_task_schedule = PatientTaskSchedule()
        patient_task_schedule.patient_pk = patient.pk
        patient_task_schedule.schedule_id = schedule1.id
        patient_task_schedule.start_datetime = local(2020, 6, 12, 9)
        patient_task_schedule.settings = {
            "name 1": "value 1",
            "name 2": "value 2",
            "name 3": "value 3",
        }

        self.dbsession.add(patient_task_schedule)
        self.req.add_get_params(
            {ViewParam.SERVER_PK: str(patient.pk)}, set_method_get=False
        )

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SERVER_PK, str(patient.pk)),
                (ViewParam.GROUP_ID, patient.group.id),
                (ViewParam.FORENAME, patient.forename),
                (ViewParam.SURNAME, patient.surname),
                ("__start__", "dob:mapping"),
                ("date", patient.dob.isoformat()),
                ("__end__", "dob:mapping"),
                ("__start__", "sex:rename"),
                ("deformField7", patient.sex),
                ("__end__", "sex:rename"),
                (ViewParam.ADDRESS, patient.address),
                (ViewParam.GP, patient.gp),
                (ViewParam.OTHER, patient.other),
                ("__start__", "id_references:sequence"),
                ("__start__", "idnum_sequence:mapping"),
                (ViewParam.WHICH_IDNUM, patient_idnum.which_idnum),
                (ViewParam.IDNUM_VALUE, patient_idnum.idnum_value),
                ("__end__", "idnum_sequence:mapping"),
                ("__end__", "id_references:sequence"),
                ("__start__", "danger:mapping"),
                ("target", "7836"),
                ("user_entry", "7836"),
                ("__end__", "danger:mapping"),
                ("__start__", "task_schedules:sequence"),
                ("__start__", "task_schedule_sequence:mapping"),
                ("schedule_id", schedule1.id),
                ("__start__", "start_datetime:mapping"),
                ("date", "2020-06-12"),
                ("time", "09:00:00"),
                ("__end__", "start_datetime:mapping"),
                (
                    "settings",
                    json.dumps(
                        {
                            "name 1": "value 1",
                            "name 2": "value 2",
                            "name 3": "value 3",
                        }
                    ),
                ),
                ("__end__", "task_schedule_sequence:mapping"),
                ("__end__", "task_schedules:sequence"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound):
            edit_finalized_patient(self.req)

        messages = self.req.session.peek_flash(FlashQueue.INFO)

        self.assertIn("No changes required", messages[0])

    def test_template_rendered_with_values(self) -> None:
        patient = self.create_patient(
            id=1,
            forename="Jo",
            surname="Patient",
            dob=datetime.date(1958, 4, 19),
            sex="F",
            address="Address",
            gp="GP",
            other="Other",
        )
        self.create_patient_idnum(
            patient_id=patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER_1,
        )

        from camcops_server.tasks import Bmi

        task1 = Bmi()
        task1.id = 1
        task1._device_id = patient.device_id
        task1._group_id = patient.group_id
        task1._era = patient.era
        task1.patient_id = patient.id
        task1.when_created = self.era_time
        task1._current = False
        self.dbsession.add(task1)

        task2 = Bmi()
        task2.id = 2
        task2._device_id = patient.device_id
        task2._group_id = patient.group_id
        task2._era = patient.era
        task2.patient_id = patient.id
        task2.when_created = self.era_time
        task2._current = False
        self.dbsession.add(task2)
        self.dbsession.commit()

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        view = EditFinalizedPatientView(
            self.req, task_tablename=task1.tablename, task_server_pk=task1.pk
        )
        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args

        context = args[0]

        self.assertIn("form", context)
        self.assertIn(task1, context["tasks"])
        self.assertIn(task2, context["tasks"])

    def test_changes_to_simple_params(self) -> None:
        view = EditFinalizedPatientView(self.req)
        patient = self.create_patient(
            id=1,
            forename="Jo",
            surname="Patient",
            dob=datetime.date(1958, 4, 19),
            sex="F",
            address="Address",
            email="jopatient@example.com",
            gp="GP",
            other=None,
        )
        view.object = patient

        changes = OrderedDict()  # type: OrderedDict

        appstruct = {
            ViewParam.FORENAME: "Joanna",
            ViewParam.SURNAME: "Patient-Patient",
            ViewParam.DOB: datetime.date(1958, 4, 19),
            ViewParam.ADDRESS: "New address",
            ViewParam.OTHER: "",
        }

        view._save_simple_params(appstruct, changes)

        self.assertEqual(changes[ViewParam.FORENAME], ("Jo", "Joanna"))
        self.assertEqual(
            changes[ViewParam.SURNAME], ("Patient", "Patient-Patient")
        )
        self.assertNotIn(ViewParam.DOB, changes)
        self.assertEqual(
            changes[ViewParam.ADDRESS], ("Address", "New address")
        )
        self.assertNotIn(ViewParam.OTHER, changes)

    def test_changes_to_idrefs(self) -> None:
        view = EditFinalizedPatientView(self.req)
        patient = self.create_patient(id=1)
        self.create_patient_idnum(
            patient_id=patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER_1,
        )
        self.create_patient_idnum(
            patient_id=patient.id,
            which_idnum=self.study_iddef.which_idnum,
            idnum_value=123,
        )

        view.object = patient

        changes = OrderedDict()  # type: OrderedDict

        appstruct = {
            ViewParam.ID_REFERENCES: [
                {
                    ViewParam.WHICH_IDNUM: self.nhs_iddef.which_idnum,
                    ViewParam.IDNUM_VALUE: TEST_NHS_NUMBER_2,
                },
                {
                    ViewParam.WHICH_IDNUM: self.rio_iddef.which_idnum,
                    ViewParam.IDNUM_VALUE: 456,
                },
            ]
        }

        view._save_idrefs(appstruct, changes)

        self.assertEqual(
            changes["idnum1 (NHS number)"],
            (TEST_NHS_NUMBER_1, TEST_NHS_NUMBER_2),
        )
        self.assertEqual(changes["idnum3 (Study number)"], (123, None))
        self.assertEqual(changes["idnum2 (RiO number)"], (None, 456))


class EditServerCreatedPatientViewTests(BasicDatabaseTestCase):
    """
    Unit tests.
    """

    def test_group_updated(self) -> None:
        patient = self.create_patient(sex="F", as_server_patient=True)
        new_group = Group()
        new_group.name = "newgroup"
        new_group.description = "New group"
        new_group.upload_policy = "sex AND anyidnum"
        new_group.finalize_policy = "sex AND idnum1"
        self.dbsession.add(new_group)
        self.dbsession.commit()

        view = EditServerCreatedPatientView(self.req)
        view.object = patient

        appstruct = {ViewParam.GROUP_ID: new_group.id}

        view.save_object(appstruct)

        self.assertEqual(patient.group_id, new_group.id)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)

        self.assertIn("testgroup", messages[0])
        self.assertIn("newgroup", messages[0])
        self.assertIn("group:", messages[0])

    def test_raises_when_not_created_on_the_server(self) -> None:
        patient = self.create_patient(id=1, _device_id=self.other_device.id)

        view = EditServerCreatedPatientView(self.req)

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        with self.assertRaises(HTTPBadRequest) as cm:
            view.get_object()

        self.assertIn("Patient is not editable", str(cm.exception))

    def test_patient_task_schedules_updated(self) -> None:
        patient = self.create_patient(sex="F", as_server_patient=True)

        schedule1 = TaskSchedule()
        schedule1.group_id = self.group.id
        schedule1.name = "Test 1"
        self.dbsession.add(schedule1)
        schedule2 = TaskSchedule()
        schedule2.group_id = self.group.id
        schedule2.name = "Test 2"
        self.dbsession.add(schedule2)
        schedule3 = TaskSchedule()
        schedule3.group_id = self.group.id
        schedule3.name = "Test 3"
        self.dbsession.add(schedule3)
        self.dbsession.commit()

        patient_task_schedule = PatientTaskSchedule()
        patient_task_schedule.patient_pk = patient.pk
        patient_task_schedule.schedule_id = schedule1.id
        patient_task_schedule.start_datetime = local(2020, 6, 12, 9)
        patient_task_schedule.settings = {
            "name 1": "value 1",
            "name 2": "value 2",
            "name 3": "value 3",
        }

        self.dbsession.add(patient_task_schedule)

        patient_task_schedule = PatientTaskSchedule()
        patient_task_schedule.patient_pk = patient.pk
        patient_task_schedule.schedule_id = schedule3.id

        self.dbsession.add(patient_task_schedule)
        self.dbsession.commit()

        self.req.add_get_params(
            {ViewParam.SERVER_PK: str(patient.pk)}, set_method_get=False
        )

        changed_schedule_1_settings = {
            "name 1": "new value 1",
            "name 2": "new value 2",
            "name 3": "new value 3",
        }
        new_schedule_2_settings = {
            "name 4": "value 4",
            "name 5": "value 5",
            "name 6": "value 6",
        }
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SERVER_PK, patient.pk),
                (ViewParam.GROUP_ID, patient.group.id),
                (ViewParam.FORENAME, patient.forename),
                (ViewParam.SURNAME, patient.surname),
                ("__start__", "dob:mapping"),
                ("date", ""),
                ("__end__", "dob:mapping"),
                ("__start__", "sex:rename"),
                ("deformField7", patient.sex),
                ("__end__", "sex:rename"),
                (ViewParam.ADDRESS, patient.address),
                (ViewParam.GP, patient.gp),
                (ViewParam.OTHER, patient.other),
                ("__start__", "id_references:sequence"),
                ("__start__", "idnum_sequence:mapping"),
                (ViewParam.WHICH_IDNUM, self.nhs_iddef.which_idnum),
                (ViewParam.IDNUM_VALUE, str(TEST_NHS_NUMBER_1)),
                ("__end__", "idnum_sequence:mapping"),
                ("__end__", "id_references:sequence"),
                ("__start__", "danger:mapping"),
                ("target", "7836"),
                ("user_entry", "7836"),
                ("__end__", "danger:mapping"),
                ("__start__", "task_schedules:sequence"),
                ("__start__", "task_schedule_sequence:mapping"),
                ("schedule_id", schedule1.id),
                ("__start__", "start_datetime:mapping"),
                ("date", "2020-06-19"),
                ("time", "08:00:00"),
                ("__end__", "start_datetime:mapping"),
                ("settings", json.dumps(changed_schedule_1_settings)),
                ("__end__", "task_schedule_sequence:mapping"),
                ("__start__", "task_schedule_sequence:mapping"),
                ("schedule_id", schedule2.id),
                ("__start__", "start_datetime:mapping"),
                ("date", "2020-07-01"),
                ("time", "13:45:00"),
                ("__end__", "start_datetime:mapping"),
                ("settings", json.dumps(new_schedule_2_settings)),
                ("__end__", "task_schedule_sequence:mapping"),
                ("__end__", "task_schedules:sequence"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound):
            edit_server_created_patient(self.req)

        self.dbsession.commit()

        schedules = {
            pts.task_schedule.name: pts for pts in patient.task_schedules
        }
        self.assertIn("Test 1", schedules)
        self.assertIn("Test 2", schedules)
        self.assertNotIn("Test 3", schedules)

        self.assertEqual(
            schedules["Test 1"].start_datetime, local(2020, 6, 19, 8)
        )
        self.assertEqual(
            schedules["Test 1"].settings, changed_schedule_1_settings
        )
        self.assertEqual(
            schedules["Test 2"].start_datetime, local(2020, 7, 1, 13, 45)
        )
        self.assertEqual(schedules["Test 2"].settings, new_schedule_2_settings)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)

        self.assertIn(
            f"Amended patient record with server PK {patient.pk}", messages[0]
        )
        self.assertIn("Task schedules", messages[0])

    def test_unprivileged_user_cannot_edit_patient(self) -> None:
        patient = self.create_patient(sex="F", as_server_patient=True)

        user = self.create_user(username="testuser")
        self.dbsession.flush()

        self.req._debugging_user = user

        view = EditServerCreatedPatientView(self.req)
        view.object = patient

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertEqual(
            cm.exception.message, "Not authorized to edit this patient"
        )

    def test_patient_can_be_assigned_the_same_schedule_twice(self) -> None:
        patient = self.create_patient(sex="F", as_server_patient=True)

        schedule1 = TaskSchedule()
        schedule1.group_id = self.group.id
        schedule1.name = "Test 1"
        self.dbsession.add(schedule1)
        self.dbsession.flush()

        pts = PatientTaskSchedule()
        pts.patient_pk = patient.pk
        pts.schedule_id = schedule1.id
        pts.start_datetime = local(2020, 6, 12, 12, 34)
        self.dbsession.add(pts)
        self.dbsession.commit()

        appstruct = {
            ViewParam.TASK_SCHEDULES: [
                {
                    ViewParam.PATIENT_TASK_SCHEDULE_ID: pts.id,
                    ViewParam.SCHEDULE_ID: schedule1.id,
                    ViewParam.START_DATETIME: local(2020, 6, 12, 12, 34),
                    ViewParam.SETTINGS: {},
                },
                {
                    ViewParam.PATIENT_TASK_SCHEDULE_ID: None,
                    ViewParam.SCHEDULE_ID: schedule1.id,
                    ViewParam.START_DATETIME: None,
                    ViewParam.SETTINGS: {},
                },
            ]
        }

        view = EditServerCreatedPatientView(self.req)
        view.object = patient

        changes = {}
        view._save_task_schedules(appstruct, changes)
        self.req.dbsession.commit()

        self.assertEqual(patient.task_schedules[0].task_schedule, schedule1)
        self.assertEqual(patient.task_schedules[1].task_schedule, schedule1)

    def test_form_values_for_existing_patient(self) -> None:
        patient = self.create_patient(
            id=1,
            forename="Jo",
            surname="Patient",
            dob=datetime.date(1958, 4, 19),
            sex="F",
            address="Address",
            email="jopatient@example.com",
            gp="GP",
            other="Other",
        )

        schedule1 = TaskSchedule()
        schedule1.group_id = self.group.id
        schedule1.name = "Test 1"
        self.dbsession.add(schedule1)
        self.dbsession.commit()

        patient_task_schedule = PatientTaskSchedule()
        patient_task_schedule.patient_pk = patient.pk
        patient_task_schedule.schedule_id = schedule1.id
        patient_task_schedule.start_datetime = local(2020, 6, 12)
        patient_task_schedule.settings = {
            "name 1": "value 1",
            "name 2": "value 2",
            "name 3": "value 3",
        }

        self.dbsession.add(patient_task_schedule)
        self.dbsession.commit()

        self.create_patient_idnum(
            patient_id=patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER_1,
        )

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        view = EditServerCreatedPatientView(self.req)
        view.object = patient

        form_values = view.get_form_values()

        self.assertEqual(form_values[ViewParam.FORENAME], "Jo")
        self.assertEqual(form_values[ViewParam.SURNAME], "Patient")
        self.assertEqual(
            form_values[ViewParam.DOB], datetime.date(1958, 4, 19)
        )
        self.assertEqual(form_values[ViewParam.SEX], "F")
        self.assertEqual(form_values[ViewParam.ADDRESS], "Address")
        self.assertEqual(form_values[ViewParam.EMAIL], "jopatient@example.com")
        self.assertEqual(form_values[ViewParam.GP], "GP")
        self.assertEqual(form_values[ViewParam.OTHER], "Other")

        self.assertEqual(form_values[ViewParam.SERVER_PK], patient.pk)
        self.assertEqual(form_values[ViewParam.GROUP_ID], patient.group.id)

        idnum = form_values[ViewParam.ID_REFERENCES][0]
        self.assertEqual(
            idnum[ViewParam.WHICH_IDNUM], self.nhs_iddef.which_idnum
        )
        self.assertEqual(idnum[ViewParam.IDNUM_VALUE], TEST_NHS_NUMBER_1)

        task_schedule = form_values[ViewParam.TASK_SCHEDULES][0]
        self.assertEqual(
            task_schedule[ViewParam.PATIENT_TASK_SCHEDULE_ID],
            patient_task_schedule.id,
        )
        self.assertEqual(
            task_schedule[ViewParam.SCHEDULE_ID],
            patient_task_schedule.schedule_id,
        )
        self.assertEqual(
            task_schedule[ViewParam.START_DATETIME],
            patient_task_schedule.start_datetime,
        )
        self.assertEqual(
            task_schedule[ViewParam.SETTINGS], patient_task_schedule.settings
        )


class AddPatientViewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def test_patient_created(self) -> None:
        view = AddPatientView(self.req)

        schedule1 = TaskSchedule()
        schedule1.group_id = self.group.id
        schedule1.name = "Test 1"
        self.dbsession.add(schedule1)

        schedule2 = TaskSchedule()
        schedule2.group_id = self.group.id
        schedule2.name = "Test 2"
        self.dbsession.add(schedule2)
        self.dbsession.commit()

        start_datetime1 = local(2020, 6, 12)
        start_datetime2 = local(2020, 7, 1)

        settings1 = json.dumps(
            {"name 1": "value 1", "name 2": "value 2", "name 3": "value 3"}
        )

        appstruct = {
            ViewParam.GROUP_ID: self.group.id,
            ViewParam.FORENAME: "Jo",
            ViewParam.SURNAME: "Patient",
            ViewParam.DOB: datetime.date(1958, 4, 19),
            ViewParam.SEX: "F",
            ViewParam.ADDRESS: "Address",
            ViewParam.EMAIL: "jopatient@example.com",
            ViewParam.GP: "GP",
            ViewParam.OTHER: "Other",
            ViewParam.ID_REFERENCES: [
                {
                    ViewParam.WHICH_IDNUM: self.nhs_iddef.which_idnum,
                    ViewParam.IDNUM_VALUE: 1192220552,
                }
            ],
            ViewParam.TASK_SCHEDULES: [
                {
                    ViewParam.SCHEDULE_ID: schedule1.id,
                    ViewParam.START_DATETIME: start_datetime1,
                    ViewParam.SETTINGS: settings1,
                },
                {
                    ViewParam.SCHEDULE_ID: schedule2.id,
                    ViewParam.START_DATETIME: start_datetime2,
                    ViewParam.SETTINGS: {},
                },
            ],
        }

        view.save_object(appstruct)

        patient = cast(Patient, view.object)

        server_device = Device.get_server_device(self.req.dbsession)

        self.assertEqual(patient.id, 1)
        self.assertEqual(patient.device_id, server_device.id)
        self.assertEqual(patient.era, ERA_NOW)
        self.assertEqual(patient.group.id, self.group.id)

        self.assertEqual(patient.forename, "Jo")
        self.assertEqual(patient.surname, "Patient")
        self.assertEqual(patient.dob.isoformat(), "1958-04-19")
        self.assertEqual(patient.sex, "F")
        self.assertEqual(patient.address, "Address")
        self.assertEqual(patient.email, "jopatient@example.com")
        self.assertEqual(patient.gp, "GP")
        self.assertEqual(patient.other, "Other")

        idnum = patient.get_idnum_objects()[0]
        self.assertEqual(idnum.patient_id, 1)
        self.assertEqual(idnum.which_idnum, self.nhs_iddef.which_idnum)
        self.assertEqual(idnum.idnum_value, 1192220552)

        patient_task_schedules = {
            pts.task_schedule.name: pts for pts in patient.task_schedules
        }

        self.assertIn("Test 1", patient_task_schedules)
        self.assertIn("Test 2", patient_task_schedules)

        self.assertEqual(
            patient_task_schedules["Test 1"].start_datetime, start_datetime1
        )
        self.assertEqual(patient_task_schedules["Test 1"].settings, settings1)
        self.assertEqual(
            patient_task_schedules["Test 2"].start_datetime, start_datetime2
        )

    def test_patient_takes_next_available_id(self) -> None:
        self.create_patient(id=1234, as_server_patient=True)

        view = AddPatientView(self.req)

        appstruct = {
            ViewParam.GROUP_ID: self.group.id,
            ViewParam.FORENAME: "Jo",
            ViewParam.SURNAME: "Patient",
            ViewParam.DOB: datetime.date(1958, 4, 19),
            ViewParam.SEX: "F",
            ViewParam.ADDRESS: "Address",
            ViewParam.GP: "GP",
            ViewParam.OTHER: "Other",
            ViewParam.ID_REFERENCES: [
                {
                    ViewParam.WHICH_IDNUM: self.nhs_iddef.which_idnum,
                    ViewParam.IDNUM_VALUE: 1192220552,
                }
            ],
            ViewParam.TASK_SCHEDULES: [],
        }

        view.save_object(appstruct)

        patient = cast(Patient, view.object)

        self.assertEqual(patient.id, 1235)

    def test_form_rendered_with_values(self) -> None:
        view = AddPatientView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args

        context = args[0]

        self.assertIn("form", context)

    def test_unprivileged_user_cannot_add_patient(self) -> None:
        user = self.create_user(username="testuser")
        self.dbsession.flush()

        self.req._debugging_user = user

        with self.assertRaises(HTTPBadRequest) as cm:
            add_patient(self.req)

        self.assertEqual(
            cm.exception.message, "Not authorized to manage patients"
        )

    def test_group_listed_for_privileged_group_member(self) -> None:
        user = self.create_user(username="testuser")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_manage_patients=True)
        self.dbsession.commit()

        self.req._debugging_user = user

        view = AddPatientView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args

        context = args[0]

        self.assertIn("testgroup", context["form"])


class DeleteServerCreatedPatientViewTests(BasicDatabaseTestCase):
    """
    Unit tests.
    """

    def setUp(self) -> None:
        super().setUp()

        self.patient = self.create_patient(
            as_server_patient=True,
            forename="Jo",
            surname="Patient",
            dob=datetime.date(1958, 4, 19),
            sex="F",
            address="Address",
            gp="GP",
            other="Other",
        )

        patient_pk = self.patient.pk

        idnum = self.create_patient_idnum(
            as_server_patient=True,
            patient_id=self.patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER_1,
        )

        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)

        self.schedule = TaskSchedule()
        self.schedule.group_id = self.group.id
        self.schedule.name = "Test 1"
        self.dbsession.add(self.schedule)
        self.dbsession.commit()

        pts = PatientTaskSchedule()
        pts.patient_pk = patient_pk
        pts.schedule_id = self.schedule.id
        self.dbsession.add(pts)
        self.dbsession.commit()

        self.multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                ("confirm_1_t", "true"),
                ("confirm_2_t", "true"),
                ("confirm_4_t", "true"),
                ("__start__", "danger:mapping"),
                ("target", "7176"),
                ("user_entry", "7176"),
                ("__end__", "danger:mapping"),
                ("delete", "delete"),
                (FormAction.DELETE, "delete"),
            ]
        )

    def test_patient_schedule_and_idnums_deleted(self) -> None:
        self.req.fake_request_post_from_dict(self.multidict)

        patient_pk = self.patient.pk
        self.req.add_get_params(
            {ViewParam.SERVER_PK: str(patient_pk)}, set_method_get=False
        )
        view = DeleteServerCreatedPatientView(self.req)

        with self.assertRaises(HTTPFound) as e:
            view.dispatch()

        self.assertEqual(e.exception.status_code, 302)
        self.assertIn(
            Routes.VIEW_PATIENT_TASK_SCHEDULES, e.exception.headers["Location"]
        )

        deleted_patient = (
            self.dbsession.query(Patient)
            .filter(Patient._pk == patient_pk)
            .one_or_none()
        )

        self.assertIsNone(deleted_patient)

        pts = (
            self.dbsession.query(PatientTaskSchedule)
            .filter(PatientTaskSchedule.patient_pk == patient_pk)
            .one_or_none()
        )

        self.assertIsNone(pts)

        idnum = (
            self.dbsession.query(PatientIdNum)
            .filter(
                PatientIdNum.patient_id == self.patient.id,
                PatientIdNum._device_id == self.patient.device_id,
                PatientIdNum._era == self.patient.era,
                PatientIdNum._current == True,  # noqa: E712
            )
            .one_or_none()
        )

        self.assertIsNone(idnum)

    def test_registered_patient_deleted(self) -> None:
        from camcops_server.cc_modules.client_api import (
            get_or_create_single_user,
        )

        user1, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.assertEqual(user1.single_patient, self.patient)

        user2, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.assertEqual(user2.single_patient, self.patient)

        self.req.fake_request_post_from_dict(self.multidict)

        patient_pk = self.patient.pk
        self.req.add_get_params(
            {ViewParam.SERVER_PK: str(patient_pk)}, set_method_get=False
        )
        view = DeleteServerCreatedPatientView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        self.dbsession.commit()

        deleted_patient = (
            self.dbsession.query(Patient)
            .filter(Patient._pk == patient_pk)
            .one_or_none()
        )

        self.assertIsNone(deleted_patient)

        # TODO: We get weird behaviour when all the tests are run together
        # (fine for --test_class=DeleteServerCreatedPatientViewTests)
        # the assertion below fails with sqlite in spite of the commit()
        # above.

        # user = self.dbsession.query(User).filter(
        #     User.id == user1.id).one_or_none()
        # self.assertIsNone(user.single_patient_pk)

        # user = self.dbsession.query(User).filter(
        #     User.id == user2.id).one_or_none()
        # self.assertIsNone(user.single_patient_pk)

    def test_unrelated_patient_unaffected(self) -> None:
        other_patient = self.create_patient(
            as_server_patient=True,
            forename="Mo",
            surname="Patient",
            dob=datetime.date(1968, 11, 30),
            sex="M",
            address="Address",
            gp="GP",
            other="Other",
        )
        patient_pk = other_patient._pk

        saved_patient = (
            self.dbsession.query(Patient)
            .filter(Patient._pk == patient_pk)
            .one_or_none()
        )

        self.assertIsNotNone(saved_patient)

        idnum = self.create_patient_idnum(
            as_server_patient=True,
            patient_id=other_patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER_2,
        )

        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)

        saved_idnum = (
            self.dbsession.query(PatientIdNum)
            .filter(
                PatientIdNum.patient_id == other_patient.id,
                PatientIdNum._device_id == other_patient.device_id,
                PatientIdNum._era == other_patient.era,
                PatientIdNum._current == True,  # noqa: E712
            )
            .one_or_none()
        )

        self.assertIsNotNone(saved_idnum)

        pts = PatientTaskSchedule()
        pts.patient_pk = patient_pk
        pts.schedule_id = self.schedule.id
        self.dbsession.add(pts)
        self.dbsession.commit()

        self.req.fake_request_post_from_dict(self.multidict)

        self.req.add_get_params(
            {ViewParam.SERVER_PK: self.patient._pk}, set_method_get=False
        )
        view = DeleteServerCreatedPatientView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        saved_patient = (
            self.dbsession.query(Patient)
            .filter(Patient._pk == patient_pk)
            .one_or_none()
        )

        self.assertIsNotNone(saved_patient)

        saved_pts = (
            self.dbsession.query(PatientTaskSchedule)
            .filter(PatientTaskSchedule.patient_pk == patient_pk)
            .one_or_none()
        )

        self.assertIsNotNone(saved_pts)

        saved_idnum = (
            self.dbsession.query(PatientIdNum)
            .filter(
                PatientIdNum.patient_id == other_patient.id,
                PatientIdNum._device_id == other_patient.device_id,
                PatientIdNum._era == other_patient.era,
                PatientIdNum._current == True,  # noqa: E712
            )
            .one_or_none()
        )

        self.assertIsNotNone(saved_idnum)

    def test_unprivileged_user_cannot_delete_patient(self) -> None:
        self.req.fake_request_post_from_dict(self.multidict)

        patient_pk = self.patient.pk
        self.req.add_get_params(
            {ViewParam.SERVER_PK: str(patient_pk)}, set_method_get=False
        )
        view = DeleteServerCreatedPatientView(self.req)

        user = self.create_user(username="testuser")
        self.dbsession.flush()

        self.req._debugging_user = user

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertEqual(
            cm.exception.message, "Not authorized to delete this patient"
        )

    def test_unprivileged_user_cannot_see_delete_form(self) -> None:
        self.req.fake_request_post_from_dict(self.multidict)

        patient_pk = self.patient.pk
        self.req.add_get_params({ViewParam.SERVER_PK: str(patient_pk)})
        view = DeleteServerCreatedPatientView(self.req)

        user = self.create_user(username="testuser")
        self.dbsession.flush()

        self.req._debugging_user = user

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertEqual(
            cm.exception.message, "Not authorized to delete this patient"
        )


class EraseTaskTestCase(BasicDatabaseTestCase):
    """
    Unit tests.
    """

    def create_tasks(self) -> None:
        from camcops_server.tasks.bmi import Bmi

        self.task = Bmi()
        self.task.id = 1
        self.apply_standard_task_fields(self.task)
        patient = self.create_patient_with_one_idnum()
        self.task.patient_id = patient.id

        self.dbsession.add(self.task)
        self.dbsession.commit()


class EraseTaskLeavingPlaceholderViewTests(EraseTaskTestCase):
    """
    Unit tests.
    """

    def test_displays_form(self) -> None:
        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(self.task.pk),
                ViewParam.TABLE_NAME: self.task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)

    def test_deletes_task_leaving_placeholder(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SERVER_PK, self.task.pk),
                (ViewParam.TABLE_NAME, self.task.tablename),
                ("confirm_1_t", "true"),
                ("confirm_2_t", "true"),
                ("confirm_4_t", "true"),
                ("__start__", "danger:mapping"),
                ("target", "7176"),
                ("user_entry", "7176"),
                ("__end__", "danger:mapping"),
                ("delete", "delete"),
                (FormAction.DELETE, "delete"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = EraseTaskLeavingPlaceholderView(self.req)
        with mock.patch.object(
            self.task, "manually_erase"
        ) as mock_manually_erase:

            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_manually_erase.assert_called_once()
        args, kwargs = mock_manually_erase.call_args
        request = args[0]

        self.assertEqual(request, self.req)

    def test_task_not_deleted_on_cancel(self) -> None:
        self.req.fake_request_post_from_dict({FormAction.CANCEL: "cancel"})

        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(self.task.pk),
                ViewParam.TABLE_NAME: self.task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        task = self.dbsession.query(self.task.__class__).one_or_none()

        self.assertIsNotNone(task)

    def test_redirect_on_cancel(self) -> None:
        self.req.fake_request_post_from_dict({FormAction.CANCEL: "cancel"})

        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(self.task.pk),
                ViewParam.TABLE_NAME: self.task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPFound) as cm:
            view.dispatch()

        self.assertEqual(cm.exception.status_code, 302)
        self.assertIn(f"/{Routes.TASK}", cm.exception.headers["Location"])
        self.assertIn(
            f"{ViewParam.TABLE_NAME}={self.task.tablename}",
            cm.exception.headers["Location"],
        )
        self.assertIn(
            f"{ViewParam.SERVER_PK}={self.task.pk}",
            cm.exception.headers["Location"],
        )
        self.assertIn(
            f"{ViewParam.VIEWTYPE}={ViewArg.HTML}",
            cm.exception.headers["Location"],
        )

    def test_raises_when_task_does_not_exist(self) -> None:
        self.req.add_get_params(
            {ViewParam.SERVER_PK: "123", ViewParam.TABLE_NAME: "phq9"},
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertEqual(cm.exception.message, "No such task: phq9, PK=123")

    def test_raises_when_task_is_live_on_tablet(self) -> None:
        self.task._era = ERA_NOW
        self.dbsession.add(self.task)
        self.dbsession.commit()

        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(self.task.pk),
                ViewParam.TABLE_NAME: self.task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("Task is live on tablet", cm.exception.message)

    def test_raises_when_user_not_authorized_to_erase(self) -> None:
        with mock.patch.object(
            self.user, "authorized_to_erase_tasks", return_value=False
        ):

            self.req.add_get_params(
                {
                    ViewParam.SERVER_PK: str(self.task.pk),
                    ViewParam.TABLE_NAME: self.task.tablename,
                },
                set_method_get=False,
            )
            view = EraseTaskLeavingPlaceholderView(self.req)

            with self.assertRaises(HTTPBadRequest) as cm:
                view.dispatch()

        self.assertIn("Not authorized to erase tasks", cm.exception.message)

    def test_raises_when_task_already_erased(self) -> None:
        self.task._manually_erased = True
        self.dbsession.add(self.task)
        self.dbsession.commit()

        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(self.task.pk),
                ViewParam.TABLE_NAME: self.task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("already erased", cm.exception.message)


class EraseTaskEntirelyViewTests(EraseTaskTestCase):
    """
    Unit tests.
    """

    def test_deletes_task_entirely(self) -> None:
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SERVER_PK, self.task.pk),
                (ViewParam.TABLE_NAME, self.task.tablename),
                ("confirm_1_t", "true"),
                ("confirm_2_t", "true"),
                ("confirm_4_t", "true"),
                ("__start__", "danger:mapping"),
                ("target", "7176"),
                ("user_entry", "7176"),
                ("__end__", "danger:mapping"),
                ("delete", "delete"),
                (FormAction.DELETE, "delete"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = EraseTaskEntirelyView(self.req)

        with mock.patch.object(
            self.task, "delete_entirely"
        ) as mock_delete_entirely:

            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_delete_entirely.assert_called_once()
        args, kwargs = mock_delete_entirely.call_args
        request = args[0]

        self.assertEqual(request, self.req)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)
        self.assertTrue(len(messages) > 0)

        self.assertIn("Task erased", messages[0])
        self.assertIn(self.task.tablename, messages[0])
        self.assertIn("server PK {}".format(self.task.pk), messages[0])


class EditGroupViewTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def test_group_updated(self) -> None:
        other_group_1 = Group()
        other_group_1.name = "other-group-1"
        self.dbsession.add(other_group_1)

        other_group_2 = Group()
        other_group_2.name = "other-group-2"
        self.dbsession.add(other_group_2)

        self.dbsession.commit()

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.GROUP_ID, self.group.id),
                (ViewParam.NAME, "new-name"),
                (ViewParam.DESCRIPTION, "new description"),
                (ViewParam.UPLOAD_POLICY, "anyidnum AND sex"),  # reversed
                (ViewParam.FINALIZE_POLICY, "idnum1 AND sex"),  # reversed
                ("__start__", "group_ids:sequence"),
                ("group_id_sequence", str(other_group_1.id)),
                ("group_id_sequence", str(other_group_2.id)),
                ("__end__", "group_ids:sequence"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound):
            edit_group(self.req)

        self.assertEqual(self.group.name, "new-name")
        self.assertEqual(self.group.description, "new description")
        self.assertEqual(self.group.upload_policy, "anyidnum AND sex")
        self.assertEqual(self.group.finalize_policy, "idnum1 AND sex")
        self.assertIn(other_group_1, self.group.can_see_other_groups)
        self.assertIn(other_group_2, self.group.can_see_other_groups)

    def test_ip_use_added(self) -> None:
        from camcops_server.cc_modules.cc_ipuse import IpContexts

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.GROUP_ID, self.group.id),
                (ViewParam.NAME, "new-name"),
                (ViewParam.DESCRIPTION, "new description"),
                (ViewParam.UPLOAD_POLICY, "anyidnum AND sex"),
                (ViewParam.FINALIZE_POLICY, "idnum1 AND sex"),
                ("__start__", "ip_use:mapping"),
                (IpContexts.CLINICAL, "true"),
                (IpContexts.COMMERCIAL, "true"),
                ("__end__", "ip_use:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound):
            edit_group(self.req)

        self.assertTrue(self.group.ip_use.clinical)
        self.assertTrue(self.group.ip_use.commercial)
        self.assertFalse(self.group.ip_use.educational)
        self.assertFalse(self.group.ip_use.research)

    def test_ip_use_updated(self) -> None:
        from camcops_server.cc_modules.cc_ipuse import IpContexts

        self.group.ip_use.educational = True
        self.group.ip_use.research = True
        self.dbsession.add(self.group.ip_use)
        self.dbsession.commit()

        old_id = self.group.ip_use.id

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.GROUP_ID, self.group.id),
                (ViewParam.NAME, "new-name"),
                (ViewParam.DESCRIPTION, "new description"),
                (ViewParam.UPLOAD_POLICY, "anyidnum AND sex"),
                (ViewParam.FINALIZE_POLICY, "idnum1 AND sex"),
                ("__start__", "ip_use:mapping"),
                (IpContexts.CLINICAL, "true"),
                (IpContexts.COMMERCIAL, "true"),
                ("__end__", "ip_use:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound):
            edit_group(self.req)

        self.assertTrue(self.group.ip_use.clinical)
        self.assertTrue(self.group.ip_use.commercial)
        self.assertFalse(self.group.ip_use.educational)
        self.assertFalse(self.group.ip_use.research)
        self.assertEqual(self.group.ip_use.id, old_id)

    def test_other_groups_displayed_in_form(self) -> None:
        z_group = Group()
        z_group.name = "z-group"
        self.dbsession.add(z_group)

        a_group = Group()
        a_group.name = "a-group"
        self.dbsession.add(a_group)
        self.dbsession.commit()

        other_groups = Group.get_groups_from_id_list(
            self.dbsession, [z_group.id, a_group.id]
        )
        self.group.can_see_other_groups = other_groups

        self.dbsession.add(self.group)
        self.dbsession.commit()

        view = EditGroupView(self.req)
        view.object = self.group

        form_values = view.get_form_values()

        self.assertEqual(
            form_values[ViewParam.GROUP_IDS], [a_group.id, z_group.id]
        )

    def test_group_id_displayed_in_form(self) -> None:
        view = EditGroupView(self.req)
        view.object = self.group

        form_values = view.get_form_values()

        self.assertEqual(form_values[ViewParam.GROUP_ID], self.group.id)

    def test_ip_use_displayed_in_form(self) -> None:
        view = EditGroupView(self.req)
        view.object = self.group

        form_values = view.get_form_values()

        self.assertEqual(form_values[ViewParam.IP_USE], self.group.ip_use)


class SendEmailFromPatientTaskScheduleViewTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patient = self.create_patient(
            as_server_patient=True,
            forename="Jo",
            surname="Patient",
            dob=datetime.date(1958, 4, 19),
            sex="F",
            address="Address",
            gp="GP",
            other="Other",
        )

        patient_pk = self.patient.pk

        idnum = self.create_patient_idnum(
            as_server_patient=True,
            patient_id=self.patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER_1,
        )

        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)

        self.schedule = TaskSchedule()
        self.schedule.group_id = self.group.id
        self.schedule.name = "Test 1"
        self.dbsession.add(self.schedule)
        self.dbsession.commit()

        self.pts = PatientTaskSchedule()
        self.pts.patient_pk = patient_pk
        self.pts.schedule_id = self.schedule.id
        self.dbsession.add(self.pts)
        self.dbsession.commit()

    def test_displays_form(self) -> None:
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(self.pts.id)}
        )

        view = SendEmailFromPatientTaskScheduleView(self.req)
        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)

    def test_raises_for_missing_pts_id(self) -> None:
        view = SendEmailFromPatientTaskScheduleView(self.req)
        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn(
            "Patient task schedule does not exist", cm.exception.message
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_sends_email(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        self.req.config.email_host = "smtp.example.com"
        self.req.config.email_port = 587
        self.req.config.email_host_username = "mailuser"
        self.req.config.email_host_password = "mailpassword"
        self.req.config.email_use_tls = True

        multidict = MultiDict(
            [
                (ViewParam.EMAIL, "patient@example.com"),
                (ViewParam.EMAIL_FROM, "server@example.com"),
                (ViewParam.EMAIL_SUBJECT, "Subject"),
                (ViewParam.EMAIL_BODY, "Email body"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(self.pts.id)},
            set_method_get=False,
        )
        view = SendEmailFromPatientTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        args, kwargs = mock_make_email.call_args_list[0]
        self.assertEqual(kwargs["from_addr"], "server@example.com")
        self.assertEqual(kwargs["to"], "patient@example.com")
        self.assertEqual(kwargs["subject"], "Subject")
        self.assertEqual(kwargs["body"], "Email body")
        self.assertEqual(kwargs["content_type"], MimeType.HTML)

        args, kwargs = mock_send_msg.call_args
        self.assertEqual(kwargs["host"], "smtp.example.com")
        self.assertEqual(kwargs["user"], "mailuser")
        self.assertEqual(kwargs["password"], "mailpassword")
        self.assertEqual(kwargs["port"], 587)
        self.assertTrue(kwargs["use_tls"])

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_sends_cc_of_email(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        self.req.config.email_host = "smtp.example.com"
        self.req.config.email_port = 587
        self.req.config.email_host_username = "mailuser"
        self.req.config.email_host_password = "mailpassword"
        self.req.config.email_use_tls = True

        multidict = MultiDict(
            [
                (ViewParam.EMAIL, "patient@example.com"),
                (ViewParam.EMAIL_CC, "cc@example.com"),
                (ViewParam.EMAIL_FROM, "server@example.com"),
                (ViewParam.EMAIL_SUBJECT, "Subject"),
                (ViewParam.EMAIL_BODY, "Email body"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(self.pts.id)},
            set_method_get=False,
        )
        view = SendEmailFromPatientTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        args, kwargs = mock_make_email.call_args
        self.assertEqual(kwargs["to"], "patient@example.com")
        self.assertEqual(kwargs["cc"], "cc@example.com")

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_sends_bcc_of_email(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        self.req.config.email_host = "smtp.example.com"
        self.req.config.email_port = 587
        self.req.config.email_host_username = "mailuser"
        self.req.config.email_host_password = "mailpassword"
        self.req.config.email_use_tls = True

        multidict = MultiDict(
            [
                (ViewParam.EMAIL, "patient@example.com"),
                (ViewParam.EMAIL_CC, "cc@example.com"),
                (ViewParam.EMAIL_BCC, "bcc@example.com"),
                (ViewParam.EMAIL_FROM, "server@example.com"),
                (ViewParam.EMAIL_SUBJECT, "Subject"),
                (ViewParam.EMAIL_BODY, "Email body"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(self.pts.id)},
            set_method_get=False,
        )
        view = SendEmailFromPatientTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        args, kwargs = mock_make_email.call_args
        self.assertEqual(kwargs["to"], "patient@example.com")
        self.assertEqual(kwargs["bcc"], "bcc@example.com")

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_message_on_success(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        multidict = MultiDict(
            [
                (ViewParam.EMAIL, "patient@example.com"),
                (ViewParam.EMAIL_FROM, "server@example.com"),
                (ViewParam.EMAIL_SUBJECT, "Subject"),
                (ViewParam.EMAIL_BODY, "Email body"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(self.pts.id)},
            set_method_get=False,
        )
        view = SendEmailFromPatientTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)
        self.assertTrue(len(messages) > 0)

        self.assertIn("Email sent to patient@example.com", messages[0])

    @mock.patch(
        "camcops_server.cc_modules.cc_email.send_msg",
        side_effect=RuntimeError("Something bad happened"),
    )
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_message_on_failure(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        multidict = MultiDict(
            [
                (ViewParam.EMAIL, "patient@example.com"),
                (ViewParam.EMAIL_FROM, "server@example.com"),
                (ViewParam.EMAIL_SUBJECT, "Subject"),
                (ViewParam.EMAIL_BODY, "Email body"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(self.pts.id)},
            set_method_get=False,
        )
        view = SendEmailFromPatientTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        messages = self.req.session.peek_flash(FlashQueue.DANGER)
        self.assertTrue(len(messages) > 0)

        self.assertIn(
            "Failed to send email to patient@example.com", messages[0]
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_email_record_created(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        multidict = MultiDict(
            [
                (ViewParam.EMAIL, "patient@example.com"),
                (ViewParam.EMAIL_FROM, "server@example.com"),
                (ViewParam.EMAIL_SUBJECT, "Subject"),
                (ViewParam.EMAIL_BODY, "Email body"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(self.pts.id)},
            set_method_get=False,
        )
        view = SendEmailFromPatientTaskScheduleView(self.req)

        self.assertEqual(len(self.pts.emails), 0)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        self.assertEqual(len(self.pts.emails), 1)
        self.assertEqual(self.pts.emails[0].email.to, "patient@example.com")

    def test_unprivileged_user_cannot_email_patient(self) -> None:
        user = self.create_user(username="testuser")
        self.dbsession.flush()

        self.req._debugging_user = user

        multidict = MultiDict(
            [
                (ViewParam.EMAIL, "patient@example.com"),
                (ViewParam.EMAIL_FROM, "server@example.com"),
                (ViewParam.EMAIL_SUBJECT, "Subject"),
                (ViewParam.EMAIL_BODY, "Email body"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(self.pts.id)},
            set_method_get=False,
        )

        with self.assertRaises(HTTPBadRequest) as cm:
            view = SendEmailFromPatientTaskScheduleView(self.req)
            view.dispatch()

        self.assertEqual(
            cm.exception.message, "Not authorized to email patients"
        )


class LoginViewTests(TestStateMixin, BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.req.matched_route.name = "login_view"

    def test_form_rendered_with_values(self) -> None:
        self.req.add_get_params(
            {ViewParam.REDIRECT_URL: "https://www.example.com"}
        )
        view = LoginView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)
        self.assertIn("https://www.example.com", context["form"])

    def test_template_rendered(self) -> None:
        view = LoginView(self.req)
        response = view.dispatch()

        self.assertIn("Log in", response.body.decode(UTF8))

    def test_password_autocomplete_read_from_config(self) -> None:
        self.req.config.disable_password_autocomplete = False

        view = LoginView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn('autocomplete="current-password"', context["form"])

    def test_fails_when_user_locked_out(self) -> None:
        user = self.create_user(username="test")
        user.set_password(self.req, "secret")
        SecurityAccountLockout.lock_user_out(
            self.req, user.username, lockout_minutes=1
        )

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, user.username),
                (ViewParam.PASSWORD, "secret"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)

        with mock.patch.object(
            view, "fail_locked_out", side_effect=HTTPFound
        ) as mock_fail_locked_out:
            with self.assertRaises(HTTPFound):
                view.dispatch()

        args, kwargs = mock_fail_locked_out.call_args
        locked_out_until = SecurityAccountLockout.user_locked_out_until(
            self.req, user.username
        )
        self.assertEqual(args[0], locked_out_until)

    @mock.patch("camcops_server.cc_modules.webview.audit")
    def test_user_can_log_in(self, mock_audit: mock.Mock) -> None:
        user = self.create_user(username="test")
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, user.username),
                (ViewParam.PASSWORD, "secret"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)

        with mock.patch.object(user, "login") as mock_user_login:
            with mock.patch.object(
                self.req.camcops_session, "login"
            ) as mock_session_login:
                with self.assertRaises(HTTPFound):
                    view.dispatch()

        args, kwargs = mock_user_login.call_args
        self.assertEqual(args[0], self.req)

        args, kwargs = mock_session_login.call_args
        self.assertEqual(args[0], user)

        args, kwargs = mock_audit.call_args
        self.assertEqual(args[0], self.req)
        self.assertEqual(args[1], "Login")
        self.assertEqual(kwargs["user_id"], user.id)

    def test_user_with_totp_sees_token_form(self) -> None:
        user = self.create_user(
            username="test",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.TOTP,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        view = LoginView(self.req)
        view.state.update(
            mfa_user_id=user.id,
            step=MfaMixin.STEP_MFA,
            mfa_time=int(time.time()),
        )

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)
        self.assertIn("Enter the six-digit code", context["form"])
        self.assertIn(
            "Enter the code for CamCOPS displayed",
            context[MfaMixin.KEY_INSTRUCTIONS],
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_user_with_hotp_email_sees_token_form(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        user = self.create_user(
            username="test",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_EMAIL,
            email="user@example.com",
            hotp_counter=0,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)
        view = LoginView(self.req)
        view.state.update(
            mfa_user_id=user.id,
            step=MfaMixin.STEP_MFA,
            mfa_time=int(time.time()),
        )

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)
        self.assertIn("Enter the six-digit code", context["form"])
        self.assertIn(
            "We've sent a code by email", context[MfaMixin.KEY_INSTRUCTIONS]
        )

    def test_user_with_hotp_sms_sees_token_form(self) -> None:
        self.req.config.sms_backend = get_sms_backend(
            SmsBackendNames.CONSOLE, {}
        )

        phone_number = phonenumbers.parse(TEST_PHONE_NUMBER)
        user = self.create_user(
            username="test",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            phone_number=phone_number,
            hotp_counter=0,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        view = LoginView(self.req)
        view.state.update(
            mfa_user_id=user.id,
            step=MfaMixin.STEP_MFA,
            mfa_time=int(time.time()),
        )

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)
        self.assertIn("Enter the six-digit code", context["form"])
        self.assertIn(
            "We've sent a code by text message",
            context[MfaMixin.KEY_INSTRUCTIONS],
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    @mock.patch("camcops_server.cc_modules.webview.time")
    def test_session_state_set_for_user_with_mfa(
        self,
        mock_time: mock.Mock,
        mock_make_email: mock.Mock,
        mock_send_msg: mock.Mock,
    ) -> None:
        user = self.create_user(
            username="test",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_EMAIL,
            email="user@example.com",
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, user.username),
                (ViewParam.PASSWORD, "secret"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)

        with mock.patch.object(
            mock_time, "time", return_value=1234567890.1234567
        ):
            view.dispatch()

        self.assertEqual(
            self.req.camcops_session.form_state[LoginView.KEY_MFA_USER_ID],
            user.id,
        )
        self.assertEqual(
            self.req.camcops_session.form_state[MfaMixin.KEY_MFA_TIME],
            1234567890,
        )
        self.assertEqual(
            self.req.camcops_session.form_state[FormWizardMixin.PARAM_STEP],
            MfaMixin.STEP_MFA,
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_user_with_hotp_is_sent_email(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        self.req.config.email_host = "smtp.example.com"
        self.req.config.email_port = 587
        self.req.config.email_host_username = "mailuser"
        self.req.config.email_host_password = "mailpassword"
        self.req.config.email_use_tls = True
        self.req.config.email_from = "server@example.com"

        user = self.create_user(
            username="test",
            email="user@example.com",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_EMAIL,
            hotp_counter=0,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, user.username),
                (ViewParam.PASSWORD, "secret"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)
        expected_code = pyotp.HOTP(user.mfa_secret_key).at(1)
        view.dispatch()

        args, kwargs = mock_make_email.call_args_list[0]
        self.assertEqual(kwargs["from_addr"], "server@example.com")
        self.assertEqual(kwargs["to"], "user@example.com")
        self.assertEqual(kwargs["subject"], "CamCOPS authentication")
        self.assertIn(
            f"Your CamCOPS verification code is {expected_code}",
            kwargs["body"],
        )
        self.assertEqual(kwargs["content_type"], "text/plain")

        args, kwargs = mock_send_msg.call_args
        self.assertEqual(kwargs["host"], "smtp.example.com")
        self.assertEqual(kwargs["user"], "mailuser")
        self.assertEqual(kwargs["password"], "mailpassword")
        self.assertEqual(kwargs["port"], 587)
        self.assertTrue(kwargs["use_tls"])

    def test_user_with_hotp_is_sent_sms(self) -> None:
        test_config = {"username": "testuser", "password": "testpass"}

        self.req.config.sms_backend = get_sms_backend(
            SmsBackendNames.CONSOLE, {}
        )
        self.req.config.sms_config = test_config

        phone_number = phonenumbers.parse(TEST_PHONE_NUMBER)
        user = self.create_user(
            username="test",
            email="user@example.com",
            phone_number=phone_number,
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            hotp_counter=0,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, user.username),
                (ViewParam.PASSWORD, "secret"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)
        expected_code = pyotp.HOTP(user.mfa_secret_key).at(1)

        with self.assertLogs(level=logging.INFO) as logging_cm:
            view.dispatch()

        expected_message = f"Your CamCOPS verification code is {expected_code}"

        self.assertIn(
            ConsoleSmsBackend.make_msg(TEST_PHONE_NUMBER, expected_message),
            logging_cm.output[0],
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_login_with_hotp_increments_counter(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        user = self.create_user(
            username="test",
            email="user@example.com",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_EMAIL,
            hotp_counter=0,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, user.username),
                (ViewParam.PASSWORD, "secret"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)

        view.dispatch()

        self.assertEqual(user.hotp_counter, 1)

    @mock.patch("camcops_server.cc_modules.webview.audit")
    def test_user_with_totp_can_log_in(self, mock_audit: mock.Mock) -> None:
        user = self.create_user(
            username="test",
            mfa_method=MfaMethod.TOTP,
            mfa_secret_key=pyotp.random_base32(),
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()

        self.create_membership(user, self.group, may_use_webviewer=True)

        totp = pyotp.TOTP(user.mfa_secret_key)

        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, totp.now()),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)
        view.state.update(mfa_user_id=user.id, step=MfaMixin.STEP_MFA)

        with mock.patch.object(user, "login") as mock_user_login:
            with mock.patch.object(
                self.req.camcops_session, "login"
            ) as mock_session_login:
                with mock.patch.object(view, "timed_out", return_value=False):
                    with self.assertRaises(HTTPFound):
                        view.dispatch()

        args, kwargs = mock_user_login.call_args
        self.assertEqual(args[0], self.req)

        args, kwargs = mock_session_login.call_args
        self.assertEqual(args[0], user)

        args, kwargs = mock_audit.call_args
        self.assertEqual(args[0], self.req)
        self.assertEqual(args[1], "Login")
        self.assertEqual(kwargs["user_id"], user.id)
        self.assert_state_is_finished()

    @mock.patch("camcops_server.cc_modules.webview.audit")
    def test_user_with_hotp_can_log_in(self, mock_audit: mock.Mock) -> None:
        user = self.create_user(
            username="test",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=1,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()

        self.create_membership(user, self.group, may_use_webviewer=True)

        hotp = pyotp.HOTP(user.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, hotp.at(1)),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)
        view.state.update(mfa_user_id=user.id, step=MfaMixin.STEP_MFA)

        with mock.patch.object(user, "login") as mock_user_login:
            with mock.patch.object(
                self.req.camcops_session, "login"
            ) as mock_session_login:
                with mock.patch.object(view, "timed_out", return_value=False):
                    with self.assertRaises(HTTPFound):
                        view.dispatch()

        args, kwargs = mock_user_login.call_args
        self.assertEqual(args[0], self.req)

        args, kwargs = mock_session_login.call_args
        self.assertEqual(args[0], user)

        args, kwargs = mock_audit.call_args
        self.assertEqual(args[0], self.req)
        self.assertEqual(args[1], "Login")
        self.assertEqual(kwargs["user_id"], user.id)
        self.assert_state_is_finished()

    def test_form_state_cleared_on_failed_login(self) -> None:
        user = self.create_user(
            username="test",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=1,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        hotp = pyotp.HOTP(user.mfa_secret_key)

        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, hotp.at(2)),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)
        view.state.update(step=MfaMixin.STEP_MFA, mfa_user_id=user.id)

        with mock.patch.object(view, "timed_out", return_value=False):
            with self.assertRaises(HTTPFound):
                view.dispatch()

        messages = self.req.session.peek_flash(FlashQueue.DANGER)
        self.assertTrue(len(messages) > 0)
        self.assertIn("You entered an invalid code", messages[0])

        self.assert_state_is_clean()

    def test_user_cannot_log_in_if_timed_out(self) -> None:
        self.req.config.mfa_timeout_s = 600
        user = self.create_user(
            username="test",
            mfa_method=MfaMethod.TOTP,
            mfa_secret_key=pyotp.random_base32(),
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()
        self.create_membership(user, self.group, may_use_webviewer=True)

        totp = pyotp.TOTP(user.mfa_secret_key)

        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, totp.now()),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)
        view.state.update(
            mfa_user=user.id,
            mfa_time=int(time.time() - 601),
            step=MfaMixin.STEP_MFA,
        )

        with mock.patch.object(
            view, "fail_timed_out", side_effect=HTTPFound
        ) as mock_fail_timed_out:
            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_fail_timed_out.assert_called_once()

    def test_unprivileged_user_cannot_log_in(self) -> None:
        user = self.create_user(username="test")
        user.set_password(self.req, "secret")
        self.dbsession.flush()

        self.create_membership(user, self.group, may_use_webviewer=False)

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, user.username),
                (ViewParam.PASSWORD, "secret"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)

        with mock.patch.object(
            view, "fail_not_authorized", side_effect=HTTPFound
        ) as mock_fail_not_authorized:
            # The fail_not_authorized() function raises an exception
            # (of type HTTPFound) so the mock must do too. Otherwise
            # it will fall through inappropriately (and crash).
            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_fail_not_authorized.assert_called_once()

    def test_unknown_user_cannot_log_in(self) -> None:
        multidict = MultiDict(
            [
                (ViewParam.USERNAME, "unknown"),
                (ViewParam.PASSWORD, "secret"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        view = LoginView(self.req)

        with mock.patch.object(
            SecurityLoginFailure, "act_on_login_failure"
        ) as mock_act:
            with mock.patch.object(
                self.req.camcops_session, "logout"
            ) as mock_logout:
                with mock.patch.object(
                    view, "fail_not_authorized", side_effect=HTTPFound
                ) as mock_fail_not_authorized:
                    with self.assertRaises(HTTPFound):
                        view.dispatch()

        args, kwargs = mock_act.call_args
        self.assertEqual(args[0], self.req)
        self.assertEqual(args[1], "unknown")

        mock_logout.assert_called_once()
        mock_fail_not_authorized.assert_called_once()

    def test_timed_out_false_when_timeout_zero(self) -> None:
        self.req.config.mfa_timeout_s = 0
        view = LoginView(self.req)
        view.state["mfa_time"] = 0

        self.assertFalse(view.timed_out())

    def test_timed_out_false_when_no_authenticated_user(self) -> None:
        view = LoginView(self.req)

        self.assertFalse(view.timed_out())

    def test_timed_out_false_when_no_authentication_time(self) -> None:
        view = LoginView(self.req)

        user = self.create_user(username="test")
        # Should never be the case that we have a user ID but no
        # authentication time
        view.state["mfa_user_id"] = user.id

        self.assertFalse(view.timed_out())


class EditUserViewTests(BasicDatabaseTestCase):
    def test_redirect_on_cancel(self) -> None:
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()
        self.req.fake_request_post_from_dict({FormAction.CANCEL: "cancel"})
        self.req.add_get_params(
            {ViewParam.USER_ID: str(regular_user.id)}, set_method_get=False
        )

        with self.assertRaises(HTTPFound) as cm:
            edit_user(self.req)

        self.assertEqual(cm.exception.status_code, 302)
        self.assertIn(
            f"/{Routes.VIEW_ALL_USERS}", cm.exception.headers["Location"]
        )

    def test_raises_if_user_may_not_edit_another(self) -> None:
        self.req.add_get_params({ViewParam.USER_ID: str(self.user.id)})

        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()
        self.req._debugging_user = regular_user
        with self.assertRaises(HTTPBadRequest) as cm:
            edit_user(self.req)

        self.assertIn("Nobody may edit the system user", cm.exception.message)

    def test_superuser_sees_full_form(self) -> None:
        superuser = self.create_user(username="admin", superuser=True)
        self.dbsession.flush()
        self.req._debugging_user = superuser

        self.req.add_get_params({ViewParam.USER_ID: str(superuser.id)})

        response = edit_user(self.req)

        self.assertIn("Superuser (CAUTION!)", response.body.decode(UTF8))

    def test_groupadmin_sees_groupadmin_form(self) -> None:
        groupadmin = self.create_user(username="groupadmin")
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()
        self.create_membership(groupadmin, self.group, groupadmin=True)
        self.create_membership(regular_user, self.group)
        self.dbsession.flush()
        self.req._debugging_user = groupadmin

        self.req.add_get_params({ViewParam.USER_ID: str(regular_user.id)})

        response = edit_user(self.req)
        content = response.body.decode(UTF8)

        self.assertIn("Full name", content)
        self.assertNotIn("Superuser (CAUTION!)", content)

    def test_raises_for_conflicting_user_name(self) -> None:
        self.create_user(username="existing_user")
        other_user = self.create_user(username="other_user")
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, "existing_user"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_ID: str(other_user.id)}, set_method_get=False
        )

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_user(self.req)

        self.assertIn("Can't rename user", cm.exception.message)

    def test_user_is_updated(self) -> None:
        user = self.create_user(
            username="old_username",
            fullname="Old Name",
            email="old@example.com",
            language="da_DK",
        )
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, "new_username"),
                (ViewParam.FULLNAME, "New Name"),
                (ViewParam.EMAIL, "new@example.com"),
                (ViewParam.LANGUAGE, "en_GB"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        with self.assertRaises(HTTPFound):
            edit_user(self.req)

        self.assertEqual(user.username, "new_username")
        self.assertEqual(user.fullname, "New Name")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.language, "en_GB")

    def test_user_is_added_to_group(self) -> None:
        user = self.create_user(username="regular_user")
        group = self.create_group("group")
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, user.username),
                ("__start__", "group_ids:sequence"),
                ("group_id_sequence", str(group.id)),
                ("__end__", "group_ids:sequence"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        with mock.patch.object(user, "set_group_ids") as mock_set_group_ids:
            with self.assertRaises(HTTPFound):
                edit_user(self.req)

        mock_set_group_ids.assert_called_once_with([group.id])

    def test_user_stays_in_group_the_groupadmin_cannot_edit(self) -> None:
        regular_user = self.create_user(username="regular_user")
        group_b_admin = self.create_user(username="group_b_admin")
        group_a = self.create_group("group_a")
        group_b = self.create_group("group_b")
        self.dbsession.flush()
        self.create_membership(regular_user, group_a)
        self.create_membership(regular_user, group_b)
        self.create_membership(group_b_admin, group_b, groupadmin=True)
        self.dbsession.flush()
        self.req._debugging_user = group_b_admin

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, regular_user.username),
                ("__start__", "group_ids:sequence"),
                ("group_id_sequence", str(group_b.id)),
                ("__end__", "group_ids:sequence"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_ID: str(regular_user.id)}, set_method_get=False
        )

        with mock.patch.object(
            regular_user, "set_group_ids"
        ) as mock_set_group_ids:
            with self.assertRaises(HTTPFound):
                edit_user(self.req)

        mock_set_group_ids.assert_called_once_with([group_a.id, group_b.id])

    def test_upload_group_id_unset_when_membership_removed(self) -> None:
        group_a = self.create_group("group_a")
        group_b = self.create_group("group_b")
        regular_user = self.create_user(
            username="regular_user", upload_group=group_a
        )
        groupadmin = self.create_user(username="groupadmin")
        self.dbsession.flush()
        self.create_membership(regular_user, group_a)
        self.create_membership(regular_user, group_b)
        self.create_membership(groupadmin, group_a, groupadmin=True)
        self.create_membership(groupadmin, group_b, groupadmin=True)
        self.dbsession.flush()
        self.req._debugging_user = groupadmin

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, regular_user.username),
                ("__start__", "group_ids:sequence"),
                ("group_id_sequence", str(group_b.id)),
                ("__end__", "group_ids:sequence"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_ID: str(regular_user.id)}, set_method_get=False
        )

        with self.assertRaises(HTTPFound):
            edit_user(self.req)

        self.assertIsNone(regular_user.upload_group_id)

    def test_get_form_values(self) -> None:
        regular_user = self.create_user(
            username="regular_user",
            fullname="Full Name",
            email="user@example.com",
            language="da_DK",
        )
        group_b_admin = self.create_user(username="group_b_admin")
        group_a = self.create_group("group_a")
        group_b = self.create_group("group_b")
        self.dbsession.flush()
        self.create_membership(regular_user, group_a)
        self.create_membership(regular_user, group_b)
        self.create_membership(group_b_admin, group_b, groupadmin=True)
        self.dbsession.flush()
        self.req._debugging_user = group_b_admin

        view = EditUserGroupAdminView(self.req)
        # Would normally be set when going through dispatch()
        view.object = regular_user

        form_values = view.get_form_values()

        self.assertEqual(
            form_values[ViewParam.USERNAME], regular_user.username
        )
        self.assertEqual(
            form_values[ViewParam.FULLNAME], regular_user.fullname
        )
        self.assertEqual(form_values[ViewParam.EMAIL], regular_user.email)
        self.assertEqual(
            form_values[ViewParam.LANGUAGE], regular_user.language
        )
        self.assertEqual(form_values[ViewParam.GROUP_IDS], [group_b.id])

    def test_raises_if_email_address_used_for_mfa(self) -> None:
        regular_user = self.create_user(
            username="regular_user",
            mfa_method=MfaMethod.HOTP_EMAIL,
            email="user@example.com",
        )
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.USERNAME, regular_user.username),
                (ViewParam.EMAIL, ""),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_ID: str(regular_user.id)}, set_method_get=False
        )

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_user(self.req)

        self.assertIn(
            "used for multi-factor authentication", cm.exception.message
        )


class EditOwnUserMfaViewTests(BasicDatabaseTestCase):
    def test_get_form_values_mfa_method(self) -> None:
        regular_user = self.create_user(
            username="regular_user", mfa_method=MfaMethod.HOTP_SMS
        )
        self.dbsession.flush()

        self.req._debugging_user = regular_user
        view = EditOwnUserMfaView(self.req)

        # Would normally be set when going through dispatch()
        view.object = regular_user

        form_values = view.get_form_values()

        self.assertEqual(
            form_values[ViewParam.MFA_METHOD], regular_user.mfa_method
        )

    def test_get_form_values_hotp_email(self) -> None:
        regular_user = self.create_user(
            username="regular_user",
            mfa_method=MfaMethod.HOTP_EMAIL,
            email="regular_user@example.com",
        )
        self.dbsession.flush()

        self.req._debugging_user = regular_user
        view = EditOwnUserMfaView(self.req)

        # Would normally be set when going through dispatch()
        view.object = regular_user
        view.state.update(step=EditOwnUserMfaView.STEP_HOTP_EMAIL)

        mock_secret_key = pyotp.random_base32()
        with mock.patch(
            "camcops_server.cc_modules.webview.pyotp.random_base32",
            return_value=mock_secret_key,
        ) as mock_random_base32:
            form_values = view.get_form_values()

        mock_random_base32.assert_called_once()

        self.assertEqual(
            form_values[ViewParam.MFA_SECRET_KEY], mock_secret_key
        )
        self.assertEqual(form_values[ViewParam.EMAIL], regular_user.email)

    def test_get_form_values_hotp_sms(self) -> None:
        regular_user = self.create_user(
            username="regular_user",
            mfa_method=MfaMethod.HOTP_SMS,
            phone_number=phonenumbers.parse(TEST_PHONE_NUMBER),
        )
        self.dbsession.flush()

        self.req._debugging_user = regular_user
        view = EditOwnUserMfaView(self.req)

        # Would normally be set when going through dispatch()
        view.object = regular_user
        view.state.update(step=EditOwnUserMfaView.STEP_HOTP_SMS)

        mock_secret_key = pyotp.random_base32()
        with mock.patch(
            "camcops_server.cc_modules.webview.pyotp.random_base32",
            return_value=mock_secret_key,
        ) as mock_random_base32:
            form_values = view.get_form_values()

        mock_random_base32.assert_called_once()

        self.assertEqual(
            form_values[ViewParam.MFA_SECRET_KEY], mock_secret_key
        )
        self.assertEqual(
            form_values[ViewParam.PHONE_NUMBER], regular_user.phone_number
        )

    def test_get_form_values_totp(self) -> None:
        regular_user = self.create_user(
            username="regular_user", mfa_method=MfaMethod.TOTP
        )
        self.dbsession.flush()

        self.req._debugging_user = regular_user
        view = EditOwnUserMfaView(self.req)

        # Would normally be set when going through dispatch()
        view.object = regular_user
        view.state.update(step=EditOwnUserMfaView.STEP_TOTP)

        mock_secret_key = pyotp.random_base32()
        with mock.patch(
            "camcops_server.cc_modules.webview.pyotp.random_base32",
            return_value=mock_secret_key,
        ) as mock_random_base32:
            form_values = view.get_form_values()

        mock_random_base32.assert_called_once()

        self.assertEqual(
            form_values[ViewParam.MFA_SECRET_KEY], mock_secret_key
        )

    def test_user_can_set_secret_key(self) -> None:
        regular_user = self.create_user(username="regular_user")
        regular_user.mfa_method = MfaMethod.TOTP
        regular_user.ensure_mfa_info()
        # ... otherwise, the absence of e.g. the HOTP counter will cause a
        # secret key reset.
        self.dbsession.flush()

        mfa_secret_key = pyotp.random_base32()

        multidict = MultiDict(
            [
                (ViewParam.MFA_SECRET_KEY, mfa_secret_key),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)
        self.req.config.mfa_methods = [MfaMethod.TOTP]

        view = EditOwnUserMfaView(self.req)
        view.state.update(step=EditOwnUserMfaView.STEP_TOTP)

        view.dispatch()

        self.assertEqual(regular_user.mfa_secret_key, mfa_secret_key)

    def test_user_can_set_method_totp(self) -> None:
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.MFA_METHOD, MfaMethod.TOTP),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)
        self.req.config.mfa_methods = [MfaMethod.TOTP]

        view = EditOwnUserMfaView(self.req)

        view.dispatch()

        self.assertEqual(regular_user.mfa_method, MfaMethod.TOTP)

    def test_user_can_set_method_hotp_email(self) -> None:
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.MFA_METHOD, MfaMethod.HOTP_EMAIL),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)
        self.req.config.mfa_methods = [MfaMethod.HOTP_EMAIL]

        view = EditOwnUserMfaView(self.req)

        view.dispatch()

        self.assertEqual(regular_user.mfa_method, MfaMethod.HOTP_EMAIL)
        self.assertEqual(regular_user.hotp_counter, 0)

    def test_user_can_set_method_hotp_sms(self) -> None:
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.MFA_METHOD, MfaMethod.HOTP_SMS),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)
        self.req.config.mfa_methods = [MfaMethod.HOTP_SMS]

        view = EditOwnUserMfaView(self.req)

        view.dispatch()

        self.assertEqual(regular_user.mfa_method, MfaMethod.HOTP_SMS)
        self.assertEqual(regular_user.hotp_counter, 0)

    def test_user_can_disable_mfa(self) -> None:
        regular_user = self.create_user(
            username="regular_user", mfa_method=MfaMethod.TOTP
        )
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.MFA_METHOD, MfaMethod.NO_MFA),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)
        self.req.config.mfa_methods = [
            MfaMethod.TOTP,
            MfaMethod.HOTP_SMS,
            MfaMethod.HOTP_EMAIL,
            MfaMethod.NO_MFA,
        ]

        view = EditOwnUserMfaView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        self.assertEqual(regular_user.mfa_method, MfaMethod.NO_MFA)

    def test_user_can_set_phone_number(self) -> None:
        regular_user = self.create_user(username="regular_user")
        regular_user.mfa_method = MfaMethod.HOTP_SMS
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.PHONE_NUMBER, TEST_PHONE_NUMBER),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)
        self.req.config.mfa_methods = [MfaMethod.HOTP_SMS]

        view = EditOwnUserMfaView(self.req)
        view.state.update(step=EditOwnUserMfaView.STEP_HOTP_SMS)

        view.dispatch()

        test_number = phonenumbers.parse(TEST_PHONE_NUMBER)
        self.assertEqual(regular_user.phone_number, test_number)

    def test_user_can_set_email_address(self) -> None:
        regular_user = self.create_user(username="regular_user")
        # We're going to force this user to the e-mail verification step, so
        # we need to ensure it's set to use e-mail MFA:
        regular_user.mfa_method = MfaMethod.HOTP_EMAIL
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.EMAIL, "regular_user@example.com"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)

        view = EditOwnUserMfaView(self.req)
        view.state.update(step=EditOwnUserMfaView.STEP_HOTP_EMAIL)

        view.dispatch()

        self.assertEqual(regular_user.email, "regular_user@example.com")


class ChangeOtherPasswordViewTests(TestStateMixin, BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.req.matched_route.name = "change_other_password"

    def test_raises_for_invalid_user(self) -> None:
        multidict = MultiDict([(FormAction.SUBMIT, "submit")])
        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.USER_ID: "123"}, set_method_get=False
        )

        view = ChangeOtherPasswordView(self.req)
        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("Cannot find User with id:123", cm.exception.message)

    def test_raises_when_user_may_not_edit_other_user(self) -> None:
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()
        multidict = MultiDict(
            [
                ("__start__", "new_password:mapping"),
                (ViewParam.NEW_PASSWORD, "monkeybusiness"),
                ("new_password-confirm", "monkeybusiness"),
                ("__end__", "new_password:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.USER_ID: str(self.user.id)}, set_method_get=False
        )

        view = ChangeOtherPasswordView(self.req)
        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("Nobody may edit the system user", cm.exception.message)

    def test_password_set(self) -> None:
        groupadmin = self.create_user(username="groupadmin")
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()
        self.create_membership(groupadmin, self.group, groupadmin=True)
        self.create_membership(regular_user, self.group)
        self.dbsession.flush()

        self.assertFalse(regular_user.must_change_password)

        multidict = MultiDict(
            [
                ("__start__", "new_password:mapping"),
                (ViewParam.NEW_PASSWORD, "monkeybusiness"),
                ("new_password-confirm", "monkeybusiness"),
                ("__end__", "new_password:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = groupadmin
        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.USER_ID: str(regular_user.id)}, set_method_get=False
        )

        view = ChangeOtherPasswordView(self.req)

        with mock.patch.object(
            regular_user, "set_password"
        ) as mock_set_password:
            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_set_password.assert_called_once_with(self.req, "monkeybusiness")
        self.assertFalse(regular_user.must_change_password)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)
        self.assertTrue(len(messages) > 0)
        self.assertIn("Password changed for user 'regular_user'", messages[0])

    def test_user_forced_to_change_password(self) -> None:
        groupadmin = self.create_user(username="groupadmin")
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()
        self.create_membership(groupadmin, self.group, groupadmin=True)
        self.create_membership(regular_user, self.group)
        self.dbsession.flush()

        multidict = MultiDict(
            [
                (ViewParam.MUST_CHANGE_PASSWORD, "true"),
                ("__start__", "new_password:mapping"),
                (ViewParam.NEW_PASSWORD, "monkeybusiness"),
                ("new_password-confirm", "monkeybusiness"),
                ("__end__", "new_password:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = groupadmin
        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.USER_ID: str(regular_user.id)}, set_method_get=False
        )

        view = ChangeOtherPasswordView(self.req)

        with mock.patch.object(
            regular_user, "force_password_change"
        ) as mock_force_change:
            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_force_change.assert_called_once()

    def test_redirects_if_editing_own_account(self) -> None:
        superuser = self.create_user(username="admin", superuser=True)
        self.dbsession.flush()
        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(superuser.id)}, set_method_get=False
        )

        view = ChangeOtherPasswordView(self.req)
        with self.assertRaises(HTTPFound) as cm:
            view.dispatch()

        self.assertEqual(cm.exception.status_code, 302)
        self.assertIn(
            f"/{Routes.CHANGE_OWN_PASSWORD}", cm.exception.headers["Location"]
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_user_sees_otp_form_if_mfa_setup(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        superuser = self.create_user(
            username="admin",
            superuser=True,
            email="admin@example.com",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=0,
        )

        user = self.create_user(username="user")
        self.dbsession.flush()
        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        view = ChangeOtherPasswordView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)
        self.assertIn("Enter the six-digit code", context["form"])

    def test_code_sent_if_mfa_setup(self) -> None:
        self.req.config.sms_backend = get_sms_backend(
            SmsBackendNames.CONSOLE, {}
        )

        phone_number = phonenumbers.parse(TEST_PHONE_NUMBER)
        superuser = self.create_user(
            username="admin",
            superuser=True,
            email="admin@example.com",
            phone_number=phone_number,
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            hotp_counter=0,
        )
        user = self.create_user(username="user", email="user@example.com")
        self.dbsession.flush()

        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        view = ChangeOtherPasswordView(self.req)
        with self.assertLogs(level=logging.INFO) as logging_cm:
            view.dispatch()

        expected_code = pyotp.HOTP(superuser.mfa_secret_key).at(1)
        expected_message = f"Your CamCOPS verification code is {expected_code}"

        self.assertIn(
            ConsoleSmsBackend.make_msg(TEST_PHONE_NUMBER, expected_message),
            logging_cm.output[0],
        )

    def test_user_can_enter_token(self) -> None:
        superuser = self.create_user(
            username="admin",
            superuser=True,
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user = self.create_user(username="user", email="user@example.com")
        self.dbsession.flush()

        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        hotp = pyotp.HOTP(superuser.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, hotp.at(1)),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        view = ChangeOtherPasswordView(self.req)

        response = view.dispatch()

        self.assertEqual(
            self.req.camcops_session.form_state[FormWizardMixin.PARAM_STEP],
            ChangeOtherPasswordView.STEP_CHANGE_PASSWORD,
        )
        self.assertIn("Change password for user:", response.body.decode(UTF8))
        self.assertIn(
            "Type the new password and confirm it", response.body.decode(UTF8)
        )

    def test_form_state_cleared_on_invalid_token(self) -> None:
        superuser = self.create_user(
            username="superuser",
            superuser=True,
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user = self.create_user(username="user", email="user@example.com")
        self.dbsession.flush()

        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        hotp = pyotp.HOTP(superuser.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, hotp.at(2)),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        view = ChangeOtherPasswordView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        messages = self.req.session.peek_flash(FlashQueue.DANGER)
        self.assertTrue(len(messages) > 0)
        self.assertIn("You entered an invalid code", messages[0])

        self.assert_state_is_clean()

    def test_cannot_change_password_if_timed_out(self) -> None:
        self.req.config.mfa_timeout_s = 600
        superuser = self.create_user(
            username="admin",
            superuser=True,
            mfa_method=MfaMethod.TOTP,
            mfa_secret_key=pyotp.random_base32(),
        )
        user = self.create_user(username="user")
        self.dbsession.flush()

        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        totp = pyotp.TOTP(superuser.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, totp.now()),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        view = ChangeOtherPasswordView(self.req)
        view.state.update(
            mfa_user=superuser.id,
            mfa_time=int(time.time() - 601),
            step=MfaMixin.STEP_MFA,
        )

        with mock.patch.object(
            view, "fail_timed_out", side_effect=HTTPFound
        ) as mock_fail_timed_out:
            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_fail_timed_out.assert_called_once()


class EditOtherUserMfaViewTests(TestStateMixin, BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.req.matched_route.name = "edit_other_user_mfa"

    def test_raises_for_invalid_user(self) -> None:
        multidict = MultiDict([(FormAction.SUBMIT, "submit")])
        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.USER_ID: "123"}, set_method_get=False
        )

        view = EditOtherUserMfaView(self.req)
        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("Cannot find User with id:123", cm.exception.message)

    def test_raises_when_user_may_not_edit_other_user(self) -> None:
        regular_user = self.create_user(username="regular_user")
        self.dbsession.flush()
        multidict = MultiDict([(FormAction.SUBMIT, "submit")])
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.USER_ID: str(self.user.id)}, set_method_get=False
        )

        view = EditOtherUserMfaView(self.req)
        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("Nobody may edit the system user", cm.exception.message)

    def test_disable_mfa(self) -> None:
        groupadmin = self.create_user(username="groupadmin")
        regular_user = self.create_user(
            username="regular_user", mfa_method=MfaMethod.TOTP
        )
        self.dbsession.flush()
        self.create_membership(groupadmin, self.group, groupadmin=True)
        self.create_membership(regular_user, self.group)
        self.dbsession.flush()

        self.assertFalse(regular_user.must_change_password)

        multidict = MultiDict(
            [(ViewParam.DISABLE_MFA, "true"), (FormAction.SUBMIT, "submit")]
        )
        self.req._debugging_user = groupadmin
        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.USER_ID: str(regular_user.id)}, set_method_get=False
        )

        view = EditOtherUserMfaView(self.req)
        with self.assertRaises(HTTPFound):
            view.dispatch()

        self.assertEqual(regular_user.mfa_method, MfaMethod.NO_MFA)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)
        self.assertTrue(len(messages) > 0)
        self.assertIn(
            "Multi-factor authentication disabled for user 'regular_user'",
            messages[0],
        )

    def test_redirects_if_editing_own_account(self) -> None:
        superuser = self.create_user(username="admin", superuser=True)
        self.dbsession.flush()
        self.req._debugging_user = superuser
        self.req.add_get_params({ViewParam.USER_ID: str(superuser.id)})

        view = EditOtherUserMfaView(self.req)
        with self.assertRaises(HTTPFound) as cm:
            view.dispatch()

        self.assertEqual(cm.exception.status_code, 302)
        self.assertIn(
            f"/{Routes.EDIT_OWN_USER_MFA}", cm.exception.headers["Location"]
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_user_sees_otp_form_if_mfa_setup(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        superuser = self.create_user(
            username="admin",
            superuser=True,
            email="admin@example.com",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=0,
        )

        user = self.create_user(username="user")
        self.dbsession.flush()
        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        view = EditOtherUserMfaView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)
        self.assertIn("Enter the six-digit code", context["form"])

    def test_code_sent_if_mfa_setup(self) -> None:
        self.req.config.sms_backend = get_sms_backend(
            SmsBackendNames.CONSOLE, {}
        )

        phone_number = phonenumbers.parse(TEST_PHONE_NUMBER)
        superuser = self.create_user(
            username="admin",
            superuser=True,
            email="admin@example.com",
            phone_number=phone_number,
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            hotp_counter=0,
        )
        user = self.create_user(username="user", email="user@example.com")
        self.dbsession.flush()

        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        view = EditOtherUserMfaView(self.req)
        with self.assertLogs(level=logging.INFO) as logging_cm:
            view.dispatch()

        expected_code = pyotp.HOTP(superuser.mfa_secret_key).at(1)
        expected_message = f"Your CamCOPS verification code is {expected_code}"

        self.assertIn(
            ConsoleSmsBackend.make_msg(TEST_PHONE_NUMBER, expected_message),
            logging_cm.output[0],
        )

    def test_user_can_enter_token(self) -> None:
        superuser = self.create_user(
            username="admin",
            superuser=True,
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user = self.create_user(username="user", email="user@example.com")
        self.dbsession.flush()

        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        hotp = pyotp.HOTP(superuser.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, hotp.at(1)),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        view = EditOtherUserMfaView(self.req)

        response = view.dispatch()

        self.assertEqual(
            self.req.camcops_session.form_state[FormWizardMixin.PARAM_STEP],
            "other_user_mfa",
        )
        self.assertIn(
            "Edit multi-factor authentication for user:",
            response.body.decode(UTF8),
        )

    def test_form_state_cleared_on_invalid_token(self) -> None:
        superuser = self.create_user(
            username="superuser",
            superuser=True,
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user = self.create_user(username="user", email="user@example.com")
        self.dbsession.flush()

        self.req._debugging_user = superuser
        self.req.add_get_params(
            {ViewParam.USER_ID: str(user.id)}, set_method_get=False
        )

        hotp = pyotp.HOTP(superuser.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, hotp.at(2)),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        view = EditOtherUserMfaView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        messages = self.req.session.peek_flash(FlashQueue.DANGER)
        self.assertTrue(len(messages) > 0)
        self.assertIn("You entered an invalid code", messages[0])

        self.assert_state_is_clean()


class EditUserGroupMembershipViewTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.regular_user = User()
        self.regular_user.username = "ruser"
        self.regular_user.hashedpw = ""
        self.dbsession.add(self.regular_user)
        self.dbsession.flush()

        self.group_admin = User()
        self.group_admin.username = "gadmin"
        self.group_admin.hashedpw = ""
        self.dbsession.add(self.group_admin)
        self.dbsession.flush()

        admin_ugm = UserGroupMembership(
            user_id=self.group_admin.id, group_id=self.group.id
        )
        admin_ugm.groupadmin = True
        self.dbsession.add(admin_ugm)

        self.ugm = UserGroupMembership(
            user_id=self.regular_user.id, group_id=self.group.id
        )
        self.dbsession.add(self.ugm)
        self.dbsession.commit()

    def test_superuser_can_update_user_group_membership(self) -> None:
        self.assertFalse(self.ugm.may_upload)
        self.assertFalse(self.ugm.may_register_devices)
        self.assertFalse(self.ugm.may_use_webviewer)
        self.assertFalse(self.ugm.view_all_patients_when_unfiltered)
        self.assertFalse(self.ugm.may_dump_data)
        self.assertFalse(self.ugm.may_run_reports)
        self.assertFalse(self.ugm.may_add_notes)
        self.assertFalse(self.ugm.may_manage_patients)
        self.assertFalse(self.ugm.may_email_patients)
        self.assertFalse(self.ugm.groupadmin)

        multidict = MultiDict(
            [
                (ViewParam.MAY_UPLOAD, "true"),
                (ViewParam.MAY_REGISTER_DEVICES, "true"),
                (ViewParam.MAY_USE_WEBVIEWER, "true"),
                (ViewParam.VIEW_ALL_PATIENTS_WHEN_UNFILTERED, "true"),
                (ViewParam.MAY_DUMP_DATA, "true"),
                (ViewParam.MAY_RUN_REPORTS, "true"),
                (ViewParam.MAY_ADD_NOTES, "true"),
                (ViewParam.MAY_MANAGE_PATIENTS, "true"),
                (ViewParam.MAY_EMAIL_PATIENTS, "true"),
                (ViewParam.GROUPADMIN, "true"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(self.ugm.id)},
            set_method_get=False,
        )

        with self.assertRaises(HTTPFound):
            edit_user_group_membership(self.req)

        self.assertTrue(self.ugm.may_upload)
        self.assertTrue(self.ugm.may_register_devices)
        self.assertTrue(self.ugm.may_use_webviewer)
        self.assertTrue(self.ugm.view_all_patients_when_unfiltered)
        self.assertTrue(self.ugm.may_dump_data)
        self.assertTrue(self.ugm.may_run_reports)
        self.assertTrue(self.ugm.may_add_notes)
        self.assertTrue(self.ugm.may_manage_patients)
        self.assertTrue(self.ugm.may_email_patients)

    def test_groupadmin_can_update_user_group_membership(self) -> None:
        self.req._debugging_user = self.group_admin

        self.assertFalse(self.ugm.may_upload)
        self.assertFalse(self.ugm.may_register_devices)
        self.assertFalse(self.ugm.may_use_webviewer)
        self.assertFalse(self.ugm.view_all_patients_when_unfiltered)
        self.assertFalse(self.ugm.may_dump_data)
        self.assertFalse(self.ugm.may_run_reports)
        self.assertFalse(self.ugm.may_add_notes)
        self.assertFalse(self.ugm.may_manage_patients)
        self.assertFalse(self.ugm.may_email_patients)

        multidict = MultiDict(
            [
                (ViewParam.MAY_UPLOAD, "true"),
                (ViewParam.MAY_REGISTER_DEVICES, "true"),
                (ViewParam.MAY_USE_WEBVIEWER, "true"),
                (ViewParam.VIEW_ALL_PATIENTS_WHEN_UNFILTERED, "true"),
                (ViewParam.MAY_DUMP_DATA, "true"),
                (ViewParam.MAY_RUN_REPORTS, "true"),
                (ViewParam.MAY_ADD_NOTES, "true"),
                (ViewParam.MAY_MANAGE_PATIENTS, "true"),
                (ViewParam.MAY_EMAIL_PATIENTS, "true"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(self.ugm.id)},
            set_method_get=False,
        )

        with self.assertRaises(HTTPFound):
            edit_user_group_membership(self.req)

        self.assertTrue(self.ugm.may_upload)
        self.assertTrue(self.ugm.may_register_devices)
        self.assertTrue(self.ugm.may_use_webviewer)
        self.assertTrue(self.ugm.view_all_patients_when_unfiltered)
        self.assertTrue(self.ugm.may_dump_data)
        self.assertTrue(self.ugm.may_run_reports)
        self.assertTrue(self.ugm.may_add_notes)
        self.assertTrue(self.ugm.may_manage_patients)
        self.assertTrue(self.ugm.may_email_patients)

    def test_raises_if_cant_edit_user(self) -> None:
        self.ugm.user_id = self.user.id
        self.dbsession.add(self.ugm)
        self.dbsession.commit()

        multidict = MultiDict([(FormAction.SUBMIT, "submit")])

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(self.ugm.id)},
            set_method_get=False,
        )

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_user_group_membership(self.req)

        self.assertIn("Nobody may edit the system user", cm.exception.message)

    def test_raises_if_cant_administer_group(self) -> None:
        group_a = self.create_group("groupa")
        group_b = self.create_group("groupb")

        user1 = self.create_user(username="user1")
        user2 = self.create_user(username="user2")
        self.dbsession.flush()

        # User 1 is a group administrator for group A,
        # User 2 is a member if group A
        self.create_membership(user1, group_a, groupadmin=True)
        self.create_membership(user2, group_a),

        # User 1 is not an administrator of group B
        # User 2 is a member of group B
        ugm = self.create_membership(user2, group_b)
        self.dbsession.commit()

        multidict = MultiDict([(FormAction.SUBMIT, "submit")])

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(ugm.id)},
            set_method_get=False,
        )

        self.req._debugging_user = user1

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_user_group_membership(self.req)

        self.assertIn(
            "You may not administer this group", cm.exception.message
        )

    def test_cancel_returns_to_users_list(self) -> None:
        multidict = MultiDict([(FormAction.CANCEL, "cancel")])

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(self.ugm.id)},
            set_method_get=False,
        )

        with self.assertRaises(HTTPFound) as cm:
            edit_user_group_membership(self.req)

        self.assertEqual(cm.exception.status_code, 302)

        self.assertIn(Routes.VIEW_ALL_USERS, cm.exception.headers["Location"])


class ChangeOwnPasswordViewTests(TestStateMixin, BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.req.matched_route.name = "change_own_password"

    def test_user_can_change_password(self) -> None:
        new_password = "monkeybusiness"

        user = self.create_user(username="user", mfa_method=MfaMethod.NO_MFA)
        user.set_password(self.req, "secret")
        multidict = MultiDict(
            [
                (ViewParam.OLD_PASSWORD, "secret"),
                ("__start__", "new_password:mapping"),
                (ViewParam.NEW_PASSWORD, new_password),
                ("new_password-confirm", new_password),
                ("__end__", "new_password-mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req._debugging_user = user

        with mock.patch.object(user, "set_password") as mock_set_password:
            with self.assertRaises(HTTPFound):
                change_own_password(self.req)

        mock_set_password.assert_called_once_with(self.req, new_password)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)
        self.assertTrue(len(messages) > 0)
        self.assertIn("You have changed your password", messages[0])
        self.assert_state_is_finished()

    def test_user_sees_expiry_message(self) -> None:
        user = self.create_user(
            username="user",
            mfa_method=MfaMethod.NO_MFA,
            must_change_password=True,
        )
        self.req._debugging_user = user

        with mock.patch.object(self.req.session, "flash") as mock_flash:
            change_own_password(self.req)

        args, kwargs = mock_flash.call_args
        self.assertIn("Your password has expired", args[0])
        self.assertEqual(kwargs["queue"], FlashQueue.DANGER)

    def test_password_must_differ(self) -> None:
        view = ChangeOwnPasswordView(self.req)

        form_kwargs = view.get_form_kwargs()
        self.assertIn("must_differ", form_kwargs)
        self.assertTrue(form_kwargs["must_differ"])

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_user_sees_otp_form_if_mfa_setup(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        user = self.create_user(
            username="user",
            email="user@example.com",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=0,
        )
        self.req._debugging_user = user

        view = ChangeOwnPasswordView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args
        context = args[0]

        self.assertIn("form", context)
        self.assertIn("Enter the six-digit code", context["form"])

    def test_code_sent_if_mfa_setup(self) -> None:
        self.req.config.sms_backend = get_sms_backend(
            SmsBackendNames.CONSOLE, {}
        )
        phone_number = phonenumbers.parse(TEST_PHONE_NUMBER)
        user = self.create_user(
            username="user",
            email="user@example.com",
            phone_number=phone_number,
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            hotp_counter=0,
        )

        self.req._debugging_user = user
        view = ChangeOwnPasswordView(self.req)
        with self.assertLogs(level=logging.INFO) as logging_cm:
            view.dispatch()

        expected_code = pyotp.HOTP(user.mfa_secret_key).at(1)
        expected_message = f"Your CamCOPS verification code is {expected_code}"

        self.assertIn(
            ConsoleSmsBackend.make_msg(TEST_PHONE_NUMBER, expected_message),
            logging_cm.output[0],
        )

    def test_user_can_enter_token(self) -> None:
        user = self.create_user(
            username="user",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()

        self.req._debugging_user = user

        hotp = pyotp.HOTP(user.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, hotp.at(1)),  # the token
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        view = ChangeOwnPasswordView(self.req)

        response = view.dispatch()

        self.assertEqual(
            self.req.camcops_session.form_state[FormWizardMixin.PARAM_STEP],
            ChangeOwnPasswordView.STEP_CHANGE_PASSWORD,
        )
        self.assertIn("Change your password", response.body.decode(UTF8))
        self.assertIn(
            "Type the new password and confirm it", response.body.decode(UTF8)
        )

    def test_form_state_cleared_on_invalid_token(self) -> None:
        user = self.create_user(
            username="user",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()

        self.req._debugging_user = user

        hotp = pyotp.HOTP(user.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, hotp.at(2)),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        view = ChangeOwnPasswordView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        messages = self.req.session.peek_flash(FlashQueue.DANGER)
        self.assertTrue(len(messages) > 0)
        self.assertIn("You entered an invalid code", messages[0])

        self.assert_state_is_clean()

    def test_cannot_change_password_if_timed_out(self) -> None:
        self.req.config.mfa_timeout_s = 600
        user = self.create_user(
            username="user",
            mfa_method=MfaMethod.TOTP,
            mfa_secret_key=pyotp.random_base32(),
        )
        user.set_password(self.req, "secret")
        self.dbsession.flush()

        self.req._debugging_user = user

        totp = pyotp.TOTP(user.mfa_secret_key)
        multidict = MultiDict(
            [
                (ViewParam.ONE_TIME_PASSWORD, totp.now()),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        view = ChangeOwnPasswordView(self.req)
        view.state.update(
            mfa_user=user.id,
            mfa_time=int(time.time() - 601),
            step=MfaMixin.STEP_MFA,
        )

        with mock.patch.object(
            view, "fail_timed_out", side_effect=HTTPFound
        ) as mock_fail_timed_out:
            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_fail_timed_out.assert_called_once()
