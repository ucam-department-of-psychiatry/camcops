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

from pendulum import Duration

from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_pyramid import Routes
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    PatientTaskScheduleEmail,
    TaskScheduleItem,
)
from camcops_server.cc_modules.cc_testfactories import (
    EmailFactory,
    PatientTaskScheduleEmailFactory,
    PatientTaskScheduleFactory,
    ServerCreatedPatientFactory,
    TaskScheduleFactory,
    TaskScheduleItemFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase


# =============================================================================
# Unit tests
# =============================================================================


class TaskScheduleTests(DemoRequestTestCase):
    def test_deleting_deletes_related_objects(self) -> None:
        patient = ServerCreatedPatientFactory()
        schedule = TaskScheduleFactory(group=patient._group)

        item = TaskScheduleItemFactory(
            task_schedule=schedule,
            task_table_name="ace3",
        )

        pts = PatientTaskScheduleFactory(
            task_schedule=schedule,
            patient=patient,
        )

        pts_email = PatientTaskScheduleEmailFactory(
            patient_task_schedule=pts,
        )

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
            .filter(Email.id == pts_email.email.id)
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
            .filter(Email.id == pts_email.email.id)
            .one_or_none()
        )


class TaskScheduleItemTests(DemoRequestTestCase):
    def test_description_shows_shortname_and_number_of_days(self) -> None:
        item = TaskScheduleItemFactory(
            task_table_name="bmi",
            due_from=Duration(days=30),
        )
        self.assertEqual(item.description(self.req), "BMI @ 30 days")

    def test_description_with_no_durations(self) -> None:
        item = TaskScheduleItemFactory(task_table_name="bmi")
        self.assertEqual(item.description(self.req), "BMI @ ? days")

    def test_due_within_calculated_from_due_by_and_due_from(self) -> None:
        item = TaskScheduleItemFactory(
            due_from=Duration(days=30),
            due_by=Duration(days=50),
        )
        self.assertEqual(item.due_within.in_days(), 20)

    def test_due_within_is_none_when_missing_due_by(self) -> None:
        item = TaskScheduleItemFactory(due_from=Duration(days=30))
        self.assertIsNone(item.due_within)

    def test_due_within_calculated_when_missing_due_from(self) -> None:
        item = TaskScheduleItemFactory(due_by=Duration(days=30))
        self.assertEqual(item.due_within.in_days(), 30)


class PatientTaskScheduleTests(DemoRequestTestCase):
    def test_email_body_contains_access_key(self) -> None:
        schedule = TaskScheduleFactory(email_template="{access_key}")
        pts = PatientTaskScheduleFactory(task_schedule=schedule)

        self.assertIn(
            f"{pts.patient.uuid_as_proquint}", pts.email_body(self.req)
        )

    def test_email_body_contains_server_url(self) -> None:
        schedule = TaskScheduleFactory(email_template="{server_url}")
        pts = PatientTaskScheduleFactory(task_schedule=schedule)

        expected_url = self.req.route_url(Routes.CLIENT_API)

        self.assertIn(f"{expected_url}", pts.email_body(self.req))

    def test_email_body_contains_patient_forename(self) -> None:
        schedule = TaskScheduleFactory(email_template="{forename}")
        pts = PatientTaskScheduleFactory(task_schedule=schedule)

        self.assertIn(f"{pts.patient.forename}", pts.email_body(self.req))

    def test_email_body_contains_patient_surname(self) -> None:
        schedule = TaskScheduleFactory(email_template="{surname}")
        pts = PatientTaskScheduleFactory(task_schedule=schedule)

        self.assertIn(f"{pts.patient.surname}", pts.email_body(self.req))

    def test_email_body_contains_android_launch_url(self) -> None:
        schedule = TaskScheduleFactory(email_template="{android_launch_url}")
        pts = PatientTaskScheduleFactory(task_schedule=schedule)

        url = pts.email_body(self.req)
        (scheme, netloc, path, query, fragment) = urlsplit(url)
        self.assertEqual(scheme, "https")
        self.assertEqual(netloc, "ucam-department-of-psychiatry.github.io")
        self.assertEqual(path, "/camcops/register")
        query_dict = parse_qs(query)
        self.assertEqual(query_dict["default_single_user_mode"], ["true"])
        self.assertEqual(
            query_dict["default_server_location"],
            [self.req.route_url(Routes.CLIENT_API)],
        )
        self.assertEqual(
            query_dict["default_access_key"], [pts.patient.uuid_as_proquint]
        )

    def test_email_body_contains_ios_launch_url(self) -> None:
        schedule = TaskScheduleFactory(email_template="{ios_launch_url}")
        pts = PatientTaskScheduleFactory(task_schedule=schedule)

        url = pts.email_body(self.req)
        (scheme, netloc, path, query, fragment) = urlsplit(url)
        self.assertEqual(scheme, "camcops")
        self.assertEqual(netloc, "ucam-department-of-psychiatry.github.io")
        self.assertEqual(path, "/camcops/register")
        query_dict = parse_qs(query)
        self.assertEqual(query_dict["default_single_user_mode"], ["true"])
        self.assertEqual(
            query_dict["default_server_location"],
            [self.req.route_url(Routes.CLIENT_API)],
        )
        self.assertEqual(
            query_dict["default_access_key"], [pts.patient.uuid_as_proquint]
        )

    def test_email_body_disallows_invalid_template(self) -> None:
        schedule = TaskScheduleFactory(email_template="{foobar}")
        pts = PatientTaskScheduleFactory(task_schedule=schedule)

        with self.assertRaises(KeyError):
            pts.email_body(self.req)

    def test_email_body_disallows_accessing_properties(self) -> None:
        schedule = TaskScheduleFactory(email_template="{server_url.__class__}")
        pts = PatientTaskScheduleFactory(task_schedule=schedule)

        with self.assertRaises(KeyError):
            pts.email_body(self.req)

    def test_email_sent_false_for_no_emails(self) -> None:
        pts = PatientTaskScheduleFactory()
        self.assertFalse(pts.email_sent)

    def test_email_sent_false_for_one_unsent_email(self) -> None:
        email1 = EmailFactory(sent=False)
        pts_email1 = PatientTaskScheduleEmailFactory(email=email1)
        self.assertFalse(pts_email1.patient_task_schedule.email_sent)

    def test_email_sent_true_for_one_sent_email(self) -> None:
        email1 = EmailFactory(sent=True)
        pts_email1 = PatientTaskScheduleEmailFactory(email=email1)
        self.assertTrue(pts_email1.patient_task_schedule.email_sent)
