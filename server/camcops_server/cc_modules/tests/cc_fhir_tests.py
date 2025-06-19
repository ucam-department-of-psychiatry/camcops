"""
camcops_server/cc_modules/tests/cc_fhir_tests.py

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

import datetime
import json
import logging
from typing import Dict, List
from unittest import mock

from cardinal_pythonlib.httpconst import HttpMethod
import pendulum
from requests.exceptions import HTTPError

from camcops_server.cc_modules.cc_constants import FHIRConst as Fc
from camcops_server.cc_modules.cc_exportmodels import (
    ExportedTask,
    ExportedTaskFhir,
    ExportedTaskFhirEntry,
)
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_exportrecipientinfo import (
    ExportRecipientInfo,
)
from camcops_server.cc_modules.cc_fhir import (
    fhir_reference_from_identifier,
    fhir_sysval_from_id,
    FhirExportException,
    FhirTaskExporter,
)
from camcops_server.cc_modules.cc_pyramid import Routes
from camcops_server.cc_modules.cc_testfactories import (
    NHSPatientIdNumFactory,
    PatientFactory,
    RioPatientIdNumFactory,
)

from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.cc_modules.cc_version_string import (
    CAMCOPS_SERVER_VERSION_STRING,
)
from camcops_server.tasks.tests.factories import (
    ApeqptFactory,
    BmiFactory,
    DiagnosisIcd10Factory,
    DiagnosisIcd10ItemFactory,
    DiagnosisIcd9CMFactory,
    DiagnosisIcd9CMItemFactory,
    Gad7Factory,
    Phq9Factory,
)


log = logging.getLogger()


# =============================================================================
# Helper classes
# =============================================================================


class MockFhirTaskExporter(FhirTaskExporter):
    pass


class MockFhirResponse(mock.Mock):
    def __init__(self, response_json: Dict):
        super().__init__(
            text=json.dumps(response_json),
            json=mock.Mock(return_value=response_json),
        )


class FhirExportTestCase(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()
        recipientinfo = ExportRecipientInfo()

        self.recipient = ExportRecipient(other=recipientinfo)
        self.recipient.fhir_api_url = "https://www.example.com/fhir"

        # auto increment doesn't work for BigInteger with SQLite
        self.recipient.id = 1
        self.recipient.recipient_name = "test"

        self.camcops_root_url = self.req.route_url(Routes.HOME).rstrip("/")
        # ... no trailing slash


class FhirExportPatientTestCase(FhirExportTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patient = PatientFactory()
        self.patient_nhs_idnum = NHSPatientIdNumFactory(patient=self.patient)
        self.patient_rio_idnum = RioPatientIdNumFactory(patient=self.patient)

        self.recipient.primary_idnum = self.patient_rio_idnum.which_idnum


# =============================================================================
# A generic patient-based task: PHQ9
# =============================================================================


class FhirTaskExporterPhq9Tests(FhirExportPatientTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.task = Phq9Factory(
            patient=self.patient,
            q1=0,
            q2=1,
            q3=2,
            q4=3,
            q5=0,
            q6=1,
            q7=2,
            q8=3,
            q9=0,
            q10=3,
        )

    def test_patient_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {Fc.TYPE: Fc.TRANSACTION_RESPONSE}

        with mock.patch.object(
            exporter.client.server,
            "post_json",
            return_value=MockFhirResponse(response_json),
        ) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        self.assertEqual(sent_json[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_BUNDLE)
        self.assertEqual(sent_json[Fc.TYPE], Fc.TRANSACTION)

        patient = sent_json[Fc.ENTRY][0][Fc.RESOURCE]
        self.assertEqual(patient[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_PATIENT)

        identifier = patient[Fc.IDENTIFIER]
        idnum_value = self.patient_rio_idnum.idnum_value

        patient_id = self.patient.get_fhir_identifier(self.req, self.recipient)

        self.assertEqual(identifier[0][Fc.SYSTEM], patient_id.system)
        self.assertEqual(identifier[0][Fc.VALUE], str(idnum_value))

        self.assertEqual(
            patient[Fc.NAME][0][Fc.NAME_FAMILY], self.patient.surname
        )
        self.assertEqual(
            patient[Fc.NAME][0][Fc.NAME_GIVEN], [self.patient.forename]
        )
        self.assertEqual(patient[Fc.GENDER], Fc.GENDER_FEMALE)

        request = sent_json[Fc.ENTRY][0][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL], Fc.RESOURCE_TYPE_PATIENT)
        self.assertEqual(
            request[Fc.IF_NONE_EXIST],
            fhir_reference_from_identifier(patient_id),
        )

    def test_questionnaire_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {Fc.TYPE: Fc.TRANSACTION_RESPONSE}

        with mock.patch.object(
            exporter.client.server,
            "post_json",
            return_value=MockFhirResponse(response_json),
        ) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        questionnaire = sent_json[Fc.ENTRY][1][Fc.RESOURCE]
        self.assertEqual(
            questionnaire[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_QUESTIONNAIRE
        )
        self.assertEqual(questionnaire[Fc.STATUS], Fc.QSTATUS_ACTIVE)

        identifier = questionnaire[Fc.IDENTIFIER]

        questionnaire_url = (
            f"{self.camcops_root_url}/{Routes.FHIR_QUESTIONNAIRE_SYSTEM}"
        )
        self.assertEqual(identifier[0][Fc.SYSTEM], questionnaire_url)
        self.assertEqual(
            identifier[0][Fc.VALUE], f"phq9/{CAMCOPS_SERVER_VERSION_STRING}"
        )

        question_1 = questionnaire[Fc.ITEM][0]
        question_10 = questionnaire[Fc.ITEM][9]
        self.assertEqual(question_1[Fc.LINK_ID], "q1")
        self.assertEqual(
            question_1[Fc.TEXT],
            "1. Little interest or pleasure in doing things",
        )
        self.assertEqual(question_1[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)

        options = question_1[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY], "Not at all")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(
            options[1][Fc.VALUE_CODING][Fc.DISPLAY], "Several days"
        )

        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.CODE], "2")
        self.assertEqual(
            options[2][Fc.VALUE_CODING][Fc.DISPLAY], "More than half the days"
        )

        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.CODE], "3")
        self.assertEqual(
            options[3][Fc.VALUE_CODING][Fc.DISPLAY], "Nearly every day"
        )

        self.assertEqual(question_10[Fc.LINK_ID], "q10")
        self.assertEqual(
            question_10[Fc.TEXT],
            (
                "10. If you checked off any problems, how difficult have "
                "these problems made it for you to do your work, take care of "
                "things at home, or get along with other people?"
            ),
        )
        self.assertEqual(question_10[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)
        options = question_10[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(
            options[0][Fc.VALUE_CODING][Fc.DISPLAY], "Not difficult at all"
        )

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(
            options[1][Fc.VALUE_CODING][Fc.DISPLAY], "Somewhat difficult"
        )

        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.CODE], "2")
        self.assertEqual(
            options[2][Fc.VALUE_CODING][Fc.DISPLAY], "Very difficult"
        )

        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.CODE], "3")
        self.assertEqual(
            options[3][Fc.VALUE_CODING][Fc.DISPLAY], "Extremely difficult"
        )

        self.assertEqual(len(questionnaire[Fc.ITEM]), 10)

        request = sent_json[Fc.ENTRY][1][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL], Fc.RESOURCE_TYPE_QUESTIONNAIRE)
        q_id = self.task._get_fhir_questionnaire_id(self.req)
        self.assertEqual(
            request[Fc.IF_NONE_EXIST], fhir_reference_from_identifier(q_id)
        )

    def test_questionnaire_response_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {Fc.TYPE: Fc.TRANSACTION_RESPONSE}

        with mock.patch.object(
            exporter.client.server,
            "post_json",
            return_value=MockFhirResponse(response_json),
        ) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        response = sent_json[Fc.ENTRY][2][Fc.RESOURCE]
        self.assertEqual(
            response[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_QUESTIONNAIRE_RESPONSE
        )

        q_id = self.task._get_fhir_questionnaire_id(self.req)
        self.assertEqual(response[Fc.QUESTIONNAIRE], fhir_sysval_from_id(q_id))
        self.assertEqual(
            response[Fc.AUTHORED], self.task.when_created.isoformat()
        )
        self.assertEqual(response[Fc.STATUS], Fc.QSTATUS_COMPLETED)

        subject = response[Fc.SUBJECT]
        identifier = subject[Fc.IDENTIFIER]
        self.assertEqual(subject[Fc.TYPE], Fc.RESOURCE_TYPE_PATIENT)
        idnum_value = self.patient_rio_idnum.idnum_value

        patient_id = self.patient.get_fhir_identifier(self.req, self.recipient)
        if isinstance(identifier, list):
            test_identifier = identifier[0]
        else:  # only one
            test_identifier = identifier
        self.assertEqual(test_identifier[Fc.SYSTEM], patient_id.system)
        self.assertEqual(test_identifier[Fc.VALUE], str(idnum_value))

        request = sent_json[Fc.ENTRY][2][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(
            request[Fc.URL], Fc.RESOURCE_TYPE_QUESTIONNAIRE_RESPONSE
        )
        qr_id = self.task._get_fhir_questionnaire_response_id(self.req)
        self.assertEqual(
            request[Fc.IF_NONE_EXIST], fhir_reference_from_identifier(qr_id)
        )

        item_1 = response[Fc.ITEM][0]
        item_10 = response[Fc.ITEM][9]
        self.assertEqual(item_1[Fc.LINK_ID], "q1")
        self.assertEqual(
            item_1[Fc.TEXT], "1. Little interest or pleasure in doing things"
        )
        answer_1 = item_1[Fc.ANSWER][0]
        # noinspection PyUnresolvedReferences
        self.assertEqual(answer_1[Fc.VALUE_INTEGER], self.task.q1)

        self.assertEqual(item_10[Fc.LINK_ID], "q10")
        self.assertEqual(
            item_10[Fc.TEXT],
            (
                "10. If you checked off any problems, how difficult have "
                "these problems made it for you to do your work, take care of "
                "things at home, or get along with other people?"
            ),
        )
        answer_10 = item_10[Fc.ANSWER][0]
        self.assertEqual(answer_10[Fc.VALUE_INTEGER], self.task.q10)

        self.assertEqual(len(response[Fc.ITEM]), 10)

    # noinspection PyUnresolvedReferences
    def test_exported_task_saved(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        # auto increment doesn't work for BigInteger with SQLite
        exported_task.id = 1
        self.dbsession.add(exported_task)

        exported_task_fhir = ExportedTaskFhir(exported_task)
        self.dbsession.add(exported_task_fhir)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            Fc.RESOURCE_TYPE: Fc.RESOURCE_TYPE_BUNDLE,
            Fc.ID: "cae48957-e7e6-4649-97f8-0a882076ad0a",
            Fc.TYPE: Fc.TRANSACTION_RESPONSE,
            Fc.LINK: [
                {Fc.RELATION: Fc.SELF, Fc.URL: "http://localhost:8080/fhir"}
            ],
            Fc.ENTRY: [
                {
                    Fc.RESPONSE: {
                        Fc.STATUS: Fc.RESPONSE_STATUS_200_OK,
                        Fc.LOCATION: "Patient/1/_history/1",
                        Fc.ETAG: "1",
                    }
                },
                {
                    Fc.RESPONSE: {
                        Fc.STATUS: Fc.RESPONSE_STATUS_200_OK,
                        Fc.LOCATION: "Questionnaire/26/_history/1",
                        Fc.ETAG: "1",
                    }
                },
                {
                    Fc.RESPONSE: {
                        Fc.STATUS: Fc.RESPONSE_STATUS_201_CREATED,
                        Fc.LOCATION: "QuestionnaireResponse/42/_history/1",
                        Fc.ETAG: "1",
                        Fc.LAST_MODIFIED: "2021-05-24T09:30:11.098+00:00",
                    }
                },
            ],
        }

        with mock.patch.object(
            exporter.client.server,
            "post_json",
            return_value=MockFhirResponse(response_json),
        ):
            exporter.export_task()

        self.dbsession.commit()

        entries = (
            exported_task_fhir.entries
        )  # type: List[ExportedTaskFhirEntry]

        entries.sort(key=lambda e: e.location)

        self.assertEqual(entries[0].status, Fc.RESPONSE_STATUS_200_OK)
        self.assertEqual(entries[0].location, "Patient/1/_history/1")
        self.assertEqual(entries[0].etag, "1")

        self.assertEqual(entries[1].status, Fc.RESPONSE_STATUS_200_OK)
        self.assertEqual(entries[1].location, "Questionnaire/26/_history/1")
        self.assertEqual(entries[1].etag, "1")

        self.assertEqual(entries[2].status, Fc.RESPONSE_STATUS_201_CREATED)
        self.assertEqual(
            entries[2].location, "QuestionnaireResponse/42/_history/1"
        )
        self.assertEqual(entries[2].etag, "1")
        self.assertEqual(
            entries[2].last_modified,
            datetime.datetime(2021, 5, 24, 9, 30, 11, 98000),
        )

    def test_raises_when_http_error(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        errmsg = "Something bad happened"
        with mock.patch.object(
            exporter.client.server,
            "post_json",
            side_effect=HTTPError(response=mock.Mock(text=errmsg)),
        ):
            with self.assertRaises(FhirExportException) as cm:
                exporter.export_task()

            message = str(cm.exception)
            self.assertIn(errmsg, message)

    def test_raises_when_fhirclient_raises(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        exporter.client.server = None
        with self.assertRaises(FhirExportException) as cm:
            exporter.export_task()

            message = str(cm.exception)
            self.assertIn("Cannot create a resource without a server", message)

    def test_raises_for_missing_api_url(self) -> None:
        self.recipient.fhir_api_url = ""
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        with self.assertRaises(FhirExportException) as cm:
            FhirTaskExporter(self.req, exported_task_fhir)

        message = str(cm.exception)
        self.assertIn("must be initialized with `base_uri`", message)


# =============================================================================
# A generic anonymous task: APEQPT
# =============================================================================

APEQPT_Q_WHEN = "Date and time the assessment tool was completed"
OFFERED_PREFERENCE = "Have you been offered your preference?"
SATISFIED_ASSESSMENT = "How satisfied were you with your assessment?"
TELL_US = (
    "Please use this space to tell us about your experience of our service."
)
PREFER_ANY = "Do you prefer any of the treatments among the options available?"
GIVEN_INFO = (
    "Were you given information about options for choosing a "
    "treatment that is appropriate for your problems?"
)
APEQ_SATIS_A4 = "Completely satisfied"
APEQ_SATIS_A3 = "Mostly satisfied"
APEQ_SATIS_A2 = "Neither satisfied nor dissatisfied"
APEQ_SATIS_A1 = "Not satisfied"
APEQ_SATIS_A0 = "Not at all satisfied"


class FhirTaskExporterAnonymousTests(FhirExportTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.task = ApeqptFactory(
            q_datetime=pendulum.now(),
            q1_choice=0,
            q2_choice=1,
            q3_choice=2,
            q1_satisfaction=3,
            q2_satisfaction="Service experience",
        )

    def test_questionnaire_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {Fc.TYPE: Fc.TRANSACTION_RESPONSE}

        with mock.patch.object(
            exporter.client.server,
            "post_json",
            return_value=MockFhirResponse(response_json),
        ) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        questionnaire = sent_json[Fc.ENTRY][0][Fc.RESOURCE]
        self.assertEqual(
            questionnaire[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_QUESTIONNAIRE
        )
        self.assertEqual(questionnaire[Fc.STATUS], Fc.QSTATUS_ACTIVE)

        identifier = questionnaire[Fc.IDENTIFIER]

        questionnaire_url = (
            f"{self.camcops_root_url}/{Routes.FHIR_QUESTIONNAIRE_SYSTEM}"
        )
        self.assertEqual(identifier[0][Fc.SYSTEM], questionnaire_url)
        self.assertEqual(
            identifier[0][Fc.VALUE], f"apeqpt/{CAMCOPS_SERVER_VERSION_STRING}"
        )

        self.assertEqual(len(questionnaire[Fc.ITEM]), 5)
        (
            q1_choice,
            q2_choice,
            q3_choice,
            q1_satisfaction,
            q2_satisfaction,
        ) = questionnaire[Fc.ITEM]

        # q1_choice
        self.assertEqual(q1_choice[Fc.LINK_ID], "q1_choice")
        self.assertEqual(q1_choice[Fc.TEXT], GIVEN_INFO)
        self.assertEqual(q1_choice[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)

        options = q1_choice[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY], "No")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY], "Yes")

        # q2_choice
        self.assertEqual(q2_choice[Fc.LINK_ID], "q2_choice")
        self.assertEqual(q2_choice[Fc.TEXT], PREFER_ANY)
        self.assertEqual(q2_choice[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)
        options = q2_choice[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY], "No")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY], "Yes")

        # q3_choice
        self.assertEqual(q3_choice[Fc.LINK_ID], "q3_choice")
        self.assertEqual(q3_choice[Fc.TEXT], OFFERED_PREFERENCE)
        self.assertEqual(q3_choice[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)
        options = q3_choice[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY], "No")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY], "Yes")

        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.CODE], "2")
        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.DISPLAY], "N/A")

        # q1_satisfaction
        self.assertEqual(q1_satisfaction[Fc.LINK_ID], "q1_satisfaction")
        self.assertEqual(q1_satisfaction[Fc.TEXT], SATISFIED_ASSESSMENT)
        self.assertEqual(q1_satisfaction[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)
        options = q1_satisfaction[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(
            options[0][Fc.VALUE_CODING][Fc.DISPLAY], APEQ_SATIS_A0
        )

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(
            options[1][Fc.VALUE_CODING][Fc.DISPLAY], APEQ_SATIS_A1
        )

        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.CODE], "2")
        self.assertEqual(
            options[2][Fc.VALUE_CODING][Fc.DISPLAY], APEQ_SATIS_A2
        )

        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.CODE], "3")
        self.assertEqual(
            options[3][Fc.VALUE_CODING][Fc.DISPLAY], APEQ_SATIS_A3
        )

        self.assertEqual(options[4][Fc.VALUE_CODING][Fc.CODE], "4")
        self.assertEqual(
            options[4][Fc.VALUE_CODING][Fc.DISPLAY], APEQ_SATIS_A4
        )

        # q2 satisfaction
        self.assertEqual(q2_satisfaction[Fc.LINK_ID], "q2_satisfaction")
        self.assertEqual(q2_satisfaction[Fc.TEXT], TELL_US)
        self.assertEqual(q2_satisfaction[Fc.TYPE], Fc.QITEM_TYPE_STRING)

        request = sent_json[Fc.ENTRY][0][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL], Fc.RESOURCE_TYPE_QUESTIONNAIRE)
        q_id = self.task._get_fhir_questionnaire_id(self.req)
        self.assertEqual(
            request[Fc.IF_NONE_EXIST], fhir_reference_from_identifier(q_id)
        )

    def test_questionnaire_response_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {Fc.TYPE: Fc.TRANSACTION_RESPONSE}

        with mock.patch.object(
            exporter.client.server,
            "post_json",
            return_value=MockFhirResponse(response_json),
        ) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        response = sent_json[Fc.ENTRY][1][Fc.RESOURCE]
        self.assertEqual(
            response[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_QUESTIONNAIRE_RESPONSE
        )
        q_id = self.task._get_fhir_questionnaire_id(self.req)
        self.assertEqual(response[Fc.QUESTIONNAIRE], fhir_sysval_from_id(q_id))
        self.assertEqual(
            response[Fc.AUTHORED], self.task.when_created.isoformat()
        )
        self.assertEqual(response[Fc.STATUS], Fc.QSTATUS_COMPLETED)

        request = sent_json[Fc.ENTRY][1][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL], "QuestionnaireResponse")
        qr_id = self.task._get_fhir_questionnaire_response_id(self.req)
        self.assertEqual(
            request[Fc.IF_NONE_EXIST], fhir_reference_from_identifier(qr_id)
        )

        self.assertEqual(len(response[Fc.ITEM]), 5)
        (
            q1_choice,
            q2_choice,
            q3_choice,
            q1_satisfaction,
            q2_satisfaction,
        ) = response[Fc.ITEM]

        # q1_choice
        self.assertEqual(q1_choice[Fc.LINK_ID], "q1_choice")
        self.assertEqual(q1_choice[Fc.TEXT], GIVEN_INFO)
        q1_choice_answer = q1_choice[Fc.ANSWER][0]
        self.assertEqual(
            q1_choice_answer[Fc.VALUE_INTEGER], self.task.q1_choice
        )

        # q2_choice
        self.assertEqual(q2_choice[Fc.LINK_ID], "q2_choice")
        self.assertEqual(q2_choice[Fc.TEXT], PREFER_ANY)
        q2_choice_answer = q2_choice[Fc.ANSWER][0]
        self.assertEqual(
            q2_choice_answer[Fc.VALUE_INTEGER], self.task.q2_choice
        )

        # q3_choice
        self.assertEqual(q3_choice[Fc.LINK_ID], "q3_choice")
        self.assertEqual(q3_choice[Fc.TEXT], OFFERED_PREFERENCE)
        q3_choice_answer = q3_choice[Fc.ANSWER][0]
        self.assertEqual(
            q3_choice_answer[Fc.VALUE_INTEGER], self.task.q3_choice
        )

        # q1_satisfaction
        self.assertEqual(q1_satisfaction[Fc.LINK_ID], "q1_satisfaction")
        self.assertEqual(q1_satisfaction[Fc.TEXT], SATISFIED_ASSESSMENT)
        q1_satisfaction_answer = q1_satisfaction[Fc.ANSWER][0]
        self.assertEqual(
            q1_satisfaction_answer[Fc.VALUE_INTEGER], self.task.q1_satisfaction
        )

        # q2 satisfaction
        self.assertEqual(q2_satisfaction[Fc.LINK_ID], "q2_satisfaction")
        self.assertEqual(q2_satisfaction[Fc.TEXT], TELL_US)
        q2_satisfaction_answer = q2_satisfaction[Fc.ANSWER][0]
        self.assertEqual(
            q2_satisfaction_answer[Fc.VALUE_STRING], self.task.q2_satisfaction
        )


# =============================================================================
# Tasks that add their own special details
# =============================================================================


class FhirTaskExporterBMITests(FhirExportPatientTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.task = BmiFactory(patient=self.patient)

    def test_observations(self) -> None:
        bundle = self.task.get_fhir_bundle(
            self.req, self.recipient, skip_docs_if_other_content=True
        )

        bundle_json = bundle.as_json()

        height_entry = bundle_json[Fc.ENTRY][3]
        mass_entry = bundle_json[Fc.ENTRY][4]
        bmi_entry = bundle_json[Fc.ENTRY][5]
        waist_entry = bundle_json[Fc.ENTRY][6]

        height_resource = height_entry[Fc.RESOURCE]
        mass_resource = mass_entry[Fc.RESOURCE]
        bmi_resource = bmi_entry[Fc.RESOURCE]
        waist_resource = waist_entry[Fc.RESOURCE]

        self.assertEqual(
            height_resource[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_OBSERVATION
        )
        self.assertEqual(
            height_resource[Fc.VALUE_QUANTITY][Fc.VALUE], self.task.height_m
        )

        self.assertEqual(
            mass_resource[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_OBSERVATION
        )
        self.assertAlmostEqual(
            mass_resource[Fc.VALUE_QUANTITY][Fc.VALUE],
            self.task.mass_kg,
            places=2,
        )

        self.assertEqual(
            bmi_resource[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_OBSERVATION
        )
        self.assertAlmostEqual(
            bmi_resource[Fc.VALUE_QUANTITY][Fc.VALUE],
            self.task.bmi(),
            places=2,
        )

        self.assertEqual(
            waist_resource[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_OBSERVATION
        )
        self.assertAlmostEqual(
            waist_resource[Fc.VALUE_QUANTITY][Fc.VALUE],
            self.task.waist_cm,
            places=2,
        )


class FhirTaskExporterDiagnosisIcd10Tests(FhirExportPatientTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.task = DiagnosisIcd10Factory(patient=self.patient)

        # noinspection PyArgumentList
        self.item1 = DiagnosisIcd10ItemFactory(
            diagnosis_icd10=self.task,
            seqnum=1,
            code="F33.30",
            description="Recurrent depressive disorder, current episode "
            "severe with psychotic symptoms: "
            "with mood-congruent psychotic symptoms",
            comment="Cotard's syndrome",
        )
        # noinspection PyArgumentList
        self.item2 = DiagnosisIcd10ItemFactory(
            diagnosis_icd10=self.task,
            seqnum=2,
            code="F43.1",
            description="Post-traumatic stress disorder",
        )

    def test_observations(self) -> None:
        bundle = self.task.get_fhir_bundle(
            self.req, self.recipient, skip_docs_if_other_content=True
        )

        bundle_json = bundle.as_json()

        cotard_resource = bundle_json[Fc.ENTRY][4][Fc.RESOURCE]
        ptsd_resource = bundle_json[Fc.ENTRY][5][Fc.RESOURCE]

        self.assertEqual(
            cotard_resource[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_CONDITION
        )
        self.assertEqual(
            cotard_resource[Fc.CODE][Fc.CODING][0][Fc.CODE], "F33.30"
        )
        self.assertIn(
            "Cotard's syndrome",
            cotard_resource[Fc.CODE][Fc.CODING][0][Fc.DISPLAY],
        )
        self.assertIn(
            "Recurrent depressive",
            cotard_resource[Fc.CODE][Fc.CODING][0][Fc.DISPLAY],
        )

        self.assertEqual(
            ptsd_resource[Fc.CODE][Fc.CODING][0][Fc.CODE], "F43.1"
        )


class FhirTaskExporterDiagnosisIcd9CMTests(FhirExportPatientTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.task = DiagnosisIcd9CMFactory(patient=self.patient)

        # noinspection PyArgumentList
        self.item1 = DiagnosisIcd9CMItemFactory(
            diagnosis_icd9cm=self.task,
            seqnum=1,
            code="290.4",
            description="Vascular dementia",
            comment="or perhaps mixed dementia",
        )
        # noinspection PyArgumentList
        self.item2 = DiagnosisIcd9CMItemFactory(
            diagnosis_icd9cm=self.task,
            seqnum=2,
            code="303.0",
            description="Acute alcoholic intoxication",
        )

    def test_observations(self) -> None:
        bundle = self.task.get_fhir_bundle(
            self.req, self.recipient, skip_docs_if_other_content=True
        )
        bundle_json = bundle.as_json()
        dementia_resource = bundle_json[Fc.ENTRY][4][Fc.RESOURCE]
        intoxication_resource = bundle_json[Fc.ENTRY][5][Fc.RESOURCE]

        self.assertEqual(
            dementia_resource[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_CONDITION
        )
        self.assertEqual(
            dementia_resource[Fc.CODE][Fc.CODING][0][Fc.CODE], "290.4"
        )
        self.assertIn(
            "Vascular dementia",
            dementia_resource[Fc.CODE][Fc.CODING][0][Fc.DISPLAY],
        )
        self.assertIn(
            "or perhaps mixed dementia",
            dementia_resource[Fc.CODE][Fc.CODING][0][Fc.DISPLAY],
        )

        self.assertEqual(
            intoxication_resource[Fc.CODE][Fc.CODING][0][Fc.CODE], "303.0"
        )


class FhirTaskExporterGad7Tests(FhirExportPatientTestCase):
    """
    The GAD7 is a standard questionnaire that we don't provide any special
    FHIR support for; we rely on autodiscovery. This is essentially a high
    level test for _fhir_autodiscover() in cc_task.py, albeit not a
    particularly thorough one.
    """

    def setUp(self) -> None:
        super().setUp()

        self.task = Gad7Factory(
            patient=self.patient,
            q1=0,
            q2=1,
            q3=2,
            q4=3,
            q5=0,
            q6=1,
            q7=2,
        )

    def test_observations(self) -> None:
        bundle = self.task.get_fhir_bundle(
            self.req, self.recipient, skip_docs_if_other_content=True
        )
        bundle_json = bundle.as_json()
        questions = bundle_json[Fc.ENTRY][1][Fc.RESOURCE][Fc.ITEM]
        answers = bundle_json[Fc.ENTRY][2][Fc.RESOURCE][Fc.ITEM]

        # Question text
        self.assertIn(
            "1. Feeling nervous, anxious or on edge", questions[0][Fc.TEXT]
        )
        # Comment string
        self.assertIn(
            "Q1, nervous/anxious/on edge (0 not at all - 3 nearly every day)",
            questions[0][Fc.TEXT],
        )

        self.assertIn(
            "1. Feeling nervous, anxious or on edge", answers[0][Fc.TEXT]
        )
        self.assertIn(
            "Q1, nervous/anxious/on edge (0 not at all - 3 nearly every day)",
            answers[0][Fc.TEXT],
        )

        self.assertEqual(answers[0][Fc.ANSWER][0][Fc.VALUE_INTEGER], 0)
        self.assertEqual(answers[1][Fc.ANSWER][0][Fc.VALUE_INTEGER], 1)
        self.assertEqual(answers[2][Fc.ANSWER][0][Fc.VALUE_INTEGER], 2)
        self.assertEqual(answers[3][Fc.ANSWER][0][Fc.VALUE_INTEGER], 3)
