"""
camcops_server/tasks/tests/diagnosis_tests.py

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
    NHSIdNumDefinitionFactory,
    NHSPatientIdNumFactory,
    PatientFactory,
    UserFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.cc_modules.cc_pyramid import ViewParam
from camcops_server.tasks.diagnosis import DiagnosisICD10FinderReport
from camcops_server.tasks.tests.factories import (
    DiagnosisIcd10Factory,
    DiagnosisIcd10ItemFactory,
)


class DiagnosisICD10FinderReportTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.report = DiagnosisICD10FinderReport()
        self.req._debugging_user = UserFactory(superuser=True)

    def test_no_records_creates_empty_report(self) -> None:
        pages = self.report.get_spreadsheet_pages(self.req)

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].headings, [])
        self.assertEqual(pages[0].rows, [])

    def test_creates_report_from_one_record(self) -> None:
        patient = PatientFactory()
        idnum = NHSPatientIdNumFactory(patient=patient)
        diagnosis = DiagnosisIcd10Factory(patient=patient)
        item = DiagnosisIcd10ItemFactory(
            diagnosis_icd10=diagnosis,
            code="code",
            description="description",
        )

        params = {
            ViewParam.WHICH_IDNUM: idnum.which_idnum,
        }

        self.req.set_get_params(params)
        pages = self.report.get_spreadsheet_pages(self.req)

        self.assertEqual(len(pages), 1)
        self.assertEqual(
            pages[0].rows[0],
            {
                "surname": patient.surname,
                "forename": patient.forename,
                "dob": patient.dob,
                "sex": patient.sex,
                "NHS number": idnum.idnum_value,
                "when_created": diagnosis.when_created,
                "system": "ICD-10",
                "code": item.code,
                "description": item.description,
            },
        )

    def test_code_excluded(self) -> None:
        patient1 = PatientFactory()
        nhs_iddef = NHSIdNumDefinitionFactory()
        idnum1 = NHSPatientIdNumFactory(iddef=nhs_iddef, patient=patient1)
        diagnosis1 = DiagnosisIcd10Factory(patient=patient1)
        item1 = DiagnosisIcd10ItemFactory(
            diagnosis_icd10=diagnosis1,
            code="code1",
            description="description1",
        )

        patient2 = PatientFactory()
        NHSPatientIdNumFactory(patient=patient2, iddef=nhs_iddef)
        diagnosis2 = DiagnosisIcd10Factory(patient=patient2)

        DiagnosisIcd10ItemFactory(
            diagnosis_icd10=diagnosis2,
            code="code2",
            description="description2",
        )

        params = {
            ViewParam.WHICH_IDNUM: nhs_iddef.which_idnum,
            ViewParam.DIAGNOSES_INCLUSION: "code1",
            ViewParam.DIAGNOSES_EXCLUSION: "code2",
        }

        self.req.set_get_params(params)
        pages = self.report.get_spreadsheet_pages(self.req)

        self.assertEqual(len(pages), 1)
        page = pages[0]
        self.assertEqual(len(page.rows), 1)
        self.assertEqual(
            page.rows[0],
            {
                "surname": patient1.surname,
                "forename": patient1.forename,
                "dob": patient1.dob,
                "sex": patient1.sex,
                "NHS number": idnum1.idnum_value,
                "when_created": diagnosis1.when_created,
                "system": "ICD-10",
                "code": item1.code,
                "description": item1.description,
            },
        )
