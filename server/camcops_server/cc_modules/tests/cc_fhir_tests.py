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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

"""

import datetime
import json
from typing import Dict
from unittest import mock

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
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase
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
        self.recipient.fhir_api_url = "http://www.example.com/fhir"

        # auto increment doesn't work for BigInteger with SQLite
        self.recipient.id = 1
        self.recipient.recipient_name = "test"


class FhirTaskExporterTests(FhirExportTestCase):
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

    def test_patient_exported_with_phq9(self) -> None:
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

        iddef_url = f"http://127.0.0.1:8000/fhir_patient_id/{which_idnum}"

        self.assertEqual(identifier[0]["system"], iddef_url)
        self.assertEqual(identifier[0]["value"], str(idnum_value))

        self.assertEqual(patient["name"][0]["family"], self.patient.surname)
        self.assertEqual(patient["name"][0]["given"], [self.patient.forename])
        self.assertEqual(patient["gender"], "female")

        request = sent_json["entry"][0]["request"]
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["url"], "Patient")
        self.assertEqual(
            request["ifNoneExist"],
            (f"identifier={iddef_url}|{idnum_value}")
        )

    def test_questionnaire_exported_with_phq9(self) -> None:
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

        questionnaire_url = "http://127.0.0.1:8000/fhir_questionnaire_id"
        self.assertEqual(identifier[0]["system"], questionnaire_url)
        self.assertEqual(identifier[0]["value"], "phq9")

        question_1 = questionnaire["item"][0]
        question_10 = questionnaire["item"][9]
        self.assertEqual(question_1["linkId"], "q1")
        self.assertEqual(question_1["text"],
                         "1. Little interest or pleasure in doing things")
        self.assertEqual(question_1["type"], "choice")

        self.assertEqual(question_10["linkId"], "q10")
        self.assertEqual(
            question_10["text"],
            ("10. If you checked off any problems, how difficult have these "
             "problems made it for you to do your work, take care of things "
             "at home, or get along with other people?")
        )
        self.assertEqual(question_10["type"], "choice")
        self.assertEqual(len(questionnaire["item"]), 10)

        request = sent_json["entry"][1]["request"]
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["url"], "Questionnaire")
        self.assertEqual(
            request["ifNoneExist"],
            (f"identifier={questionnaire_url}|phq9")
        )

    def test_questionnaire_response_exported_with_phq9(self) -> None:
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
            "http://127.0.0.1:8000/fhir_questionnaire_id|phq9"
        )
        self.assertEqual(response["status"], "completed")

        subject = response["subject"]
        identifier = subject["identifier"]
        self.assertEqual(subject["type"], "Patient")
        which_idnum = self.patient_rio.which_idnum
        idnum_value = self.patient_rio.idnum_value

        iddef_url = f"http://127.0.0.1:8000/fhir_patient_id/{which_idnum}"
        self.assertEqual(identifier["system"], iddef_url)
        self.assertEqual(identifier["value"], str(idnum_value))

        request = sent_json["entry"][2]["request"]
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["url"], "QuestionnaireResponse")
        response_url = "http://127.0.0.1:8000/fhir_questionnaire_response_id/phq9"  # noqa E501
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
