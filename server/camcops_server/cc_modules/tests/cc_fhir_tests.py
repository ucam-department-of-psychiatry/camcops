#!/usr/bin/env python

"""camcops_server/cc_modules/tests/cc_fhir_tests.py

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

import datetime
import json
from typing import Dict
from unittest import mock

from cardinal_pythonlib.httpconst import HttpMethod
import pendulum
from requests.exceptions import HTTPError

from camcops_server.cc_modules.cc_exportmodels import (
    ExportedTask,
    ExportedTaskFhir,
)
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_exportrecipientinfo import ExportRecipientInfo
from camcops_server.cc_modules.cc_fhir import (
    FhirExportException,
    FhirTaskExporter,
)
from camcops_server.cc_modules.cc_pyramid import Routes
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase
from camcops_server.tasks.apeqpt import Apeqpt
from camcops_server.tasks.phq9 import Phq9


# =============================================================================
# Integration testing
# =============================================================================

class MockFhirTaskExporter(FhirTaskExporter):
    pass


class MockFhirResponse(mock.Mock):
    def __init__(self, response_json: Dict):
        super().__init__(
            text=json.dumps(response_json),
            json=mock.Mock(return_value=response_json)
        )


class FhirExportTestCase(DemoDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        recipientinfo = ExportRecipientInfo()

        self.recipient = ExportRecipient(recipientinfo)
        self.recipient.primary_idnum = self.rio_iddef.which_idnum
        self.recipient.fhir_api_url = "https://www.example.com/fhir"

        # auto increment doesn't work for BigInteger with SQLite
        self.recipient.id = 1
        self.recipient.recipient_name = "test"

        self.camcops_root_url = self.req.route_url(Routes.HOME).rstrip("/")
        # ... no trailing slash


class FhirTaskExporterPhq9Tests(FhirExportTestCase):
    def create_tasks(self) -> None:
        self.patient = self.create_patient(
            forename="Gwendolyn",
            surname="Ryann",
            sex="F"
        )
        self.patient_nhs = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=8879736213
        )
        self.patient_rio = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.rio_iddef.which_idnum,
            idnum_value=12345
        )

        self.task = Phq9()
        self.apply_standard_task_fields(self.task)
        self.task.q1 = 0
        self.task.q2 = 1
        self.task.q3 = 2
        self.task.q4 = 3
        self.task.q5 = 0
        self.task.q6 = 1
        self.task.q7 = 2
        self.task.q8 = 3
        self.task.q9 = 0
        self.task.q10 = 3
        self.task.patient_id = self.patient.id
        self.task.save_with_next_available_id(self.req, self.patient._device_id)
        self.dbsession.commit()

    def test_patient_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            'type': 'transaction-response',
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        self.assertEqual(sent_json["resourceType"], "Bundle")
        self.assertEqual(sent_json["type"], "transaction")

        patient = sent_json["entry"][0]["resource"]
        self.assertEqual(patient["resourceType"], "Patient")

        identifier = patient["identifier"]
        which_idnum = self.patient_rio.which_idnum
        idnum_value = self.patient_rio.idnum_value

        iddef_url = (
            f"{self.camcops_root_url}/"
            f"{Routes.FHIR_PATIENT_ID_SYSTEM}/{which_idnum}"
        )

        self.assertEqual(identifier[0]["system"], iddef_url)
        self.assertEqual(identifier[0]["value"], str(idnum_value))

        self.assertEqual(patient["name"][0]["family"], self.patient.surname)
        self.assertEqual(patient["name"][0]["given"], [self.patient.forename])
        self.assertEqual(patient["gender"], "female")

        request = sent_json["entry"][0]["request"]
        self.assertEqual(request["method"], HttpMethod.POST)
        self.assertEqual(request["url"], "Patient")
        self.assertEqual(
            request["ifNoneExist"],
            (f"identifier={iddef_url}|{idnum_value}")
        )

    def test_questionnaire_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            'type': 'transaction-response',
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        questionnaire = sent_json["entry"][1]["resource"]
        self.assertEqual(questionnaire["resourceType"], "Questionnaire")
        self.assertEqual(questionnaire["status"], "active")

        identifier = questionnaire["identifier"]

        questionnaire_url = (
            f"{self.camcops_root_url}/{Routes.FHIR_QUESTIONNAIRE_ID}"
        )
        self.assertEqual(identifier[0]["system"], questionnaire_url)
        self.assertEqual(identifier[0]["value"], "phq9")

        question_1 = questionnaire["item"][0]
        question_10 = questionnaire["item"][9]
        self.assertEqual(question_1["linkId"], "q1")
        self.assertEqual(question_1["text"],
                         "1. Little interest or pleasure in doing things")
        self.assertEqual(question_1["type"], "choice")

        options = question_1["answerOption"]
        self.assertEqual(options[0]["valueCoding"]["code"], "0")
        self.assertEqual(options[0]["valueCoding"]["display"], "Not at all")

        self.assertEqual(options[1]["valueCoding"]["code"], "1")
        self.assertEqual(options[1]["valueCoding"]["display"], "Several days")

        self.assertEqual(options[2]["valueCoding"]["code"], "2")
        self.assertEqual(options[2]["valueCoding"]["display"],
                         "More than half the days")

        self.assertEqual(options[3]["valueCoding"]["code"], "3")
        self.assertEqual(options[3]["valueCoding"]["display"],
                         "Nearly every day")

        self.assertEqual(question_10["linkId"], "q10")
        self.assertEqual(
            question_10["text"],
            ("10. If you checked off any problems, how difficult have these "
             "problems made it for you to do your work, take care of things "
             "at home, or get along with other people?")
        )
        self.assertEqual(question_10["type"], "choice")
        options = question_10["answerOption"]
        self.assertEqual(options[0]["valueCoding"]["code"], "0")
        self.assertEqual(options[0]["valueCoding"]["display"],
                         "Not difficult at all")

        self.assertEqual(options[1]["valueCoding"]["code"], "1")
        self.assertEqual(options[1]["valueCoding"]["display"],
                         "Somewhat difficult")

        self.assertEqual(options[2]["valueCoding"]["code"], "2")
        self.assertEqual(options[2]["valueCoding"]["display"],
                         "Very difficult")

        self.assertEqual(options[3]["valueCoding"]["code"], "3")
        self.assertEqual(options[3]["valueCoding"]["display"],
                         "Extremely difficult")

        self.assertEqual(len(questionnaire["item"]), 10)

        request = sent_json["entry"][1]["request"]
        self.assertEqual(request["method"], HttpMethod.POST)
        self.assertEqual(request["url"], "Questionnaire")
        self.assertEqual(
            request["ifNoneExist"],
            (f"identifier={questionnaire_url}|phq9")
        )

    def test_questionnaire_response_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            'type': 'transaction-response',
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        response = sent_json["entry"][2]["resource"]
        self.assertEqual(response["resourceType"], "QuestionnaireResponse")
        self.assertEqual(
            response["questionnaire"],
            (
                f"{self.camcops_root_url}/"
                f"{Routes.FHIR_QUESTIONNAIRE_ID}|phq9"
            )
        )
        self.assertEqual(response["authored"],
                         self.task.when_created.isoformat())
        self.assertEqual(response["status"], "completed")

        subject = response["subject"]
        identifier = subject["identifier"]
        self.assertEqual(subject["type"], "Patient")
        which_idnum = self.patient_rio.which_idnum
        idnum_value = self.patient_rio.idnum_value

        iddef_url = (
            f"{self.camcops_root_url}/"
            f"{Routes.FHIR_PATIENT_ID_SYSTEM}/{which_idnum}"
        )
        self.assertEqual(identifier["system"], iddef_url)
        self.assertEqual(identifier["value"], str(idnum_value))

        request = sent_json["entry"][2]["request"]
        self.assertEqual(request["method"], HttpMethod.POST)
        self.assertEqual(request["url"], "QuestionnaireResponse")
        response_url = (
            f"{self.camcops_root_url}/"
            f"{Routes.FHIR_QUESTIONNAIRE_RESPONSE_ID}/phq9"
        )
        self.assertEqual(
            request["ifNoneExist"],
            (f"identifier={response_url}|{self.task._pk}")
        )

        item_1 = response["item"][0]
        item_10 = response["item"][9]
        self.assertEqual(item_1["linkId"], "q1")
        self.assertEqual(item_1["text"],
                         "1. Little interest or pleasure in doing things")
        answer_1 = item_1["answer"][0]
        self.assertEqual(answer_1["valueInteger"], self.task.q1)

        self.assertEqual(item_10["linkId"], "q10")
        self.assertEqual(
            item_10["text"],
            ("10. If you checked off any problems, how difficult have these "
             "problems made it for you to do your work, take care of things "
             "at home, or get along with other people?")
        )
        answer_10 = item_10["answer"][0]
        self.assertEqual(answer_10["valueInteger"], self.task.q10)

        self.assertEqual(len(response["item"]), 10)

    def test_exported_task_saved(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        # auto increment doesn't work for BigInteger with SQLite
        exported_task.id = 1
        self.dbsession.add(exported_task)

        exported_task_fhir = ExportedTaskFhir(exported_task)
        self.dbsession.add(exported_task_fhir)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            'resourceType': 'Bundle',
            'id': 'cae48957-e7e6-4649-97f8-0a882076ad0a',
            'type': 'transaction-response',
            'link': [
                {
                    'relation': 'self',
                    'url': 'http://localhost:8080/fhir'
                }
            ],
            'entry': [
                {
                    'response': {
                        'status': '200 OK',
                        'location': 'Patient/1/_history/1',
                        'etag': '1'
                    }
                },
                {
                    'response': {
                        'status': '200 OK',
                        'location': 'Questionnaire/26/_history/1',
                        'etag': '1'
                    }
                },
                {
                    'response': {
                        'status': '201 Created',
                        'location': 'QuestionnaireResponse/42/_history/1',
                        'etag': '1',
                        'lastModified': '2021-05-24T09:30:11.098+00:00'
                    }
                }
            ]
        }

        with mock.patch.object(exporter.client.server, "post_json",
                               return_value=MockFhirResponse(response_json)):
            exporter.export_task()

        self.dbsession.commit()

        entries = exported_task_fhir.entries

        entries.sort(key=lambda e: e.location)

        self.assertEqual(entries[0].status, "200 OK")
        self.assertEqual(entries[0].location, "Patient/1/_history/1")
        self.assertEqual(entries[0].etag, "1")

        self.assertEqual(entries[1].status, "200 OK")
        self.assertEqual(entries[1].location, "Questionnaire/26/_history/1")
        self.assertEqual(entries[1].etag, "1")

        self.assertEqual(entries[2].status, "201 Created")
        self.assertEqual(entries[2].location,
                         "QuestionnaireResponse/42/_history/1")
        self.assertEqual(entries[2].etag, "1")
        self.assertEqual(entries[2].last_modified,
                         datetime.datetime(2021, 5, 24, 9, 30, 11, 98000))

    def test_raises_when_task_does_not_support(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        with mock.patch.object(self.task,
                               "get_fhir_bundle_entries") as mock_task:
            mock_task.side_effect = NotImplementedError(
                "Something is not implemented"
            )

            with self.assertRaises(FhirExportException) as cm:
                exporter.export_task()

            message = str(cm.exception)
            self.assertIn("Something is not implemented", message)

    def test_raises_when_http_error(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        with mock.patch.object(
                exporter.client.server, "post_json",
                side_effect=HTTPError(
                    response=mock.Mock(text="Something bad happened")
                )
        ):
            with self.assertRaises(FhirExportException) as cm:
                exporter.export_task()

            message = str(cm.exception)
            self.assertIn("Something bad happened", message)

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


class FhirTaskExporterAnonymousTests(FhirExportTestCase):
    def create_tasks(self) -> None:
        self.task = Apeqpt()
        self.apply_standard_task_fields(self.task)
        self.task.q_datetime = pendulum.now()
        self.task.q1_choice = 0
        self.task.q2_choice = 1
        self.task.q3_choice = 2
        self.task.q1_satisfaction = 3
        self.task.q2_satisfaction = "Service experience"

        self.task.save_with_next_available_id(self.req,
                                              self.server_device.id)
        self.dbsession.commit()

    def test_questionnaire_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            'type': 'transaction-response',
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        questionnaire = sent_json["entry"][0]["resource"]
        self.assertEqual(questionnaire["resourceType"], "Questionnaire")
        self.assertEqual(questionnaire["status"], "active")

        identifier = questionnaire["identifier"]

        questionnaire_url = (
            f"{self.camcops_root_url}/{Routes.FHIR_QUESTIONNAIRE_ID}"
        )
        self.assertEqual(identifier[0]["system"], questionnaire_url)
        self.assertEqual(identifier[0]["value"], "apeqpt")

        q_datetime = questionnaire["item"][0]

        q1_choice = questionnaire["item"][1]
        q2_choice = questionnaire["item"][2]
        q3_choice = questionnaire["item"][3]

        q1_satisfaction = questionnaire["item"][4]
        q2_satisfaction = questionnaire["item"][5]

        # q_datetime
        self.assertEqual(q_datetime["linkId"], "q_datetime")
        self.assertEqual(q_datetime["text"],
                         "Date &amp; Time the Assessment Tool was Completed")
        self.assertEqual(q_datetime["type"], "dateTime")

        # q1_choice
        self.assertEqual(q1_choice["linkId"], "q1_choice")
        self.assertEqual(
            q1_choice["text"],
            ("Were you given information about options for choosing a "
             "treatment that is appropriate for your problems?")
        )
        self.assertEqual(q1_choice["type"], "choice")

        options = q1_choice["answerOption"]
        self.assertEqual(options[0]["valueCoding"]["code"], "0")
        self.assertEqual(options[0]["valueCoding"]["display"], "No")

        self.assertEqual(options[1]["valueCoding"]["code"], "1")
        self.assertEqual(options[1]["valueCoding"]["display"], "Yes")

        # q2_choice
        self.assertEqual(q2_choice["linkId"], "q2_choice")
        self.assertEqual(
            q2_choice["text"],
            ("Do you prefer any of the treatments among the options available?")
        )
        self.assertEqual(q2_choice["type"], "choice")
        options = q2_choice["answerOption"]
        self.assertEqual(options[0]["valueCoding"]["code"], "0")
        self.assertEqual(options[0]["valueCoding"]["display"], "No")

        self.assertEqual(options[1]["valueCoding"]["code"], "1")
        self.assertEqual(options[1]["valueCoding"]["display"], "Yes")

        # q3_choice
        self.assertEqual(q3_choice["linkId"], "q3_choice")
        self.assertEqual(
            q3_choice["text"],
            ("Have you been offered your preference?")
        )
        self.assertEqual(q3_choice["type"], "choice")
        options = q3_choice["answerOption"]
        self.assertEqual(options[0]["valueCoding"]["code"], "0")
        self.assertEqual(options[0]["valueCoding"]["display"], "No")

        self.assertEqual(options[1]["valueCoding"]["code"], "1")
        self.assertEqual(options[1]["valueCoding"]["display"], "Yes")

        self.assertEqual(options[2]["valueCoding"]["code"], "2")
        self.assertEqual(options[2]["valueCoding"]["display"], "N/A")

        # q1_satisfaction
        self.assertEqual(q1_satisfaction["linkId"], "q1_satisfaction")
        self.assertEqual(
            q1_satisfaction["text"],
            ("How satisfied were you with your assessment")
        )
        self.assertEqual(q1_satisfaction["type"], "choice")
        options = q1_satisfaction["answerOption"]
        self.assertEqual(options[0]["valueCoding"]["code"], "0")
        self.assertEqual(options[0]["valueCoding"]["display"],
                         "Not at all Satisfied")

        self.assertEqual(options[1]["valueCoding"]["code"], "1")
        self.assertEqual(options[1]["valueCoding"]["display"], "Not Satisfied")

        self.assertEqual(options[2]["valueCoding"]["code"], "2")
        self.assertEqual(options[2]["valueCoding"]["display"],
                         "Neither Satisfied nor Dissatisfied")

        self.assertEqual(options[3]["valueCoding"]["code"], "3")
        self.assertEqual(options[3]["valueCoding"]["display"],
                         "Mostly Satisfied")

        self.assertEqual(options[4]["valueCoding"]["code"], "4")
        self.assertEqual(options[4]["valueCoding"]["display"],
                         "Completely Satisfied")

        # q2 satisfaction
        self.assertEqual(q2_satisfaction["linkId"], "q2_satisfaction")
        self.assertEqual(
            q2_satisfaction["text"],
            ("Please use this space to tell us about your experience of our "
             "service")
        )
        self.assertEqual(q2_satisfaction["type"], "string")

        self.assertEqual(len(questionnaire["item"]), 6)

        request = sent_json["entry"][0]["request"]
        self.assertEqual(request["method"], HttpMethod.POST)
        self.assertEqual(request["url"], "Questionnaire")
        self.assertEqual(
            request["ifNoneExist"],
            (f"identifier={questionnaire_url}|apeqpt")
        )

    def test_questionnaire_response_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            'type': 'transaction-response',
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        response = sent_json["entry"][1]["resource"]
        self.assertEqual(response["resourceType"], "QuestionnaireResponse")
        self.assertEqual(
            response["questionnaire"],
            (
                f"{self.camcops_root_url}/"
                f"{Routes.FHIR_QUESTIONNAIRE_ID}|apeqpt"
            )
        )
        self.assertEqual(response["authored"],
                         self.task.when_created.isoformat())
        self.assertEqual(response["status"], "completed")

        request = sent_json["entry"][1]["request"]
        self.assertEqual(request["method"], HttpMethod.POST)
        self.assertEqual(request["url"], "QuestionnaireResponse")
        response_url = (
            f"{self.camcops_root_url}/"
            f"{Routes.FHIR_QUESTIONNAIRE_RESPONSE_ID}/apeqpt"
        )
        self.assertEqual(
            request["ifNoneExist"],
            (f"identifier={response_url}|{self.task._pk}")
        )

        q_datetime = response["item"][0]

        q1_choice = response["item"][1]
        q2_choice = response["item"][2]
        q3_choice = response["item"][3]

        q1_satisfaction = response["item"][4]
        q2_satisfaction = response["item"][5]

        # q_datetime
        self.assertEqual(q_datetime["linkId"], "q_datetime")
        self.assertEqual(q_datetime["text"],
                         "Date &amp; Time the Assessment Tool was Completed")
        q_datetime_answer = q_datetime["answer"][0]
        self.assertEqual(q_datetime_answer["valueDateTime"],
                         self.task.q_datetime.isoformat())

        # q1_choice
        self.assertEqual(q1_choice["linkId"], "q1_choice")
        self.assertEqual(
            q1_choice["text"],
            ("Were you given information about options for choosing a "
             "treatment that is appropriate for your problems?")
        )
        q1_choice_answer = q1_choice["answer"][0]
        self.assertEqual(q1_choice_answer["valueInteger"], self.task.q1_choice)

        # q2_choice
        self.assertEqual(q2_choice["linkId"], "q2_choice")
        self.assertEqual(
            q2_choice["text"],
            ("Do you prefer any of the treatments among the options available?")
        )
        q2_choice_answer = q2_choice["answer"][0]
        self.assertEqual(q2_choice_answer["valueInteger"], self.task.q2_choice)

        # q3_choice
        self.assertEqual(q3_choice["linkId"], "q3_choice")
        self.assertEqual(
            q3_choice["text"],
            ("Have you been offered your preference?")
        )
        q3_choice_answer = q3_choice["answer"][0]
        self.assertEqual(q3_choice_answer["valueInteger"], self.task.q3_choice)

        # q1_satisfaction
        self.assertEqual(q1_satisfaction["linkId"], "q1_satisfaction")
        self.assertEqual(
            q1_satisfaction["text"],
            ("How satisfied were you with your assessment")
        )
        q1_satisfaction_answer = q1_satisfaction["answer"][0]
        self.assertEqual(q1_satisfaction_answer["valueInteger"],
                         self.task.q1_satisfaction)

        # q2 satisfaction
        self.assertEqual(q2_satisfaction["linkId"], "q2_satisfaction")
        self.assertEqual(
            q2_satisfaction["text"],
            ("Please use this space to tell us about your experience of our "
             "service")
        )
        q2_satisfaction_answer = q2_satisfaction["answer"][0]
        self.assertEqual(q2_satisfaction_answer["valueString"],
                         self.task.q2_satisfaction)

        self.assertEqual(len(response["item"]), 6)
