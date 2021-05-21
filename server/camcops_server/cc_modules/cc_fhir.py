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

from fhirclient import client
from fhirclient.models.bundle import Bundle

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
        # TODO: Return value

        # TODO: Version of questionnaire?

        bundle_entries = [
            self.task.patient.get_fhir_bundle_entry(
                self.request,
                self.exported_task.recipient
            )
        ] + self.task.get_fhir_bundle_entries(
            self.request,
            self.exported_task.recipient
        )

        bundle = Bundle(jsondict={
            "type": "transaction",
            "entry": bundle_entries,
        })

        bundle.create(self.client.server)
