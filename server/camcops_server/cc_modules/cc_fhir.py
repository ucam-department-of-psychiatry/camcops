#!/usr/bin/env python

# noinspection HttpUrlsUsage
"""
camcops_server/cc_modules/cc_fhir.py

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

**Implements communication with a FHIR server.**

Fast Healthcare Interoperability Resources

https://www.hl7.org/fhir/

Our implementation exports:

- patients as FHIR Patient resources;
- task concepts as FHIR Questionnaire resources;
- task instances as FHIR QuestionnaireResponse resources.

Currently PHQ9 and APEQPT (anonymous) are supported. Each task and patient (if
appropriate is sent to the FHIR server in a single "transaction" Bundle).
The resources are given a unique identifier based on the URL of the CamCOPS
server.

We use the Python client https://github.com/smart-on-fhir/client-py/.
This only supports one version of the FHIR specification (currently 4.0.1).


*Testing: HAPI FHIR server locally*

To test with a HAPI FHIR server locally, which was installed from instructions
at https://github.com/hapifhir/hapi-fhir-jpaserver-starter (Docker). Most
simply:

.. code-block:: bash

    docker run -p 8080:8080 hapiproject/hapi:latest

with the following entry in the CamCOPS export recipient configuration:

.. code-block:: ini

    FHIR_API_URL = http://localhost:8080/fhir

To inspect it while it's running (apart from via its log):

- Browse to (by default) http://localhost:8080/

  - then e.g. Patient --> Search, which is a pretty version of
    http://localhost:8080/fhir/Patient?_pretty=true;

  - Questionnaire --> Search, which is a pretty version of
    http://localhost:8080/fhir/Questionnaire?_pretty=true.

- Can also browse to (by default) http://localhost:8080/fhir/metadata


*Testing: Other*

There are also public sandboxes at:

- http://hapi.fhir.org/baseR4
- https://r4.smarthealthit.org (errors when exporting questionnaire responses)


*Problems that have gone*

- "Failed to CREATE resource with match URL ... because this search matched 2
  resources" -- an OperationOutcome error.

  At https://groups.google.com/g/hapi-fhir/c/8OolMOpf8SU, it says (for an error
  with 40 resources) "You can only do a conditional create if there are 0..1
  existing resources on the server that match the criteria, and in this case
  there are 40." But I think that is an error in the explanation.

  Proper documentation for ``ifNoneExist`` (Python client) or ``If-None-Exist``
  (FHIR itself) is at https://www.hl7.org/fhir/http.html#ccreate.

  I suspect that "0..1" comment relates to "cardinality", which is how many
  times the attribute can appear in a resource type
  (https://www.hl7.org/fhir/conformance-rules.html#cardinality); that is, this
  statement is optional. It would clearly be silly if it meant "create if no
  more than 1 exist"!

  However, the "Failed to CREATE" problem seemed to go away. It does work fine,
  and you get status messages of "200 OK" rather than "201 Created" if you try
  to insert the same information again (``SELECT * FROM
  _exported_task_fhir_entry;``).

"""


# =============================================================================
# Imports
# =============================================================================

import json
import logging
from typing import Dict, TYPE_CHECKING

from fhirclient import client
from fhirclient.models.bundle import Bundle
from requests.exceptions import HTTPError

from camcops_server.cc_modules.cc_constants import FHIRConst as FC

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_exportmodels import ExportedTaskFhir
    from camcops_server.cc_modules.cc_request import CamcopsRequest

log = logging.getLogger(__name__)


# =============================================================================
# Debugging options
# =============================================================================

DEBUG_FHIR_PATIENT_ID = False

if any([DEBUG_FHIR_PATIENT_ID]):
    log.warning("Debugging options enabled!")


# =============================================================================
# Development thoughts
# =============================================================================

_ = """

- Dive into the internals of the HAPI FHIR server:

.. code-block:: bash

    docker container ls | grep hapi  # find its container ID
    docker exec -it <CONTAINER_NAME_OR_ID> bash
    
    # Find files modified in the last 10 minutes:
    find / -mmin -10 -type f -not -path "/proc/*" -not -path "/sys/*" -exec ls -l {} \;
    # ... which reveals /usr/local/tomcat/target/database/h2.mv.db
    #               and /usr/local/tomcat/logs/localhost_access_log*

    # Now, from http://h2database.com/html/tutorial.html#command_line_tools,
    find / -name "h2*.jar"
    # ... /usr/local/tomcat/webapps/ROOT/WEB-INF/lib/h2-1.4.200.jar
    
    java -cp /usr/local/tomcat/webapps/ROOT/WEB-INF/lib/h2*.jar org.h2.tools.Shell
    # - URL = jdbc:h2:/usr/local/tomcat/target/database/h2
    #   ... it will append ".mv.db"
    # - Accept other defaults.
    # - Then from the "sql>" prompt, try e.g. SHOW TABLES;

However, it won't connect with the server open. (And you can't stop the Docker
FHIR server and repeat the connection using ``docker run -it <IMAGE_ID> bash``
rather than ``docker exec``, because then the data will disappear as Docker
returns to its starting image.) But you can copy the database and open the
copy, e.g. with

.. code-block:: bash

    cd /usr/local/tomcat/target/database
    cp h2.mv.db h2_copy.mv.db
    java -cp /usr/local/tomcat/webapps/ROOT/WEB-INF/lib/h2*.jar org.h2.tools.Shell
    # URL = jdbc:h2:/usr/local/tomcat/target/database/h2_copy

but then that needs a username/password. Better is to create
``application.yaml`` in a host machine directory, like this:

.. code-block:: bash

    # From MySQL:
    # CREATE DATABASE hapi_test_db;
    # CREATE USER 'hapi_test_user'@'localhost' IDENTIFIED BY 'hapi_test_password';
    # GRANT ALL PRIVILEGES ON hapi_test_db.* TO 'hapi_test_user'@'localhost';

    mkdir ~/hapi_test
    cd ~/hapi_test
    git clone https://github.com/hapifhir/hapi-fhir-jpaserver-starter
    cd hapi-fhir-jpaserver-starter
    nano src/main/resources/application.yaml

... no, better is to use the web interface!

"""  # noqa


# =============================================================================
# Exceptions
# =============================================================================

class FhirExportException(Exception):
    pass


# =============================================================================
# Export tasks via FHIR
# =============================================================================

class FhirTaskExporter(object):
    """
    Class that knows how to export a single task to FHIR.
    """
    def __init__(self,
                 request: "CamcopsRequest",
                 exported_task_fhir: "ExportedTaskFhir") -> None:
        self.request = request
        self.exported_task = exported_task_fhir.exported_task
        self.exported_task_fhir = exported_task_fhir

        self.recipient = self.exported_task.recipient
        self.task = self.exported_task.task

        # TODO: In theory these settings should handle authentication
        # for any server that is SMART-compliant but we've not tested this.
        # https://sep.com/blog/smart-on-fhir-what-is-smart-what-is-fhir/
        settings = {
            FC.API_BASE: self.recipient.fhir_api_url,
            FC.APP_ID: self.recipient.fhir_app_id,
            FC.APP_SECRET: self.recipient.fhir_app_secret,
            FC.LAUNCH_TOKEN: self.recipient.fhir_launch_token,
        }

        try:
            self.client = client.FHIRClient(settings=settings)
        except Exception as e:
            raise FhirExportException(f"Error creating FHIRClient: {e}")

    def export_task(self) -> None:
        """
        Export a single task to the server, with associated patient information
        if the task has an associated patient.
        """
        # TODO: Check FHIR server's capability statement
        # https://www.hl7.org/fhir/capabilitystatement.html

        # statement = self.client.server.capabilityStatement
        # The client doesn't support looking for a particular capability
        # We could check for:
        # fhirVersion (the client does not support multiple versions)
        # conditional create
        # supported resource types (statement.rest[0].resource[])
        bundle_entries = []

        if self.task.has_patient:
            patient_entry = self.task.patient.get_fhir_bundle_entry(
                self.request,
                self.exported_task.recipient
            )
            bundle_entries.append(patient_entry)

        try:
            task_entries = self.task.get_fhir_bundle_entries(
                self.request,
                self.exported_task.recipient
            )
            bundle_entries += task_entries

        except NotImplementedError as e:
            raise FhirExportException(str(e))

        bundle = Bundle(jsondict={
            FC.TYPE: FC.TRANSACTION,
            FC.ENTRY: bundle_entries,
        })

        try:
            # Attempt to create the receiver on the server, via POST:
            if DEBUG_FHIR_PATIENT_ID:
                bundle_str = json.dumps(bundle.as_json(), indent=4)
                log.debug(f"FHIR bundle outbound to server:\n{bundle_str}")
            response = bundle.create(self.client.server)
            if response is None:
                # Not sure this will ever happen.
                # fhirabstractresource.py create() says it returns
                # "None or the response JSON on success" but an exception will
                # already have been raised if there was a failure
                raise FhirExportException(
                    "The FHIR server unexpectedly returned an OK, empty "
                    "response")

            self.parse_response(response)

        except HTTPError as e:
            raise FhirExportException(
                f"The FHIR server returned an error: {e.response.text}")

        except Exception as e:
            # Unfortunate that fhirclient doesn't give us anything more
            # specific
            raise FhirExportException(f"Error from fhirclient: {e}")

    def parse_response(self, response: Dict) -> None:
        """
        Parse the response from the FHIR server to which we have sent our
        task. The response looks something like this:

        .. code-block:: json

            {
              "resourceType": "Bundle",
              "id": "cae48957-e7e6-4649-97f8-0a882076ad0a",
              "type": "transaction-response",
              "link": [
                {
                  "relation": "self",
                  "url": "http://localhost:8080/fhir"
                }
              ],
              "entry": [
                {
                  "response": {
                    "status": "200 OK",
                    "location": "Patient/1/_history/1",
                    "etag": "1"
                  }
                },
                {
                  "response": {
                    "status": "200 OK",
                    "location": "Questionnaire/26/_history/1",
                    "etag": "1"
                  }
                },
                {
                  "response": {
                    "status": "201 Created",
                    "location": "QuestionnaireResponse/42/_history/1",
                    "etag": "1",
                    "lastModified": "2021-05-24T09:30:11.098+00:00"
                  }
                }
              ]
            }

        The server's reply contains a Bundle
        (https://www.hl7.org/fhir/bundle.html), which is a container for
        resources. Here, the bundle contains entry objects
        (https://www.hl7.org/fhir/bundle-definitions.html#Bundle.entry).

        """
        bundle = Bundle(jsondict=response)

        if bundle.entry is not None:
            self._save_exported_entries(bundle)

    def _save_exported_entries(self, bundle: Bundle) -> None:
        """
        Record the server's reply components in strucured format.
        """
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTaskFhirEntry
        )
        for entry in bundle.entry:
            saved_entry = ExportedTaskFhirEntry()
            saved_entry.exported_task_fhir_id = self.exported_task_fhir.id
            saved_entry.status = entry.response.status
            saved_entry.location = entry.response.location
            saved_entry.etag = entry.response.etag
            if entry.response.lastModified is not None:
                # ... of type :class:`fhirclient.models.fhirdate.FHIRDate
                saved_entry.last_modified = entry.response.lastModified.date

            self.request.dbsession.add(saved_entry)
