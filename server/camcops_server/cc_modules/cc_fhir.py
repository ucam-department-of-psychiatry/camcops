#!/usr/bin/env python

"""camcops_server/cc_modules/cc_fhir.py

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

**Implements communication with a FHIR server.**
"""

from typing import TYPE_CHECKING
from unittest import mock

from fhirclient import client
from fhirclient.models.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhirclient.models.humanname import HumanName
from fhirclient.models.identifier import Identifier
from fhirclient.models.patient import Patient as FhirPatient

from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_exportrecipientinfo import ExportRecipientInfo
from camcops_server.cc_modules.cc_pyramid import Routes
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_exportmodels import ExportedTaskFhir
    from camcops_server.cc_modules.cc_request import CamcopsRequest


class FhirExportException(Exception):
    pass


class PatchedBundle(Bundle):
    # Workaround https://github.com/smart-on-fhir/client-py/issues/102
    # TODO: Submit PR
    def relativeBase(self):
        if self.type == "transaction":
            return ""

        return super().relativeBase()


class FhirTaskExporter(object):
    def __init__(self,
                 request: "CamcopsRequest",
                 exported_task_fhir: "ExportedTaskFhir") -> None:
        self.request = request
        self.exported_task = exported_task_fhir.exported_task

        self.recipient = self.exported_task.recipient
        self.task = self.exported_task.task
        settings = {
            "app_id": "camcops",
            "api_base": self.recipient.fhir_api_url
        }

        self.client = client.FHIRClient(settings=settings)

    def export_task(self) -> None:
        # TODO: Authentication
        # TODO: Server capability statement
        # TODO: Anonymous tasks
        # TODO: Missing API URL in config

        which_idnum = self.recipient.primary_idnum
        idnum_object = self.task.patient.get_idnum_object(which_idnum)
        idnum_value = idnum_object.idnum_value
        idnum_url = self.request.route_url(
            Routes.FHIR_PATIENT_ID,
            which_idnum=which_idnum
        )

        identifier = Identifier(jsondict={
            "system": idnum_url,
            "value": str(idnum_value),
        })

        name = HumanName(jsondict={
            "family": self.task.patient.surname,
            "given": [self.task.patient.forename],
        })

        gender_lookup = {
            "F": "female",
            "M": "male",
            "X": "other",
        }

        patient = FhirPatient(jsondict={
            "identifier": [identifier.as_json()],
            "name": [name.as_json()],
            "gender": gender_lookup.get(self.task.patient.sex, "unknown")
        })

        request = BundleEntryRequest(jsondict={
            "method": "POST",
            "url": "Patient",
            "ifNoneExist": f"identifier={idnum_url}|{idnum_value}",
        })

        bundle_entries = [
            BundleEntry(jsondict={
                "resource": patient.as_json(),
                "request": request.as_json()
            }).as_json(),
        ]

        bundle = PatchedBundle(jsondict={
            "type": "transaction",
            "entry": bundle_entries,
        })

        bundle.create(self.client.server)

# =============================================================================
# Integration testing
# =============================================================================


class MockFhirTaskExporter(FhirTaskExporter):
    pass


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
        from camcops_server.tasks.phq9 import Phq9
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
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTask,
            ExportedTaskFhir,
        )

        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        with mock.patch.object(
                exporter.client.server, "post_json") as mock_post:
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
