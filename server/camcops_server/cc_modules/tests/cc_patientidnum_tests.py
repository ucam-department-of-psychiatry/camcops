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

from camcops_server.cc_modules.cc_testfactories import (
    NHSPatientIdNumFactory,
    PatientFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase


class EquivalenceTests(DemoRequestTestCase):
    """
    Tests for the __eq__ method on PatientIdNum.
    """

    def test_same_object_true(self) -> None:
        idnum = NHSPatientIdNumFactory()

        self.assertEqual(idnum, idnum)

    def test_same_idnum_true(self) -> None:
        patient_1 = PatientFactory()
        patient_2 = PatientFactory()

        idnum_1 = NHSPatientIdNumFactory(patient=patient_1)
        idnum_2 = NHSPatientIdNumFactory(
            patient=patient_2,
            which_idnum=idnum_1.which_idnum,
            idnum_value=idnum_1.idnum_value,
        )

        self.assertEqual(idnum_1, idnum_2)

    def test_different_idnum_false(self) -> None:
        patient_1 = PatientFactory()
        patient_2 = PatientFactory()

        idnum_1 = NHSPatientIdNumFactory(patient=patient_1)
        idnum_2 = NHSPatientIdNumFactory(patient=patient_2)

        self.assertNotEqual(idnum_1, idnum_2)

    def test_one_idnum_value_none_false(self) -> None:
        patient_1 = PatientFactory()
        patient_2 = PatientFactory()

        idnum_1 = NHSPatientIdNumFactory(patient=patient_1)
        idnum_2 = NHSPatientIdNumFactory(
            patient=patient_2,
            which_idnum=idnum_1.which_idnum,
            idnum_value=None,
        )

        self.assertNotEqual(idnum_1, idnum_2)

    def test_not_a_patientidnum_false(self) -> None:
        idnum = NHSPatientIdNumFactory()
        self.assertNotEqual(idnum, "not a patient")
