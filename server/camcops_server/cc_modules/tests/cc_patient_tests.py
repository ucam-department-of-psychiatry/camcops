"""
camcops_server/cc_modules/tests/cc_patient_tests.py

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

import hl7
import pendulum

from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_simpleobjects import BarePatientInfo
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
from camcops_server.cc_modules.cc_simpleobjects import IdNumReference
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    TaskSchedule,
    TaskScheduleItem,
)
from camcops_server.cc_modules.cc_spreadsheet import SpreadsheetPage
from camcops_server.cc_modules.cc_testfactories import (
    GroupFactory,
    NHSPatientIdNumFactory,
    PatientFactory,
    PatientTaskScheduleFactory,
    RioPatientIdNumFactory,
    ServerCreatedPatientFactory,
    TaskScheduleFactory,
    TaskScheduleItemFactory,
    UserFactory,
    UserGroupMembershipFactory,
)
from camcops_server.cc_modules.cc_unittest import (
    BasicDatabaseTestCase,
    DemoRequestTestCase,
)
from camcops_server.cc_modules.cc_xml import XmlElement


# =============================================================================
# Unit tests
# =============================================================================


class PatientTests(DemoRequestTestCase):
    def test_patient(self) -> None:
        req = self.req
        req._debugging_user = UserFactory()

        p = PatientFactory()
        nhs_idnum = NHSPatientIdNumFactory(patient=p)
        RioPatientIdNumFactory(patient=p)

        idnum_objects = p.get_idnum_objects()
        self.assertEqual(len(idnum_objects), 2)
        for pidnum in idnum_objects:
            self.assertIsInstance(pidnum, PatientIdNum)

        idnum_references = p.get_idnum_references()
        self.assertEqual(len(idnum_references), 2)
        for idref in idnum_references:
            self.assertIsInstance(idref, IdNumReference)

        idnum_raw_values = p.get_idnum_raw_values_only()
        self.assertEqual(len(idnum_raw_values), 2)
        for idnum in idnum_raw_values:
            self.assertIsInstance(idnum, int)

        self.assertIsInstance(p.get_xml_root(req), XmlElement)
        self.assertIsInstance(p.get_spreadsheet_page(req), SpreadsheetPage)
        self.assertIsInstance(p.get_bare_ptinfo(), BarePatientInfo)
        self.assertIsInstanceOrNone(p.group, Group)
        self.assertIsInstance(p.satisfies_upload_id_policy(), bool)
        self.assertIsInstance(p.satisfies_finalize_id_policy(), bool)
        self.assertIsInstance(p.get_surname(), str)
        self.assertIsInstance(p.get_forename(), str)
        self.assertIsInstance(p.get_surname_forename_upper(), str)
        for longform in (True, False):
            self.assertIsInstance(p.get_dob_html(req, longform), str)
        age_str_int = p.get_age(req)
        assert isinstance(age_str_int, str) or isinstance(age_str_int, int)
        self.assertIsInstanceOrNone(p.get_dob(), pendulum.Date)
        self.assertIsInstanceOrNone(p.get_dob_str(), str)
        age_at_str_int = p.get_age_at(req.now)
        assert isinstance(age_at_str_int, str) or isinstance(
            age_at_str_int, int
        )
        self.assertIsInstance(p.is_female(), bool)
        self.assertIsInstance(p.is_male(), bool)
        self.assertIsInstance(p.get_sex(), str)
        self.assertIsInstance(p.get_sex_verbose(), str)
        self.assertIsInstance(p.get_address(), str)
        self.assertIsInstance(p.get_email(), str)
        self.assertIsInstance(
            p.get_hl7_pid_segment(req, self.recipdef), hl7.Segment
        )
        self.assertIsInstanceOrNone(
            p.get_idnum_object(which_idnum=nhs_idnum.which_idnum), PatientIdNum
        )
        self.assertIsInstanceOrNone(
            p.get_idnum_value(which_idnum=nhs_idnum.which_idnum), int
        )
        self.assertIsInstance(
            p.get_iddesc(req, which_idnum=nhs_idnum.which_idnum), str
        )
        self.assertIsInstance(
            p.get_idshortdesc(req, which_idnum=nhs_idnum.which_idnum), str
        )
        self.assertIsInstance(p.is_preserved(), bool)
        self.assertIsInstance(p.is_finalized(), bool)
        self.assertIsInstance(p.user_may_edit(req), bool)

    def test_surname_forename_upper(self) -> None:
        patient = PatientFactory(forename="Forename", surname="Surname")
        self.assertEqual(
            patient.get_surname_forename_upper(), "SURNAME, FORENAME"
        )

    def test_surname_forename_upper_no_forename(self) -> None:
        patient = PatientFactory(forename=None, surname="Surname")
        self.assertEqual(
            patient.get_surname_forename_upper(), "SURNAME, (UNKNOWN)"
        )

    def test_surname_forename_upper_no_surname(self) -> None:
        patient = PatientFactory(forename="Forename", surname=None)
        self.assertEqual(
            patient.get_surname_forename_upper(), "(UNKNOWN), FORENAME"
        )


class LineageTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patient = PatientFactory()
        self.current_patient_idnum = NHSPatientIdNumFactory(
            patient=self.patient
        )
        self.assertTrue(self.current_patient_idnum._current)

        self.not_current_patient_idnum = NHSPatientIdNumFactory(
            patient=self.patient,
            _current=False,
            id=self.current_patient_idnum.id,
            which_idnum=self.current_patient_idnum.which_idnum,
            idnum_value=self.current_patient_idnum.idnum_value,
        )
        self.assertFalse(self.not_current_patient_idnum._current)

    def test_gen_patient_idnums_even_noncurrent(self) -> None:
        idnums = list(self.patient.gen_patient_idnums_even_noncurrent())

        self.assertEqual(len(idnums), 2)


class PatientDeleteTests(DemoRequestTestCase):
    def test_deletes_patient_task_schedule(self) -> None:
        schedule = TaskScheduleFactory()

        item = TaskScheduleItemFactory(
            task_schedule=schedule,
            task_table_name="ace3",
            due_from=pendulum.Duration(days=30),
            due_by=pendulum.Duration(days=60),
        )

        patient = ServerCreatedPatientFactory()

        pts = PatientTaskScheduleFactory(
            task_schedule=schedule,
            patient=patient,
        )

        self.assertIsNotNone(
            self.dbsession.query(TaskSchedule)
            .filter(TaskSchedule.id == schedule.id)
            .one_or_none()
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

        self.dbsession.delete(patient)
        self.dbsession.commit()

        self.assertIsNotNone(
            self.dbsession.query(TaskSchedule)
            .filter(TaskSchedule.id == schedule.id)
            .one_or_none()
        )
        self.assertIsNotNone(
            self.dbsession.query(TaskScheduleItem)
            .filter(TaskScheduleItem.id == item.id)
            .one_or_none()
        )

        self.assertIsNone(
            self.dbsession.query(PatientTaskSchedule)
            .filter(PatientTaskSchedule.id == pts.id)
            .one_or_none()
        )


class PatientPermissionTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.user = UserFactory()
        self.group = GroupFactory()

    def test_group_administrator_may_edit_server_patient(self) -> None:
        patient = ServerCreatedPatientFactory(_group=self.group)
        ugm = UserGroupMembershipFactory(
            user_id=self.user.id, group_id=self.group.id, groupadmin=True
        )

        self.req._debugging_user = ugm.user
        self.assertTrue(patient.user_may_edit(self.req))

    def test_group_administrator_may_edit_finalized_patient(self) -> None:
        patient = PatientFactory(_group=self.group)
        ugm = UserGroupMembershipFactory(
            user_id=self.user.id, group_id=self.group.id, groupadmin=True
        )

        self.assertTrue(ugm.groupadmin)

        self.req._debugging_user = ugm.user
        self.assertTrue(patient.user_may_edit(self.req))

    def test_group_member_with_permission_may_edit_server_created(
        self,
    ) -> None:
        patient = ServerCreatedPatientFactory(_group=self.group)
        ugm = UserGroupMembershipFactory(
            user_id=self.user.id,
            group_id=self.group.id,
            may_manage_patients=True,
        )

        self.req._debugging_user = ugm.user
        self.assertTrue(patient.user_may_edit(self.req))

    def test_group_member_with_permission_may_not_edit_finalized(self) -> None:
        patient = PatientFactory(_group=self.group)
        ugm = UserGroupMembershipFactory(
            user_id=self.user.id,
            group_id=self.group.id,
            may_manage_patients=True,
        )

        self.req._debugging_user = ugm.user
        self.assertFalse(patient.user_may_edit(self.req))


class EquivalenceTests(DemoRequestTestCase):
    """
    Tests for the __eq__ method on Patient.
    """

    def test_same_object_true(self) -> None:
        patient = PatientFactory()

        self.assertEqual(patient, patient)

    def test_same_id_device_era_true(self) -> None:
        patient_1 = PatientFactory()
        patient_2 = PatientFactory(
            id=patient_1.id, _device=patient_1._device, _era=patient_1._era
        )

        self.assertEqual(patient_1, patient_2)

    def test_same_idnum_true(self) -> None:
        patient_1 = PatientFactory()
        patient_2 = PatientFactory()

        idnum_1 = NHSPatientIdNumFactory(patient=patient_1)
        NHSPatientIdNumFactory(
            patient=patient_2,
            which_idnum=idnum_1.which_idnum,
            idnum_value=idnum_1.idnum_value,
        )

        self.assertEqual(patient_1, patient_2)

    def test_different_idnum_false(self) -> None:
        patient_1 = PatientFactory()
        patient_2 = PatientFactory()

        NHSPatientIdNumFactory(patient=patient_1)
        NHSPatientIdNumFactory(patient=patient_2)

        self.assertNotEqual(patient_1, patient_2)

    def test_not_a_patient_false(self) -> None:
        patient = PatientFactory()
        self.assertNotEqual(patient, "not a patient")
