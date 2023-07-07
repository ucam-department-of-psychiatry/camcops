#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_taskschedule_tests.py

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

from urllib.parse import parse_qs, urlsplit

from cardinal_pythonlib.uriconst import UriSchemes
from pendulum import Duration

from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_pyramid import Routes
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    PatientTaskScheduleEmail,
    TaskSchedule,
    TaskScheduleItem,
)
from camcops_server.cc_modules.cc_unittest import (
    DemoDatabaseTestCase,
    DemoRequestTestCase,
)


# =============================================================================
# Unit tests
# =============================================================================


class TaskScheduleTests(DemoDatabaseTestCase):
    def test_deleting_deletes_related_objects(self) -> None:
        schedule = TaskSchedule()
        schedule.group_id = self.group.id
        self.dbsession.add(schedule)
        self.dbsession.flush()

        item = TaskScheduleItem()
        item.schedule_id = schedule.id
        item.task_table_name = "ace3"
        item.due_from = Duration(days=30)
        item.due_by = Duration(days=60)
        self.dbsession.add(item)
        self.dbsession.flush()

        patient = self.create_patient()

        pts = PatientTaskSchedule()
        pts.schedule_id = schedule.id
        pts.patient_pk = patient.pk
        self.dbsession.add(pts)
        self.dbsession.flush()

        email = Email()
        self.dbsession.add(email)
        self.dbsession.flush()

        pts_email = PatientTaskScheduleEmail()
        pts_email.email_id = email.id
        pts_email.patient_task_schedule_id = pts.id
        self.dbsession.add(pts_email)
        self.dbsession.commit()

        self.assertIsNotNone(
            self.dbsession.query(TaskScheduleItem)
            .filter(TaskScheduleItem.id == item.id)
            .one_or_none()
        )
        self.assertIsNotNone(
            self.dbsession.query(PatientTaskSchedule)
            .filter(PatientTaskSchedule.id == pts.id)
            .one_or_none()
        )
        self.assertIsNotNone(
            self.dbsession.query(PatientTaskScheduleEmail)
            .filter(
                PatientTaskScheduleEmail.patient_task_schedule_id == pts.id
            )
            .one_or_none()
        )
        self.assertIsNotNone(
            self.dbsession.query(Email)
            .filter(Email.id == email.id)
            .one_or_none()
        )

        self.dbsession.delete(schedule)
        self.dbsession.commit()

        self.assertIsNone(
            self.dbsession.query(TaskScheduleItem)
            .filter(TaskScheduleItem.id == item.id)
            .one_or_none()
        )
        self.assertIsNone(
            self.dbsession.query(PatientTaskSchedule)
            .filter(PatientTaskSchedule.id == pts.id)
            .one_or_none()
        )
        self.assertIsNone(
            self.dbsession.query(PatientTaskScheduleEmail)
            .filter(
                PatientTaskScheduleEmail.patient_task_schedule_id == pts.id
            )
            .one_or_none()
        )
        self.assertIsNone(
            self.dbsession.query(Email)
            .filter(Email.id == email.id)
            .one_or_none()
        )


class TaskScheduleItemTests(DemoRequestTestCase):
    def test_description_shows_shortname_and_number_of_days(self) -> None:
        item = TaskScheduleItem()
        item.task_table_name = "bmi"
        item.due_from = Duration(days=30)

        self.assertEqual(item.description(self.req), "BMI @ 30 days")

    def test_description_with_no_durations(self) -> None:
        item = TaskScheduleItem()
        item.task_table_name = "bmi"

        self.assertEqual(item.description(self.req), "BMI @ ? days")

    def test_due_within_calculated_from_due_by_and_due_from(self) -> None:
        item = TaskScheduleItem()
        item.due_from = Duration(days=30)
        item.due_by = Duration(days=50)

        self.assertEqual(item.due_within.in_days(), 20)

    def test_due_within_is_none_when_missing_due_by(self) -> None:
        item = TaskScheduleItem()
        item.due_from = Duration(days=30)

        self.assertIsNone(item.due_within)

    def test_due_within_calculated_when_missing_due_from(self) -> None:
        item = TaskScheduleItem()
        item.due_by = Duration(days=30)

        self.assertEqual(item.due_within.in_days(), 30)


class PatientTaskScheduleTests(DemoDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        import datetime

        self.schedule = TaskSchedule()
        self.schedule.group_id = self.group.id
        self.dbsession.add(self.schedule)

        self.patient = self.create_patient(
            id=1,
            forename="Jo",
            surname="Patient",
            dob=datetime.date(1958, 4, 19),
            sex="F",
            address="Address",
            gp="GP",
            other="Other",
        )

        self.pts = PatientTaskSchedule()
        self.pts.schedule_id = self.schedule.id
        self.pts.patient_pk = self.patient.pk
        self.dbsession.add(self.pts)
        self.dbsession.flush()

    def test_email_body_contains_access_key(self) -> None:
        self.schedule.email_template = "{access_key}"
        self.dbsession.add(self.schedule)
        self.dbsession.flush()

        self.assertIn(
            f"{self.patient.uuid_as_proquint}", self.pts.email_body(self.req)
        )

    def test_email_body_contains_server_url(self) -> None:
        self.schedule.email_template = "{server_url}"
        self.dbsession.add(self.schedule)
        self.dbsession.flush()

        expected_url = self.req.route_url(Routes.CLIENT_API)

        self.assertIn(f"{expected_url}", self.pts.email_body(self.req))

    def test_email_body_contains_patient_forename(self) -> None:
        self.schedule.email_template = "{forename}"
        self.dbsession.add(self.schedule)
        self.dbsession.flush()

        self.assertIn(
            f"{self.pts.patient.forename}", self.pts.email_body(self.req)
        )

    def test_email_body_contains_patient_surname(self) -> None:
        self.schedule.email_template = "{surname}"
        self.dbsession.add(self.schedule)
        self.dbsession.flush()

        self.assertIn(
            f"{self.pts.patient.surname}", self.pts.email_body(self.req)
        )

    def test_email_body_contains_android_launch_url(self) -> None:
        self.schedule.email_template = "{android_launch_url}"
        self.dbsession.add(self.schedule)
        self.dbsession.flush()

        url = self.pts.email_body(self.req)
        (scheme, netloc, path, query, fragment) = urlsplit(url)
        self.assertEqual(scheme, UriSchemes.HTTP)
        self.assertEqual(netloc, "camcops.org")
        self.assertEqual(path, "/register/")
        query_dict = parse_qs(query)
        self.assertEqual(query_dict["default_single_user_mode"], ["true"])
        self.assertEqual(
            query_dict["default_server_location"],
            [self.req.route_url(Routes.CLIENT_API)],
        )
        self.assertEqual(
            query_dict["default_access_key"], [self.patient.uuid_as_proquint]
        )

    def test_email_body_contains_ios_launch_url(self) -> None:
        self.schedule.email_template = "{ios_launch_url}"
        self.dbsession.add(self.schedule)
        self.dbsession.flush()

        url = self.pts.email_body(self.req)
        (scheme, netloc, path, query, fragment) = urlsplit(url)
        self.assertEqual(scheme, "camcops")
        self.assertEqual(netloc, "camcops.org")
        self.assertEqual(path, "/register/")
        query_dict = parse_qs(query)
        self.assertEqual(query_dict["default_single_user_mode"], ["true"])
        self.assertEqual(
            query_dict["default_server_location"],
            [self.req.route_url(Routes.CLIENT_API)],
        )
        self.assertEqual(
            query_dict["default_access_key"], [self.patient.uuid_as_proquint]
        )

    def test_email_body_disallows_invalid_template(self) -> None:
        self.schedule.email_template = "{foobar}"
        self.dbsession.add(self.schedule)
        self.dbsession.flush()

        with self.assertRaises(KeyError):
            self.pts.email_body(self.req)

    def test_email_body_disallows_accessing_properties(self) -> None:
        self.schedule.email_template = "{server_url.__class__}"
        self.dbsession.add(self.schedule)
        self.dbsession.flush()

        with self.assertRaises(KeyError):
            self.pts.email_body(self.req)

    def test_email_sent_false_for_no_emails(self) -> None:
        self.assertFalse(self.pts.email_sent)

    def test_email_sent_false_for_one_unsent_email(self) -> None:
        email1 = Email()
        email1.sent = False
        self.dbsession.add(email1)
        self.dbsession.flush()
        pts_email1 = PatientTaskScheduleEmail()
        pts_email1.email_id = email1.id
        pts_email1.patient_task_schedule_id = self.pts.id
        self.dbsession.add(pts_email1)
        self.dbsession.commit()

        self.assertFalse(self.pts.email_sent)

    def test_email_sent_true_for_one_sent_email(self) -> None:
        email1 = Email()
        email1.sent = False
        self.dbsession.add(email1)
        self.dbsession.flush()
        pts_email1 = PatientTaskScheduleEmail()
        pts_email1.email_id = email1.id
        pts_email1.patient_task_schedule_id = self.pts.id
        self.dbsession.add(pts_email1)

        email2 = Email()
        email2.sent = True
        self.dbsession.add(email2)
        self.dbsession.flush()
        pts_email2 = PatientTaskScheduleEmail()
        pts_email2.email_id = email2.id
        pts_email2.patient_task_schedule_id = self.pts.id
        self.dbsession.add(pts_email2)
        self.dbsession.commit()

        self.assertTrue(self.pts.email_sent)
