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
from urllib.parse import urlparse

from cardinal_pythonlib.classes import class_attribute_names
from cardinal_pythonlib.httpconst import MimeType
from pendulum import Duration, local
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
from camcops_server.cc_modules.cc_testfactories import (
    AnyIdNumGroupFactory,
    DeviceFactory,
    Fake,
    GroupFactory,
    NHSIdNumDefinitionFactory,
    NHSPatientIdNumFactory,
    PatientFactory,
    PatientTaskScheduleFactory,
    RioIdNumDefinitionFactory,
    ServerCreatedNHSPatientIdNumFactory,
    ServerCreatedPatientFactory,
    StudyPatientIdNumFactory,
    TaskScheduleFactory,
    TaskScheduleItemFactory,
    UserFactory,
    UserGroupMembershipFactory,
)
from camcops_server.cc_modules.cc_unittest import (
    BasicDatabaseTestCase,
    DemoDatabaseTestCase,
    DemoRequestTestCase,
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
from camcops_server.tasks.tests.factories import BmiFactory
from camcops_server.cc_modules.tests.cc_view_classes_tests import (
    TestStateMixin,
)
from camcops_server.cc_modules.webview import (
    add_patient,
    add_user,
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
    forcibly_finalize,
    LoginView,
    MfaMixin,
    SendEmailFromPatientTaskScheduleView,
    view_patient_task_schedule,
    view_patient_task_schedules,
)

log = logging.getLogger(__name__)


# =============================================================================
# Unit testing
# =============================================================================

UTF8 = "utf-8"


class WebviewTests(DemoDatabaseTestCase):
    def test_any_records_use_group_true(self) -> None:
        # All tasks created in DemoDatabaseTestCase will be in this group
        self.assertTrue(
            any_records_use_group(self.req, self.demo_database_group)
        )

    def test_any_records_use_group_false(self) -> None:
        """
        If this fails with:
        sqlalchemy.exc.InvalidRequestError: SQL expression, column, or mapped
        entity expected - got <name of task base class>
        then the base class probably needs to be declared __abstract__. See
        DiagnosisItemBase as an example.
        """
        group = GroupFactory()

        self.assertFalse(any_records_use_group(self.req, group))

    def test_webview_constant_validators(self) -> None:
        for x in class_attribute_names(ViewArg):
            try:
                validate_alphanum_underscore(x, self.req)
            except ValueError:
                self.fail(f"Operations.{x} fails validate_alphanum_underscore")


class AddTaskScheduleViewTests(BasicDatabaseTestCase):
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


class EditTaskScheduleViewTests(DemoRequestTestCase):
    def test_schedule_name_can_be_updated(self) -> None:
        user = self.req._debugging_user = UserFactory()
        group = GroupFactory()
        UserGroupMembershipFactory(
            group_id=group.id, user_id=user.id, groupadmin=True
        )

        schedule = TaskScheduleFactory(group=group)
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.NAME, "MOJO"),
                (ViewParam.GROUP_ID, group.id),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.SCHEDULE_ID: str(schedule.id)},
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
        group_a = GroupFactory()
        group_b = GroupFactory()

        group_a_schedule = TaskScheduleFactory(group=group_a)

        group_b_user = UserFactory()
        UserGroupMembershipFactory(
            group_id=group_b.id, user_id=group_b_user.id, groupadmin=True
        )
        self.req._debugging_user = group_b_user

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.NAME, "Something else"),
                (ViewParam.GROUP_ID, group_b.id),
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.SCHEDULE_ID: str(group_a_schedule.id)},
            set_method_get=False,
        )

        view = EditTaskScheduleView(self.req)

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("not a group administrator", cm.exception.message)


class DeleteTaskScheduleViewTests(DemoRequestTestCase):
    def test_schedule_item_is_deleted(self) -> None:
        user = self.req._debugging_user = UserFactory()
        group = GroupFactory()
        UserGroupMembershipFactory(
            group_id=group.id, user_id=user.id, groupadmin=True
        )
        schedule = TaskScheduleFactory(group=group)
        self.assertIsNotNone(self.dbsession.query(TaskSchedule).one_or_none())

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
            {ViewParam.SCHEDULE_ID: str(schedule.id)},
            set_method_get=False,
        )
        view = DeleteTaskScheduleView(self.req)

        with self.assertRaises(HTTPFound) as e:
            view.dispatch()

        self.assertEqual(e.exception.status_code, 302)
        self.assertIn(
            Routes.VIEW_TASK_SCHEDULES, e.exception.headers["Location"]
        )

        self.assertIsNone(self.dbsession.query(TaskSchedule).one_or_none())


class AddTaskScheduleItemViewTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.schedule = TaskScheduleFactory(group=self.group)

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


class EditTaskScheduleItemViewTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.schedule = TaskScheduleFactory(group=self.group)

    def test_schedule_item_is_updated(self) -> None:
        item = TaskScheduleItemFactory(
            task_schedule=self.schedule,
            task_table_name="ace3",
            due_from=Duration(days=30),
            due_by=Duration(days=60),
        )

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
            {ViewParam.SCHEDULE_ITEM_ID: str(item.id)},
            set_method_get=False,
        )
        view = EditTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPFound) as cm:
            view.dispatch()

        self.assertEqual(item.task_table_name, "bmi")
        self.assertEqual(cm.exception.status_code, 302)
        self.assertIn(
            f"{Routes.VIEW_TASK_SCHEDULE_ITEMS}"
            f"?{ViewParam.SCHEDULE_ID}={item.schedule_id}",
            cm.exception.headers["Location"],
        )

    def test_schedule_item_is_not_updated_on_cancel(self) -> None:
        item = TaskScheduleItemFactory(
            task_schedule=self.schedule,
            task_table_name="ace3",
            due_from=Duration(days=30),
            due_by=Duration(days=60),
        )

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
            {ViewParam.SCHEDULE_ITEM_ID: str(item.id)},
            set_method_get=False,
        )
        view = EditTaskScheduleItemView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        self.assertEqual(item.task_table_name, "ace3")

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
        item = TaskScheduleItemFactory(
            task_schedule=self.schedule,
            task_table_name="ace3",
            due_from=Duration(days=30),
            due_by=Duration(days=60),
        )
        view = EditTaskScheduleItemView(self.req)
        view.object = item

        form_values = view.get_form_values()

        self.assertEqual(form_values[ViewParam.SCHEDULE_ID], self.schedule.id)
        self.assertEqual(
            form_values[ViewParam.TABLE_NAME], item.task_table_name
        )
        self.assertEqual(form_values[ViewParam.DUE_FROM], item.due_from)

        due_within = item.due_by - item.due_from
        self.assertEqual(form_values[ViewParam.DUE_WITHIN], due_within)

    def test_group_a_item_cannot_be_edited_by_group_b_admin(self) -> None:
        group_a = GroupFactory()
        group_b = GroupFactory()

        group_b_admin = self.req._debugging_user = UserFactory()
        UserGroupMembershipFactory(
            group_id=group_b.id, user_id=group_b_admin.id, groupadmin=True
        )

        group_a_schedule = TaskScheduleFactory(group=group_a)
        group_a_item = TaskScheduleItemFactory(task_schedule=group_a_schedule)

        view = EditTaskScheduleItemView(self.req)
        view.object = group_a_item

        with self.assertRaises(HTTPBadRequest) as cm:
            view.get_schedule()

        self.assertIn("not a group administrator", cm.exception.message)


class DeleteTaskScheduleItemViewTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.schedule = TaskScheduleFactory(group=self.group)

        self.schedule = TaskScheduleFactory()
        self.item = TaskScheduleItemFactory(
            task_schedule=self.schedule, task_table_name="ace3"
        )

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


class EditFinalizedPatientViewTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.group = AnyIdNumGroupFactory()
        user = self.req._debugging_user = UserFactory()

        UserGroupMembershipFactory(
            group_id=self.group.id,
            user_id=user.id,
            groupadmin=True,
            view_all_patients_when_unfiltered=True,
        )

    def test_raises_when_patient_does_not_exists(self) -> None:
        with self.assertRaises(HTTPBadRequest) as cm:
            edit_finalized_patient(self.req)

        self.assertEqual(
            str(cm.exception), "Cannot find Patient with _pk:None"
        )

    @unittest.skip("Can't save patient in database without group")
    def test_raises_when_patient_not_in_a_group(self) -> None:
        patient = PatientFactory(_group=None)

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_finalized_patient(self.req)

        self.assertEqual(str(cm.exception), "Bad patient: not in a group")

    def test_raises_when_not_authorized(self) -> None:
        patient = PatientFactory()

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
        patient = PatientFactory(_era=ERA_NOW, _group=self.group)

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_finalized_patient(self.req)

        self.assertIn("Patient is not editable", str(cm.exception))

    def test_patient_updated(self) -> None:
        patient = PatientFactory(_group=self.group)
        nhs_patient_idnum = NHSPatientIdNumFactory(patient=patient)

        self.req.add_get_params(
            {ViewParam.SERVER_PK: str(patient.pk)}, set_method_get=False
        )

        new_sex = Fake.en_gb.sex()
        new_forename = Fake.en_gb.forename(new_sex)
        new_surname = Fake.en_gb.last_name()
        new_address = Fake.en_gb.address()
        new_email = Fake.en_gb.email()
        new_gp = Fake.en_gb.name()
        new_other = Fake.en_us.paragraph()
        new_dob = Fake.en_gb.consistent_date_of_birth()
        new_nhs_number = Fake.en_gb.nhs_number()

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SERVER_PK, str(patient.pk)),
                (ViewParam.GROUP_ID, str(patient.group.id)),
                (ViewParam.FORENAME, new_forename),
                (ViewParam.SURNAME, new_surname),
                ("__start__", "dob:mapping"),
                ("date", new_dob),
                ("__end__", "dob:mapping"),
                ("__start__", "sex:rename"),
                ("deformField7", new_sex),
                ("__end__", "sex:rename"),
                (ViewParam.ADDRESS, new_address),
                (ViewParam.EMAIL, new_email),
                (ViewParam.GP, new_gp),
                (ViewParam.OTHER, new_other),
                ("__start__", "id_references:sequence"),
                ("__start__", "idnum_sequence:mapping"),
                (ViewParam.WHICH_IDNUM, nhs_patient_idnum.which_idnum),
                (ViewParam.IDNUM_VALUE, new_nhs_number),
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

        self.assertEqual(patient.forename, new_forename)
        self.assertEqual(patient.surname, new_surname)
        self.assertEqual(patient.dob, new_dob)
        self.assertEqual(patient.sex, new_sex)
        self.assertEqual(patient.address, new_address)
        self.assertEqual(patient.email, new_email)
        self.assertEqual(patient.gp, new_gp)
        self.assertEqual(patient.other, new_other)

        idnum = patient.get_idnum_objects()[0]
        self.assertEqual(idnum.patient_id, patient.id)
        self.assertEqual(idnum.which_idnum, nhs_patient_idnum.which_idnum)
        self.assertEqual(idnum.idnum_value, new_nhs_number)

        self.assertEqual(len(patient.special_notes), 1)
        note = patient.special_notes[0].note

        self.assertIn("Patient details edited", note)
        self.assertIn("forename", note)
        self.assertIn(new_forename, note)

        self.assertIn("surname", note)
        self.assertIn(new_surname, note)

        self.assertIn(f"idnum{nhs_patient_idnum.which_idnum}", note)
        self.assertIn(str(new_nhs_number), note)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)

        self.assertIn(
            f"Amended patient record with server PK {patient.pk}", messages[0]
        )
        self.assertIn("forename", messages[0])
        self.assertIn(new_forename, messages[0])

        self.assertIn("surname", messages[0])
        self.assertIn(new_surname, messages[0])

        self.assertIn("idnum1", messages[0])
        self.assertIn(str(new_nhs_number), messages[0])

    def test_message_when_no_changes(self) -> None:
        patient = PatientFactory(_group=self.group)

        patient_idnum = NHSPatientIdNumFactory(
            patient=patient,
        )
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
                (ViewParam.EMAIL, patient.email),
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
                (FormAction.SUBMIT, "submit"),
            ]
        )

        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound):
            edit_finalized_patient(self.req)

        messages = self.req.session.peek_flash(FlashQueue.INFO)

        self.assertIn("No changes required", messages[0])

    def test_template_rendered_with_values(self) -> None:
        patient = PatientFactory(_group=self.group)
        NHSPatientIdNumFactory(patient=patient)

        task1 = BmiFactory(patient=patient, _current=False)
        task2 = BmiFactory(patient=patient, _current=False)

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
        patient = PatientFactory()
        old_forename = patient.forename
        old_surname = patient.surname
        old_address = patient.address
        new_forename = Fake.en_gb.forename(patient.sex)
        new_surname = Fake.en_gb.last_name()
        new_address = Fake.en_gb.address()

        view.object = patient

        changes = OrderedDict()  # type: OrderedDict

        appstruct = {
            ViewParam.FORENAME: new_forename,
            ViewParam.SURNAME: new_surname,
            ViewParam.DOB: patient.dob,
            ViewParam.ADDRESS: new_address,
            ViewParam.OTHER: patient.other,
        }

        view._save_simple_params(appstruct, changes)

        self.assertEqual(
            changes[ViewParam.FORENAME], (old_forename, new_forename)
        )
        self.assertEqual(
            changes[ViewParam.SURNAME], (old_surname, new_surname)
        )
        self.assertNotIn(ViewParam.DOB, changes)
        self.assertEqual(
            changes[ViewParam.ADDRESS], (old_address, new_address)
        )
        self.assertNotIn(ViewParam.OTHER, changes)

    def test_changes_to_idrefs(self) -> None:
        view = EditFinalizedPatientView(self.req)
        patient = PatientFactory()
        nhs_patient_idnum = NHSPatientIdNumFactory(patient=patient)
        study_patient_idnum = StudyPatientIdNumFactory(patient=patient)
        rio_iddef = RioIdNumDefinitionFactory()
        new_nhs_number = Fake.en_gb.nhs_number()
        new_rio_number = 9999  # Below the range the factory would use

        view.object = patient

        changes = OrderedDict()  # type: OrderedDict

        appstruct = {
            ViewParam.ID_REFERENCES: [
                {
                    ViewParam.WHICH_IDNUM: nhs_patient_idnum.which_idnum,
                    ViewParam.IDNUM_VALUE: new_nhs_number,
                },
                {
                    ViewParam.WHICH_IDNUM: rio_iddef.which_idnum,
                    ViewParam.IDNUM_VALUE: new_rio_number,
                },
            ]
        }

        view._save_idrefs(appstruct, changes)

        nhs_key = f"idnum{nhs_patient_idnum.which_idnum} (NHS number)"
        self.assertIn(nhs_key, changes)

        study_key = f"idnum{study_patient_idnum.which_idnum} (Study number)"
        self.assertIn(study_key, changes)

        rio_key = f"idnum{rio_iddef.which_idnum} (RiO number)"
        self.assertIn(rio_key, changes)

        self.assertEqual(
            changes[nhs_key],
            (nhs_patient_idnum.idnum_value, new_nhs_number),
        )

        self.assertEqual(
            changes[study_key], (study_patient_idnum.idnum_value, None)
        )
        self.assertEqual(changes[rio_key], (None, new_rio_number))


class EditServerCreatedPatientViewTests(BasicDatabaseTestCase):
    def test_group_updated(self) -> None:
        patient = ServerCreatedPatientFactory(_group=self.group)
        old_group = patient.group
        new_group = GroupFactory()

        view = EditServerCreatedPatientView(self.req)
        view.object = patient

        appstruct = {ViewParam.GROUP_ID: new_group.id}

        view.save_object(appstruct)

        self.assertEqual(patient.group_id, new_group.id)

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)

        self.assertIn(old_group.name, messages[0])
        self.assertIn(new_group.name, messages[0])
        self.assertIn("group:", messages[0])

    def test_raises_when_not_created_on_the_server(self) -> None:
        patient = PatientFactory()

        view = EditServerCreatedPatientView(self.req)

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        with self.assertRaises(HTTPBadRequest) as cm:
            view.get_object()

        self.assertIn("Patient is not editable", str(cm.exception))

    def test_patient_task_schedules_updated(self) -> None:
        patient = ServerCreatedPatientFactory()
        nhs_patient_idnum = NHSPatientIdNumFactory(patient=patient)
        group = patient._group

        schedule1 = TaskScheduleFactory(group=group)
        schedule2 = TaskScheduleFactory(group=group)
        schedule3 = TaskScheduleFactory(group=group)

        PatientTaskScheduleFactory(
            patient=patient,
            task_schedule=schedule1,
            start_datetime=local(2020, 6, 12, 9),
            settings={
                "name 1": "value 1",
                "name 2": "value 2",
                "name 3": "value 3",
            },
        )

        PatientTaskScheduleFactory(
            patient=patient,
            task_schedule=schedule3,
        )
        self.req.add_get_params(
            {ViewParam.SERVER_PK: str(patient.pk)}, set_method_get=False
        )

        changed_schedule_1_settings = {
            "name 1": "new value 1",
            "name 2": "new value 2",
            "name 3": "new value 3",
        }
        changed_schedule_1_datetime = local(2020, 6, 19, 8, 0, 0)
        new_schedule_2_settings = {
            "name 4": "value 4",
            "name 5": "value 5",
            "name 6": "value 6",
        }
        new_schedule_2_datetime = local(2020, 7, 1, 13, 45, 0)
        new_nhs_number = Fake.en_gb.nhs_number()
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
                (ViewParam.WHICH_IDNUM, nhs_patient_idnum.which_idnum),
                (ViewParam.IDNUM_VALUE, str(new_nhs_number)),
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
                ("date", changed_schedule_1_datetime.to_date_string()),
                ("time", changed_schedule_1_datetime.to_time_string()),
                ("__end__", "start_datetime:mapping"),
                ("settings", json.dumps(changed_schedule_1_settings)),
                ("__end__", "task_schedule_sequence:mapping"),
                ("__start__", "task_schedule_sequence:mapping"),
                ("schedule_id", schedule2.id),
                ("__start__", "start_datetime:mapping"),
                ("date", new_schedule_2_datetime.to_date_string()),
                ("time", new_schedule_2_datetime.to_time_string()),
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
        self.assertIn(schedule1.name, schedules)
        self.assertIn(schedule2.name, schedules)
        self.assertNotIn(schedule3.name, schedules)

        self.assertEqual(
            schedules[schedule1.name].start_datetime,
            changed_schedule_1_datetime,
        )
        self.assertEqual(
            schedules[schedule1.name].settings, changed_schedule_1_settings
        )
        self.assertEqual(
            schedules[schedule2.name].start_datetime,
            new_schedule_2_datetime,
        )
        self.assertEqual(
            schedules[schedule2.name].settings, new_schedule_2_settings
        )

        messages = self.req.session.peek_flash(FlashQueue.SUCCESS)

        self.assertIn(
            f"Amended patient record with server PK {patient.pk}", messages[0]
        )
        self.assertIn("Task schedules", messages[0])

    def test_unprivileged_user_cannot_edit_patient(self) -> None:
        patient = ServerCreatedPatientFactory()

        self.req._debugging_user = UserFactory()

        view = EditServerCreatedPatientView(self.req)
        view.object = patient

        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertEqual(
            cm.exception.message, "Not authorized to edit this patient"
        )

    def test_patient_can_be_assigned_the_same_schedule_twice(self) -> None:
        patient = ServerCreatedPatientFactory()

        schedule1 = TaskScheduleFactory(group=self.group)

        pts = PatientTaskScheduleFactory(
            patient=patient,
            task_schedule=schedule1,
            start_datetime=local(2020, 6, 12, 12, 34),
        )

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

        changes: OrderedDict = OrderedDict()
        view._save_task_schedules(appstruct, changes)
        self.req.dbsession.commit()

        self.assertEqual(patient.task_schedules[0].task_schedule, schedule1)
        self.assertEqual(patient.task_schedules[1].task_schedule, schedule1)

    def test_form_values_for_existing_patient(self) -> None:
        patient = PatientFactory()

        schedule1 = TaskScheduleFactory(
            group=self.group,
        )

        patient_task_schedule = PatientTaskScheduleFactory(
            patient=patient,
            task_schedule=schedule1,
            start_datetime=local(2020, 6, 12),
            settings={
                "name 1": "value 1",
                "name 2": "value 2",
                "name 3": "value 3",
            },
        )

        patient_idnum = NHSPatientIdNumFactory(patient=patient)
        self.req.add_get_params({ViewParam.SERVER_PK: str(patient.pk)})

        view = EditServerCreatedPatientView(self.req)
        view.object = patient

        form_values = view.get_form_values()

        self.assertEqual(form_values[ViewParam.FORENAME], patient.forename)
        self.assertEqual(form_values[ViewParam.SURNAME], patient.surname)
        self.assertEqual(form_values[ViewParam.DOB], patient.dob)
        self.assertEqual(form_values[ViewParam.SEX], patient.sex)
        self.assertEqual(form_values[ViewParam.ADDRESS], patient.address)
        self.assertEqual(form_values[ViewParam.EMAIL], patient.email)
        self.assertEqual(form_values[ViewParam.GP], patient.gp)
        self.assertEqual(form_values[ViewParam.OTHER], patient.other)

        self.assertEqual(form_values[ViewParam.SERVER_PK], patient.pk)
        self.assertEqual(form_values[ViewParam.GROUP_ID], patient.group.id)

        idnum = form_values[ViewParam.ID_REFERENCES][0]
        self.assertEqual(
            idnum[ViewParam.WHICH_IDNUM],
            patient_idnum.which_idnum,
        )
        self.assertEqual(
            idnum[ViewParam.IDNUM_VALUE], patient_idnum.idnum_value
        )

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


class AddPatientViewTests(BasicDatabaseTestCase):
    def test_patient_created(self) -> None:
        view = AddPatientView(self.req)

        schedule1 = TaskScheduleFactory()
        schedule2 = TaskScheduleFactory()

        start_datetime1 = local(2020, 6, 12)
        start_datetime2 = local(2020, 7, 1)

        settings1 = json.dumps(
            {"name 1": "value 1", "name 2": "value 2", "name 3": "value 3"}
        )

        nhs_iddef = NHSIdNumDefinitionFactory()
        nhs_number = Fake.en_gb.nhs_number()

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
                    ViewParam.WHICH_IDNUM: nhs_iddef.which_idnum,
                    ViewParam.IDNUM_VALUE: nhs_number,
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
        self.dbsession.commit()

        patient = cast(Patient, view.object)

        server_device = Device.get_server_device(self.req.dbsession)

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
        self.assertEqual(idnum.patient_id, patient.id)
        self.assertEqual(idnum.which_idnum, nhs_iddef.which_idnum)
        self.assertEqual(idnum.idnum_value, nhs_number)

        patient_task_schedules = {
            pts.task_schedule.name: pts for pts in patient.task_schedules
        }

        self.assertIn(schedule1.name, patient_task_schedules)
        self.assertIn(schedule2.name, patient_task_schedules)

        self.assertEqual(
            patient_task_schedules[schedule1.name].start_datetime,
            start_datetime1,
        )
        self.assertEqual(
            patient_task_schedules[schedule1.name].settings, settings1
        )
        self.assertEqual(
            patient_task_schedules[schedule2.name].start_datetime,
            start_datetime2,
        )

    def test_patient_takes_next_available_id(self) -> None:
        ServerCreatedPatientFactory(id=1234)
        nhs_iddef = NHSIdNumDefinitionFactory()

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
                    ViewParam.WHICH_IDNUM: nhs_iddef.which_idnum,
                    ViewParam.IDNUM_VALUE: Fake.en_gb.nhs_number(),
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
        user = UserFactory(username="testuser")

        self.req._debugging_user = user

        with self.assertRaises(HTTPBadRequest) as cm:
            add_patient(self.req)

        self.assertEqual(
            cm.exception.message, "Not authorized to manage patients"
        )

    def test_group_listed_for_privileged_group_member(self) -> None:
        user = UserFactory()
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_manage_patients=True
        )

        self.req._debugging_user = user

        view = AddPatientView(self.req)

        with mock.patch.object(view, "render_to_response") as mock_render:
            view.dispatch()

        args, kwargs = mock_render.call_args

        context = args[0]

        self.assertIn(group.name, context["form"])


class DeleteServerCreatedPatientViewTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patient = ServerCreatedPatientFactory()

        idnum = ServerCreatedNHSPatientIdNumFactory(patient=self.patient)
        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)

        self.schedule = TaskScheduleFactory(group=self.group)

        PatientTaskScheduleFactory(
            patient=self.patient,
            task_schedule=self.schedule,
        )

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
        other_patient = ServerCreatedPatientFactory()
        patient_pk = other_patient._pk

        saved_patient = (
            self.dbsession.query(Patient)
            .filter(Patient._pk == patient_pk)
            .one_or_none()
        )

        self.assertIsNotNone(saved_patient)

        idnum = ServerCreatedNHSPatientIdNumFactory(patient=other_patient)

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

        PatientTaskScheduleFactory(
            patient=other_patient, task_schedule=self.schedule
        )

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

        user = UserFactory(username="testuser")

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

        user = UserFactory()

        self.req._debugging_user = user

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertEqual(
            cm.exception.message, "Not authorized to delete this patient"
        )


class EraseTaskTestCase(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patient = PatientFactory(_group=self.group)


class EraseTaskLeavingPlaceholderViewTests(EraseTaskTestCase):
    def test_displays_form(self) -> None:
        task = BmiFactory(patient=self.patient)
        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(task.pk),
                ViewParam.TABLE_NAME: task.tablename,
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
        task = BmiFactory(patient=self.patient)
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SERVER_PK, task.pk),
                (ViewParam.TABLE_NAME, task.tablename),
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
        with mock.patch.object(task, "manually_erase") as mock_manually_erase:

            with self.assertRaises(HTTPFound):
                view.dispatch()

        mock_manually_erase.assert_called_once()
        args, kwargs = mock_manually_erase.call_args
        request = args[0]

        self.assertEqual(request, self.req)

    def test_task_not_deleted_on_cancel(self) -> None:
        task = BmiFactory(patient=self.patient)
        self.req.fake_request_post_from_dict({FormAction.CANCEL: "cancel"})

        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(task.pk),
                ViewParam.TABLE_NAME: task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPFound):
            view.dispatch()

        task = self.dbsession.query(task.__class__).one_or_none()

        self.assertIsNotNone(task)

    def test_redirect_on_cancel(self) -> None:
        task = BmiFactory(patient=self.patient)
        self.req.fake_request_post_from_dict({FormAction.CANCEL: "cancel"})

        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(task.pk),
                ViewParam.TABLE_NAME: task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPFound) as cm:
            view.dispatch()

        self.assertEqual(cm.exception.status_code, 302)
        self.assertIn(f"/{Routes.TASK}", cm.exception.headers["Location"])
        self.assertIn(
            f"{ViewParam.TABLE_NAME}={task.tablename}",
            cm.exception.headers["Location"],
        )
        self.assertIn(
            f"{ViewParam.SERVER_PK}={task.pk}",
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
        task = BmiFactory(patient=self.patient, _era=ERA_NOW)

        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(task.pk),
                ViewParam.TABLE_NAME: task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("Task is live on tablet", cm.exception.message)

    def test_raises_when_user_not_authorized_to_erase(self) -> None:
        task = BmiFactory(patient=self.patient)
        user = UserFactory()

        self.req._debugging_user = user
        UserGroupMembershipFactory(
            user_id=user.id, group_id=self.group.id, groupadmin=True
        )

        with mock.patch.object(
            user, "authorized_to_erase_tasks", return_value=False
        ):
            self.req.add_get_params(
                {
                    ViewParam.SERVER_PK: str(task.pk),
                    ViewParam.TABLE_NAME: task.tablename,
                },
                set_method_get=False,
            )
            view = EraseTaskLeavingPlaceholderView(self.req)

            with self.assertRaises(HTTPBadRequest) as cm:
                view.dispatch()

        self.assertIn("Not authorized to erase tasks", cm.exception.message)

    def test_raises_when_task_already_erased(self) -> None:
        task = BmiFactory(patient=self.patient, _manually_erased=True)

        self.req.add_get_params(
            {
                ViewParam.SERVER_PK: str(task.pk),
                ViewParam.TABLE_NAME: task.tablename,
            },
            set_method_get=False,
        )
        view = EraseTaskLeavingPlaceholderView(self.req)

        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("already erased", cm.exception.message)


class EraseTaskEntirelyViewTests(EraseTaskTestCase):
    def test_deletes_task_entirely(self) -> None:
        task = BmiFactory(patient=self.patient)
        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.SERVER_PK, task.pk),
                (ViewParam.TABLE_NAME, task.tablename),
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
            task, "delete_entirely"
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
        self.assertIn(task.tablename, messages[0])
        self.assertIn("server PK {}".format(task.pk), messages[0])


class EditGroupViewTests(DemoRequestTestCase):
    def test_group_updated(self) -> None:
        groupadmin = self.req._debugging_user = UserFactory()
        group = GroupFactory()
        UserGroupMembershipFactory(
            group_id=group.id, user_id=groupadmin.id, groupadmin=True
        )
        other_group_1 = GroupFactory()
        other_group_2 = GroupFactory()

        nhs_iddef = NHSIdNumDefinitionFactory()

        new_name = "new-name"
        new_description = "new description"
        new_upload_policy = "anyidnum AND sex"
        new_finalize_policy = f"idnum{nhs_iddef.which_idnum} AND sex"

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.GROUP_ID, group.id),
                (ViewParam.NAME, new_name),
                (ViewParam.DESCRIPTION, new_description),
                (ViewParam.UPLOAD_POLICY, new_upload_policy),
                (ViewParam.FINALIZE_POLICY, new_finalize_policy),
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

        self.assertEqual(group.name, new_name)
        self.assertEqual(group.description, new_description)
        self.assertEqual(group.upload_policy, new_upload_policy)
        self.assertEqual(group.finalize_policy, new_finalize_policy)
        self.assertIn(other_group_1, group.can_see_other_groups)
        self.assertIn(other_group_2, group.can_see_other_groups)

    def test_ip_use_added(self) -> None:
        from camcops_server.cc_modules.cc_ipuse import IpContexts

        group = GroupFactory()
        groupadmin = self.req._debugging_user = UserFactory()
        UserGroupMembershipFactory(
            group_id=group.id, user_id=groupadmin.id, groupadmin=True
        )
        nhs_iddef = NHSIdNumDefinitionFactory()

        new_name = "new-name"
        new_description = "new description"
        new_upload_policy = "anyidnum AND sex"
        new_finalize_policy = f"idnum{nhs_iddef.which_idnum} AND sex"

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.GROUP_ID, group.id),
                (ViewParam.NAME, new_name),
                (ViewParam.DESCRIPTION, new_description),
                (ViewParam.UPLOAD_POLICY, new_upload_policy),
                (ViewParam.FINALIZE_POLICY, new_finalize_policy),
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

        self.assertTrue(group.ip_use.clinical)
        self.assertTrue(group.ip_use.commercial)
        self.assertFalse(group.ip_use.educational)
        self.assertFalse(group.ip_use.research)

    def test_ip_use_updated(self) -> None:
        from camcops_server.cc_modules.cc_ipuse import IpContexts

        group = GroupFactory(ip_use__educational=True, ip_use__research=True)
        groupadmin = self.req._debugging_user = UserFactory()
        UserGroupMembershipFactory(
            group_id=group.id, user_id=groupadmin.id, groupadmin=True
        )

        old_id = group.ip_use.id

        nhs_iddef = NHSIdNumDefinitionFactory()

        new_name = "new-name"
        new_description = "new description"
        new_upload_policy = "anyidnum AND sex"
        new_finalize_policy = f"idnum{nhs_iddef.which_idnum} AND sex"

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.GROUP_ID, group.id),
                (ViewParam.NAME, new_name),
                (ViewParam.DESCRIPTION, new_description),
                (ViewParam.UPLOAD_POLICY, new_upload_policy),
                (ViewParam.FINALIZE_POLICY, new_finalize_policy),
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

        self.assertTrue(group.ip_use.clinical)
        self.assertTrue(group.ip_use.commercial)
        self.assertFalse(group.ip_use.educational)
        self.assertFalse(group.ip_use.research)
        self.assertEqual(group.ip_use.id, old_id)

    def test_other_groups_displayed_in_form(self) -> None:
        z_group = GroupFactory(name="z-group")
        a_group = GroupFactory(name="a-group")

        other_groups = Group.get_groups_from_id_list(
            self.dbsession, [z_group.id, a_group.id]
        )
        group = GroupFactory(can_see_other_groups=other_groups)

        view = EditGroupView(self.req)
        view.object = group

        form_values = view.get_form_values()

        self.assertEqual(
            form_values[ViewParam.GROUP_IDS], [a_group.id, z_group.id]
        )

    def test_group_id_displayed_in_form(self) -> None:
        group = GroupFactory()
        view = EditGroupView(self.req)
        view.object = group

        form_values = view.get_form_values()

        self.assertEqual(form_values[ViewParam.GROUP_ID], group.id)

    def test_ip_use_displayed_in_form(self) -> None:
        group = GroupFactory()
        view = EditGroupView(self.req)
        view.object = group

        form_values = view.get_form_values()

        self.assertEqual(form_values[ViewParam.IP_USE], group.ip_use)


class SendEmailFromPatientTaskScheduleViewTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patient = ServerCreatedPatientFactory()
        idnum = ServerCreatedNHSPatientIdNumFactory(patient=self.patient)

        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)

        self.schedule = TaskScheduleFactory(group=self.group)

        self.pts = PatientTaskScheduleFactory(
            patient=self.patient, task_schedule=self.schedule
        )

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
        user = UserFactory(username="testuser")

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


class ViewPatientTaskScheduleTests(BasicDatabaseTestCase):
    def test_patient_listed_with_no_tasks(self) -> None:
        patient = ServerCreatedPatientFactory(_group=self.group)
        schedule = TaskScheduleFactory(group=self.group)

        pts = PatientTaskScheduleFactory(
            patient=patient, task_schedule=schedule
        )
        self.req.add_get_params(
            {ViewParam.PATIENT_TASK_SCHEDULE_ID: str(pts.id)}
        )

        view_dict = view_patient_task_schedule(self.req)

        self.assertEqual(view_dict["pts"], pts)
        self.assertEqual(
            view_dict["patient_descriptor"], patient.prettystr(self.req)
        )
        self.assertEqual(view_dict["task_list"], [])


class ViewPatientTaskSchedulesTests(BasicDatabaseTestCase):
    def test_patients_listed_alphabetically(self) -> None:
        patient_a = ServerCreatedPatientFactory(
            surname="alvarez", _group=self.group
        )
        patient_b = ServerCreatedPatientFactory(
            surname="brown", _group=self.group
        )
        patient_c = ServerCreatedPatientFactory(
            surname="chang", _group=self.group
        )

        schedule_1 = TaskScheduleFactory(group=self.group)
        schedule_2 = TaskScheduleFactory(group=self.group)

        PatientTaskScheduleFactory(patient=patient_a, task_schedule=schedule_1)
        PatientTaskScheduleFactory(
            patient=patient_a,
            task_schedule=schedule_2,
        )
        PatientTaskScheduleFactory(
            patient=patient_b,
            task_schedule=schedule_1,
        )
        PatientTaskScheduleFactory(
            patient=patient_c,
            task_schedule=schedule_1,
        )

        patients = view_patient_task_schedules(self.req)["page"].collection

        self.assertEqual(patients[0].surname, "alvarez")
        self.assertEqual(patients[1].surname, "brown")
        self.assertEqual(patients[2].surname, "chang")


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
        user = UserFactory(
            username="test", password__request=self.req, password="secret"
        )
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
        user = UserFactory(
            username="test", password__request=self.req, password="secret"
        )
        UserGroupMembershipFactory(
            user_id=user.id, group_id=self.group.id, may_use_webviewer=True
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
        user = UserFactory(
            username="test",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.TOTP,
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

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
        user = UserFactory(
            username="test",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_EMAIL,
            email="user@example.com",
            hotp_counter=0,
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )
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

        phone_number_str = Fake.en_gb.valid_phone_number()
        user = UserFactory(
            username="test",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            phone_number=phonenumbers.parse(phone_number_str),
            hotp_counter=0,
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

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
        user = UserFactory(
            username="test",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_EMAIL,
            email="user@example.com",
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
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

        user = UserFactory(
            username="test",
            email="user@example.com",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_EMAIL,
            hotp_counter=0,
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
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

        phone_number_str = Fake.en_gb.valid_phone_number()
        user = UserFactory(
            username="test",
            email="user@example.com",
            phone_number=phonenumbers.parse(phone_number_str),
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            hotp_counter=0,
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
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
        expected_code = pyotp.HOTP(user.mfa_secret_key).at(1)

        with self.assertLogs(level=logging.INFO) as logging_cm:
            view.dispatch()

        expected_message = f"Your CamCOPS verification code is {expected_code}"

        self.assertIn(
            ConsoleSmsBackend.make_msg(phone_number_str, expected_message),
            logging_cm.output[0],
        )

    @mock.patch("camcops_server.cc_modules.cc_email.send_msg")
    @mock.patch("camcops_server.cc_modules.cc_email.make_email")
    def test_login_with_hotp_increments_counter(
        self, mock_make_email: mock.Mock, mock_send_msg: mock.Mock
    ) -> None:
        user = UserFactory(
            username="test",
            email="user@example.com",
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_EMAIL,
            hotp_counter=0,
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
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

        view.dispatch()

        self.assertEqual(user.hotp_counter, 1)

    @mock.patch("camcops_server.cc_modules.webview.audit")
    def test_user_with_totp_can_log_in(self, mock_audit: mock.Mock) -> None:
        user = UserFactory(
            username="test",
            mfa_method=MfaMethod.TOTP,
            mfa_secret_key=pyotp.random_base32(),
            password__request=self.req,
            password="secret",
        )

        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

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
        user = UserFactory(
            username="test",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=1,
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

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
        user = UserFactory(
            username="test",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=1,
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

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
        user = UserFactory(
            username="test",
            mfa_method=MfaMethod.TOTP,
            mfa_secret_key=pyotp.random_base32(),
            password__request=self.req,
            password="secret",
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=user.id, group_id=group.id, may_use_webviewer=True
        )

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
        user = UserFactory(
            username="test", password__request=self.req, password="secret"
        )
        UserGroupMembershipFactory(
            user_id=user.id, group_id=self.group.id, may_use_webviewer=False
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

        user = UserFactory(username="test")
        # Should never be the case that we have a user ID but no
        # authentication time
        view.state["mfa_user_id"] = user.id

        self.assertFalse(view.timed_out())


class EditUserViewTests(BasicDatabaseTestCase):
    def test_redirect_on_cancel(self) -> None:
        regular_user = UserFactory(username="regular_user")
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
        self.req.add_get_params({ViewParam.USER_ID: str(self.system_user.id)})

        regular_user = UserFactory(username="regular_user")
        self.req._debugging_user = regular_user
        with self.assertRaises(HTTPBadRequest) as cm:
            edit_user(self.req)

        self.assertIn("Nobody may edit the system user", cm.exception.message)

    def test_superuser_sees_full_form(self) -> None:
        superuser = UserFactory(username="admin", superuser=True)
        self.req._debugging_user = superuser

        self.req.add_get_params({ViewParam.USER_ID: str(superuser.id)})

        response = edit_user(self.req)

        self.assertIn("Superuser (CAUTION!)", response.body.decode(UTF8))

    def test_groupadmin_sees_groupadmin_form(self) -> None:
        groupadmin = UserFactory(username="groupadmin")
        regular_user = UserFactory(username="regular_user")
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=groupadmin.id, group_id=group.id, groupadmin=True
        )
        UserGroupMembershipFactory(user_id=regular_user.id, group_id=group.id)
        self.req._debugging_user = groupadmin

        self.req.add_get_params({ViewParam.USER_ID: str(regular_user.id)})

        response = edit_user(self.req)
        content = response.body.decode(UTF8)

        self.assertIn("Full name", content)
        self.assertNotIn("Superuser (CAUTION!)", content)

    def test_raises_for_conflicting_user_name(self) -> None:
        UserFactory(username="existing_user")
        other_user = UserFactory(username="other_user")

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
        user = UserFactory(
            username="old_username",
            fullname="Old Name",
            email="old@example.com",
            language="da_DK",
        )

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
        user = UserFactory()
        group = GroupFactory()

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
        regular_user = UserFactory(username="regular_user")
        group_b_admin = UserFactory(username="group_b_admin")
        group_a = GroupFactory()
        group_b = GroupFactory()
        UserGroupMembershipFactory(
            user_id=regular_user.id, group_id=group_a.id
        )
        UserGroupMembershipFactory(
            user_id=regular_user.id, group_id=group_b.id
        )
        UserGroupMembershipFactory(
            user_id=group_b_admin.id, group_id=group_b.id, groupadmin=True
        )
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

        [actual_group_ids] = mock_set_group_ids.call_args[0]
        self.assertEqual(
            sorted(actual_group_ids), sorted([group_a.id, group_b.id])
        )

    def test_upload_group_id_unset_when_membership_removed(self) -> None:
        group_a = GroupFactory()
        group_b = GroupFactory()
        regular_user = UserFactory(upload_group=group_a)
        groupadmin = UserFactory()
        UserGroupMembershipFactory(
            group_id=group_a.id, user_id=regular_user.id
        )
        UserGroupMembershipFactory(
            group_id=group_b.id, user_id=regular_user.id
        )
        UserGroupMembershipFactory(
            group_id=group_a.id, user_id=groupadmin.id, groupadmin=True
        )
        UserGroupMembershipFactory(
            group_id=group_b.id, user_id=groupadmin.id, groupadmin=True
        )
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
        regular_user = UserFactory(
            username="regular_user",
            fullname="Full Name",
            email="user@example.com",
            language="da_DK",
        )
        group_b_admin = UserFactory(username="group_b_admin")
        group_a = GroupFactory()
        group_b = GroupFactory()
        UserGroupMembershipFactory(
            user_id=regular_user.id, group_id=group_a.id
        )
        UserGroupMembershipFactory(
            user_id=regular_user.id, group_id=group_b.id
        )
        UserGroupMembershipFactory(
            user_id=group_b_admin.id, group_id=group_b.id, groupadmin=True
        )
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
        regular_user = UserFactory(
            username="regular_user",
            mfa_method=MfaMethod.HOTP_EMAIL,
            email="user@example.com",
        )

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
        regular_user = UserFactory(
            username="regular_user", mfa_method=MfaMethod.HOTP_SMS
        )
        self.req._debugging_user = regular_user
        view = EditOwnUserMfaView(self.req)

        # Would normally be set when going through dispatch()
        view.object = regular_user

        form_values = view.get_form_values()

        self.assertEqual(
            form_values[ViewParam.MFA_METHOD], regular_user.mfa_method
        )

    def test_get_form_values_hotp_email(self) -> None:
        regular_user = UserFactory(
            username="regular_user",
            mfa_method=MfaMethod.HOTP_EMAIL,
            email="regular_user@example.com",
        )
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
        regular_user = UserFactory(
            username="regular_user",
            mfa_method=MfaMethod.HOTP_SMS,
            phone_number=phonenumbers.parse(Fake.en_gb.valid_phone_number()),
        )
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
        regular_user = UserFactory(
            username="regular_user", mfa_method=MfaMethod.TOTP
        )
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
        regular_user = UserFactory(username="regular_user")
        regular_user.mfa_method = MfaMethod.TOTP
        regular_user.ensure_mfa_info()
        # ... otherwise, the absence of e.g. the HOTP counter will cause a
        # secret key reset.
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
        regular_user = UserFactory(username="regular_user")
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
        regular_user = UserFactory(username="regular_user")
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
        regular_user = UserFactory(username="regular_user")
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
        regular_user = UserFactory(
            username="regular_user", mfa_method=MfaMethod.TOTP
        )
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
        regular_user = UserFactory(username="regular_user")
        regular_user.mfa_method = MfaMethod.HOTP_SMS

        phone_number_str = Fake.en_gb.valid_phone_number()

        multidict = MultiDict(
            [
                (ViewParam.PHONE_NUMBER, phone_number_str),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)
        self.req.config.mfa_methods = [MfaMethod.HOTP_SMS]

        view = EditOwnUserMfaView(self.req)
        view.state.update(step=EditOwnUserMfaView.STEP_HOTP_SMS)

        view.dispatch()

        self.assertEqual(
            regular_user.phone_number, phonenumbers.parse(phone_number_str)
        )

    def test_user_can_set_email_address(self) -> None:
        regular_user = UserFactory(username="regular_user")
        # We're going to force this user to the e-mail verification step, so
        # we need to ensure it's set to use e-mail MFA:
        regular_user.mfa_method = MfaMethod.HOTP_EMAIL
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
        regular_user = UserFactory(username="regular_user")
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
            {ViewParam.USER_ID: str(self.system_user.id)}, set_method_get=False
        )

        view = ChangeOtherPasswordView(self.req)
        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("Nobody may edit the system user", cm.exception.message)

    def test_password_set(self) -> None:
        groupadmin = UserFactory(username="groupadmin")
        regular_user = UserFactory(username="regular_user")
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=groupadmin.id, group_id=group.id, groupadmin=True
        )
        UserGroupMembershipFactory(user_id=regular_user.id, group_id=group.id)

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
        groupadmin = UserFactory(username="groupadmin")
        regular_user = UserFactory(username="regular_user")
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=groupadmin.id, group_id=group.id, groupadmin=True
        )
        UserGroupMembershipFactory(user_id=regular_user.id, group_id=group.id)
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
        superuser = UserFactory(username="admin", superuser=True)
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
        superuser = UserFactory(
            username="admin",
            superuser=True,
            email="admin@example.com",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=0,
        )

        user = UserFactory(username="user")
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

        phone_number_str = Fake.en_gb.valid_phone_number()
        superuser = UserFactory(
            username="admin",
            superuser=True,
            email="admin@example.com",
            phone_number=phonenumbers.parse(phone_number_str),
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            hotp_counter=0,
        )
        user = UserFactory(username="user", email="user@example.com")
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
            ConsoleSmsBackend.make_msg(phone_number_str, expected_message),
            logging_cm.output[0],
        )

    def test_user_can_enter_token(self) -> None:
        superuser = UserFactory(
            username="admin",
            superuser=True,
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user = UserFactory(username="user", email="user@example.com")
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
        superuser = UserFactory(
            username="superuser",
            superuser=True,
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user = UserFactory(username="user", email="user@example.com")
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
        superuser = UserFactory(
            username="admin",
            superuser=True,
            mfa_method=MfaMethod.TOTP,
            mfa_secret_key=pyotp.random_base32(),
        )
        user = UserFactory(username="user")
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
        regular_user = UserFactory(username="regular_user")
        multidict = MultiDict([(FormAction.SUBMIT, "submit")])
        self.req._debugging_user = regular_user
        self.req.fake_request_post_from_dict(multidict)

        self.req.add_get_params(
            {ViewParam.USER_ID: str(self.system_user.id)}, set_method_get=False
        )

        view = EditOtherUserMfaView(self.req)
        with self.assertRaises(HTTPBadRequest) as cm:
            view.dispatch()

        self.assertIn("Nobody may edit the system user", cm.exception.message)

    def test_disable_mfa(self) -> None:
        groupadmin = UserFactory(username="groupadmin")
        regular_user = UserFactory(
            username="regular_user", mfa_method=MfaMethod.TOTP
        )
        group = GroupFactory()
        UserGroupMembershipFactory(
            user_id=groupadmin.id, group_id=group.id, groupadmin=True
        )
        UserGroupMembershipFactory(user_id=regular_user.id, group_id=group.id)
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
        superuser = UserFactory(username="admin", superuser=True)
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
        superuser = UserFactory(
            username="admin",
            superuser=True,
            email="admin@example.com",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            hotp_counter=0,
        )

        user = UserFactory(username="user")
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

        phone_number_str = Fake.en_gb.valid_phone_number()
        superuser = UserFactory(
            username="admin",
            superuser=True,
            email="admin@example.com",
            phone_number=phonenumbers.parse(phone_number_str),
            mfa_secret_key=pyotp.random_base32(),
            mfa_method=MfaMethod.HOTP_SMS,
            hotp_counter=0,
        )
        user = UserFactory(username="user", email="user@example.com")
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
            ConsoleSmsBackend.make_msg(phone_number_str, expected_message),
            logging_cm.output[0],
        )

    def test_user_can_enter_token(self) -> None:
        superuser = UserFactory(
            username="admin",
            superuser=True,
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user = UserFactory(username="user", email="user@example.com")
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
        superuser = UserFactory(
            username="superuser",
            superuser=True,
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
        )
        user = UserFactory(username="user", email="user@example.com")
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


class EditUserGroupMembershipViewTests(DemoRequestTestCase):
    def test_superuser_can_update_user_group_membership(self) -> None:
        regular_user = UserFactory()
        groupadmin = UserFactory()
        group = GroupFactory()

        UserGroupMembershipFactory(
            user_id=groupadmin.id,
            group_id=group.id,
            groupadmin=True,
        )

        ugm = UserGroupMembershipFactory(
            user_id=regular_user.id, group_id=group.id
        )

        self.req._debugging_user = groupadmin

        self.assertFalse(ugm.may_upload)
        self.assertFalse(ugm.may_register_devices)
        self.assertFalse(ugm.may_use_webviewer)
        self.assertFalse(ugm.view_all_patients_when_unfiltered)
        self.assertFalse(ugm.may_dump_data)
        self.assertFalse(ugm.may_run_reports)
        self.assertFalse(ugm.may_add_notes)
        self.assertFalse(ugm.may_manage_patients)
        self.assertFalse(ugm.may_email_patients)
        self.assertFalse(ugm.groupadmin)

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
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(ugm.id)},
            set_method_get=False,
        )

        with self.assertRaises(HTTPFound):
            edit_user_group_membership(self.req)

        self.assertTrue(ugm.may_upload)
        self.assertTrue(ugm.may_register_devices)
        self.assertTrue(ugm.may_use_webviewer)
        self.assertTrue(ugm.view_all_patients_when_unfiltered)
        self.assertTrue(ugm.may_dump_data)
        self.assertTrue(ugm.may_run_reports)
        self.assertTrue(ugm.may_add_notes)
        self.assertTrue(ugm.may_manage_patients)
        self.assertTrue(ugm.may_email_patients)

    def test_groupadmin_can_update_user_group_membership(self) -> None:
        regular_user = UserFactory()
        groupadmin = UserFactory()
        group = GroupFactory()

        UserGroupMembershipFactory(
            user_id=groupadmin.id,
            group_id=group.id,
            groupadmin=True,
        )

        ugm = UserGroupMembershipFactory(
            user_id=regular_user.id, group_id=group.id
        )

        self.req._debugging_user = groupadmin

        self.assertFalse(ugm.may_upload)
        self.assertFalse(ugm.may_register_devices)
        self.assertFalse(ugm.may_use_webviewer)
        self.assertFalse(ugm.view_all_patients_when_unfiltered)
        self.assertFalse(ugm.may_dump_data)
        self.assertFalse(ugm.may_run_reports)
        self.assertFalse(ugm.may_add_notes)
        self.assertFalse(ugm.may_manage_patients)
        self.assertFalse(ugm.may_email_patients)

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
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(ugm.id)},
            set_method_get=False,
        )

        with self.assertRaises(HTTPFound):
            edit_user_group_membership(self.req)

        self.assertTrue(ugm.may_upload)
        self.assertTrue(ugm.may_register_devices)
        self.assertTrue(ugm.may_use_webviewer)
        self.assertTrue(ugm.view_all_patients_when_unfiltered)
        self.assertTrue(ugm.may_dump_data)
        self.assertTrue(ugm.may_run_reports)
        self.assertTrue(ugm.may_add_notes)
        self.assertTrue(ugm.may_manage_patients)
        self.assertTrue(ugm.may_email_patients)

    def test_raises_if_cant_edit_user(self) -> None:
        system_user = User.get_system_user(self.dbsession)
        groupadmin = UserFactory()
        group = GroupFactory()

        UserGroupMembershipFactory(
            user_id=groupadmin.id,
            group_id=group.id,
            groupadmin=True,
        )

        system_ugm = UserGroupMembershipFactory(
            user_id=system_user.id, group_id=group.id
        )

        self.req._debugging_user = groupadmin

        multidict = MultiDict([(FormAction.SUBMIT, "submit")])

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(system_ugm.id)},
            set_method_get=False,
        )

        with self.assertRaises(HTTPBadRequest) as cm:
            edit_user_group_membership(self.req)

        self.assertIn("Nobody may edit the system user", cm.exception.message)

    def test_raises_if_cant_administer_group(self) -> None:
        group_a = GroupFactory()
        group_b = GroupFactory()

        user1 = UserFactory()
        user2 = UserFactory()

        # User 1 is a group administrator for group A,
        # User 2 is a member if group A
        UserGroupMembershipFactory(
            user_id=user1.id, group_id=group_a.id, groupadmin=True
        )
        UserGroupMembershipFactory(user_id=user2.id, group_id=group_a.id),

        # User 1 is not an administrator of group B
        # User 2 is a member of group B
        ugm = UserGroupMembershipFactory(user_id=user2.id, group_id=group_b.id)

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
        regular_user = UserFactory()
        groupadmin = UserFactory()
        group = GroupFactory()

        UserGroupMembershipFactory(
            user_id=groupadmin.id,
            group_id=group.id,
            groupadmin=True,
        )

        ugm = UserGroupMembershipFactory(
            user_id=regular_user.id, group_id=group.id
        )

        self.req._debugging_user = groupadmin
        multidict = MultiDict([(FormAction.CANCEL, "cancel")])

        self.req.fake_request_post_from_dict(multidict)
        self.req.add_get_params(
            {ViewParam.USER_GROUP_MEMBERSHIP_ID: str(ugm.id)},
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

        user = UserFactory(
            username="user",
            mfa_method=MfaMethod.NO_MFA,
            password__request=self.req,
            password="secret",
        )
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
        user = UserFactory(
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
        user = UserFactory(
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
        phone_number_str = Fake.en_gb.valid_phone_number()
        user = UserFactory(
            username="user",
            email="user@example.com",
            phone_number=phonenumbers.parse(phone_number_str),
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
            ConsoleSmsBackend.make_msg(phone_number_str, expected_message),
            logging_cm.output[0],
        )

    def test_user_can_enter_token(self) -> None:
        user = UserFactory(
            username="user",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
            password__request=self.req,
            password="secret",
        )
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
        user = UserFactory(
            username="user",
            mfa_method=MfaMethod.HOTP_EMAIL,
            mfa_secret_key=pyotp.random_base32(),
            email="user@example.com",
            hotp_counter=1,
            password__request=self.req,
            password="secret",
        )
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
        user = UserFactory(
            username="user",
            mfa_method=MfaMethod.TOTP,
            mfa_secret_key=pyotp.random_base32(),
            password__request=self.req,
            password="secret",
        )
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


class AddUserTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.groupadmin = self.req._debugging_user = UserFactory()

    def test_user_created(self) -> None:
        group_1 = GroupFactory()
        group_2 = GroupFactory()

        UserGroupMembershipFactory(
            user_id=self.groupadmin.id, group_id=group_1.id, groupadmin=True
        )
        UserGroupMembershipFactory(
            user_id=self.groupadmin.id, group_id=group_2.id, groupadmin=True
        )

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.USERNAME, "test"),
                ("__start__", "new_password:mapping"),
                (ViewParam.NEW_PASSWORD, "monkeybusiness"),
                ("new_password-confirm", "monkeybusiness"),
                ("__end__", "new_password:mapping"),
                (ViewParam.MUST_CHANGE_PASSWORD, "true"),
                ("__start__", "group_ids:sequence"),
                ("group_id_sequence", str(group_1.id)),
                ("group_id_sequence", str(group_2.id)),
                ("__end__", "group_ids:sequence"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound):
            add_user(self.req)

        user = (
            self.dbsession.query(User)
            .filter(
                User.username == "test",
            )
            .one_or_none()
        )

        self.assertIsNotNone(user)

        self.assertTrue(user.must_change_password)
        self.assertIn(group_1.id, user.group_ids)
        self.assertIn(group_2.id, user.group_ids)


class ForciblyFinalizeTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.req._debugging_user = self.groupadmin

    def test_cancel_returns_to_home(self) -> None:
        multidict = MultiDict([(FormAction.CANCEL, "cancel")])
        self.req.fake_request_post_from_dict(multidict)

        exc = forcibly_finalize(self.req)
        self.assertIsInstance(exc, HTTPFound)
        self.assertEqual(exc.status_code, 302)
        self.assertEqual(urlparse(exc.headers["Location"]).path, "/")

    def test_renders_first_form_on_get(self) -> None:
        mock_render = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.webview", render_to_response=mock_render
        ):
            forcibly_finalize(self.req)

        args, kwargs = mock_render.call_args
        context = args[1]

        self.assertIn("form", context)
        self.assertIn("<select", context["form"])

    def test_renders_confirm_form_on_submit(self) -> None:
        device = DeviceFactory()

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.DEVICE_ID, device.id),
                ("__start__", "danger:mapping"),
                ("target", "7176"),
                ("user_entry", "7176"),
                ("__end__", "danger:mapping"),
                (FormAction.SUBMIT, "submit"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        mock_render = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.webview", render_to_response=mock_render
        ):
            forcibly_finalize(self.req)

        args, kwargs = mock_render.call_args
        context = args[1]

        self.assertIn("form", context)
        self.assertIn("Forcibly finalize", context["form"])

    def test_finalizes_on_submit(self) -> None:
        device = DeviceFactory()
        patient = PatientFactory(_device=device, _group=self.group)
        bmis = BmiFactory.create_batch(3, patient=patient, _era=ERA_NOW)

        multidict = MultiDict(
            [
                ("_charset_", UTF8),
                ("__formid__", "deform"),
                (ViewParam.CSRF_TOKEN, self.req.session.get_csrf_token()),
                (ViewParam.DEVICE_ID, device.id),
                ("confirm_1_t", "true"),
                ("confirm_2_t", "true"),
                ("confirm_4_t", "true"),
                ("__start__", "danger:mapping"),
                ("target", "7176"),
                ("user_entry", "7176"),
                ("__end__", "danger:mapping"),
                (FormAction.FINALIZE, "Forcibly finalize"),
            ]
        )
        self.req.fake_request_post_from_dict(multidict)

        with self.assertRaises(HTTPFound) as cm:
            forcibly_finalize(self.req)

        self.assertEqual(cm.exception.status_code, 302)
        self.assertEqual(urlparse(cm.exception.headers["Location"]).path, "/")

        for bmi in bmis:
            self.assertEqual(bmi._preserving_user_id, self.groupadmin.id)
            self.assertTrue(bmi._forcibly_preserved)
