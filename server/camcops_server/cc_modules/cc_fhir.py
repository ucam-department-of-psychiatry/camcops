#!/usr/bin/env python

# noinspection HttpUrlsUsage
"""
camcops_server/cc_modules/cc_fhir.py

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


*Intermittent problem with If-None-Exist*

This problem occurs intermittently:

- "Failed to CREATE resource with match URL ... because this search matched 2
  resources" -- an OperationOutcome error.

  At https://groups.google.com/g/hapi-fhir/c/8OolMOpf8SU, it says (for an error
  with 40 resources) "You can only do a conditional create if there are 0..1
  existing resources on the server that match the criteria, and in this case
  there are 40." But I think that is an error in the explanation.

  Proper documentation for ``ifNoneExist`` (Python client) or ``If-None-Exist``
  (FHIR itself) is at https://www.hl7.org/fhir/http.html#ccreate.

  I suspect that "0..1" comment relates to "cardinality"
  (https://www.hl7.org/fhir/bundle.html#resource), which is how many times the
  attribute can appear in a resource type
  (https://www.hl7.org/fhir/conformance-rules.html#cardinality); that is, this
  statement is optional. It would clearly be silly if it meant "create if no
  more than 1 exist"!

  However, the "Failed to CREATE" problem seemed to go away. It does work fine,
  and you get status messages of "200 OK" rather than "201 Created" if you try
  to insert the same information again (``SELECT * FROM
  _exported_task_fhir_entry;``).

- This is a concurrency problem (they dispute "bug") in the HAPI FHIR
  implementation. See our bug report at
  https://github.com/hapifhir/hapi-fhir/issues/3141.

- The suggested fix is a "unique combo search index parameter", as per
  https://smilecdr.com/docs/fhir_repository/custom_search_parameters.html#uniqueness.

- However, that seems implementation-specific (e.g. HAPI FHIR, SmileCDR). A
  specific value of ``http://hapifhir.io/fhir/StructureDefinition/sp-unique``
  must be used. Specimen code is
  https://hapifhir.io/hapi-fhir/apidocs/hapi-fhir-base/src-html/ca/uhn/fhir/util/HapiExtensions.html.

- Instead, we could force a FHIR export for a given recipient to occur in
  serial (particularly as other FHIR implementations may have this bug).

  Celery doesn't allow you to send multiple jobs and enforce that they all
  happen via the same worker
  (https://docs.celeryproject.org/en/stable/userguide/calling.html). However,
  our exports already start (mostly!) as "one recipient, one job", via
  :func:`camcops_server.cc_modules.celery.export_to_recipient_backend` (see
  :func:`camcops_server.cc_modules.celery.get_celery_settings_dict`).

  The tricky bit is that push exports require back-end single-task jobs, so
  they are hard to de-parallelize.

  So we use a carefully sequenced file lock; see
  :func:`camcops_server.cc_modules.cc_export.export_task`.

"""  # noqa


# =============================================================================
# Imports
# =============================================================================

from enum import Enum
import json
import logging
from typing import Any, Dict, List, TYPE_CHECKING

from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.httpconst import HttpMethod
from fhirclient.client import FHIRClient
from fhirclient.models.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.fhirdate import FHIRDate
from fhirclient.models.identifier import Identifier
from fhirclient.models.observation import ObservationComponent
from fhirclient.models.questionnaire import (
    QuestionnaireItem,
    QuestionnaireItemAnswerOption,
)
from fhirclient.models.quantity import Quantity
from fhirclient.models.questionnaireresponse import (
    QuestionnaireResponseItem,
    QuestionnaireResponseItemAnswer,
)
from requests.exceptions import HTTPError

from camcops_server.cc_modules.cc_constants import (
    DateFormat,
    FHIRConst as Fc,
    JSON_INDENT,
)
from camcops_server.cc_modules.cc_exception import FhirExportException
from camcops_server.cc_modules.cc_pyramid import Routes
from camcops_server.cc_modules.cc_snomed import SnomedExpression, SnomedLookup

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_exportmodels import ExportedTaskFhir
    from camcops_server.cc_modules.cc_request import CamcopsRequest

log = logging.getLogger(__name__)


# =============================================================================
# Debugging options
# =============================================================================

DEBUG_FHIR_TX = False  # needs workers to be launched with "--verbose" option

if any([DEBUG_FHIR_TX]):
    log.warning("Debugging options enabled!")


# =============================================================================
# Development thoughts
# =============================================================================

_ = """

Dive into the internals of the HAPI FHIR server
===============================================

.. code-block:: bash

    docker container ls | grep hapi  # find its container ID
    docker exec -it <CONTAINER_NAME_OR_ID> bash

    # Find files modified in the last 10 minutes:
    find / -mmin -10 -type f -not -path "/proc/*" -not -path "/sys/*" -exec ls -l {} \;
    # ... which reveals /usr/local/tomcat/target/database/h2.mv.db
    #               and /usr/local/tomcat/logs/localhost_access_log*

    # Now, from https://h2database.com/html/tutorial.html#command_line_tools,
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


Wipe FHIR exports
=================

.. code-block:: sql

    -- Delete all records of tasks exported via FHIR:
    DELETE FROM _exported_task_fhir_entry;
    DELETE FROM _exported_task_fhir;
    DELETE FROM _exported_tasks WHERE recipient_id IN (
        SELECT id FROM _export_recipients WHERE transmission_method = 'fhir'
    );

    -- Delete ALL export information
    DELETE FROM _exported_task_fhir_entry;
    DELETE FROM _exported_task_fhir;
    DELETE FROM _exported_task_email;
    DELETE FROM _exported_task_filegroup;
    DELETE FROM _exported_task_hl7msg;
    DELETE FROM _exported_task_redcap;
    DELETE FROM _exported_tasks;
    DELETE FROM _export_recipients;

What's been sent?

.. code-block:: sql

    -- Tasks exported via FHIR:
    SELECT * FROM _exported_tasks WHERE recipient_id IN (
        SELECT id FROM _export_recipients WHERE transmission_method = 'fhir'
    );

    -- Entries for all BMI tasks:
    SELECT * FROM _exported_task_fhir_entry WHERE exported_task_fhir_id IN (
        SELECT _exported_task_fhir.id FROM _exported_task_fhir
        INNER JOIN _exported_tasks
            ON _exported_task_fhir.exported_task_id = _exported_tasks.id
        INNER JOIN _export_recipients
            ON _exported_tasks.recipient_id = _export_recipients.id
        WHERE _export_recipients.transmission_method = 'fhir'
        AND _exported_tasks.basetable = 'bmi'
    );


Inspecting fhirclient
=====================

Each class has entries like this:

.. code-block:: python

    def elementProperties(self):
        js = super(DocumentReference, self).elementProperties()
        js.extend([
            ("authenticator", "authenticator", fhirreference.FHIRReference, False, None, False),
            ("author", "author", fhirreference.FHIRReference, True, None, False),
            # ...
        ])
        return js

The fields are: ``name, jsname, typ, is_list, of_many, not_optional``.
They are validated in FHIRAbstractBase.update_with_json().

"""  # noqa


# =============================================================================
# Export tasks via FHIR
# =============================================================================


class FhirTaskExporter(object):
    """
    Class that knows how to export a single task to FHIR.
    """

    def __init__(
        self, request: "CamcopsRequest", exported_task_fhir: "ExportedTaskFhir"
    ) -> None:
        self.request = request
        self.exported_task = exported_task_fhir.exported_task
        self.exported_task_fhir = exported_task_fhir

        self.recipient = self.exported_task.recipient
        self.task = self.exported_task.task

        # TODO: In theory these settings should handle authentication
        # for any server that is SMART-compliant but we've not tested this.
        # https://sep.com/blog/smart-on-fhir-what-is-smart-what-is-fhir/
        settings = {
            Fc.API_BASE: self.recipient.fhir_api_url,
            Fc.APP_ID: self.recipient.fhir_app_id,
            Fc.APP_SECRET: self.recipient.fhir_app_secret,
            Fc.LAUNCH_TOKEN: self.recipient.fhir_launch_token,
        }

        try:
            self.client = FHIRClient(settings=settings)
        except Exception as e:
            raise FhirExportException(f"Error creating FHIRClient: {e}")

    def export_task(self) -> None:
        """
        Export a single task to the server, with associated patient information
        if the task has an associated patient.
        """

        # TODO: Check FHIR server's capability statement
        # https://www.hl7.org/fhir/capabilitystatement.html
        #
        # statement = self.client.server.capabilityStatement
        # The client doesn't support looking for a particular capability
        # We could check for:
        # fhirVersion (the client does not support multiple versions)
        # conditional create
        # supported resource types (statement.rest[0].resource[])

        bundle = self.task.get_fhir_bundle(
            self.request, self.exported_task.recipient
        )  # may raise FhirExportException

        try:
            # Attempt to create the receiver on the server, via POST:
            if DEBUG_FHIR_TX:
                bundle_str = json.dumps(bundle.as_json(), indent=JSON_INDENT)
                log.debug(f"FHIR bundle outbound to server:\n{bundle_str}")
            response = bundle.create(self.client.server)
            if response is None:
                # Not sure this will ever happen.
                # fhirabstractresource.py create() says it returns
                # "None or the response JSON on success" but an exception will
                # already have been raised if there was a failure
                raise FhirExportException(
                    "The FHIR server unexpectedly returned an OK, empty "
                    "response"
                )

            self.parse_response(response)

        except HTTPError as e:
            raise FhirExportException(
                f"The FHIR server returned an error: {e.response.text}"
            )

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
            ExportedTaskFhirEntry,
        )  # delayed import

        for entry in bundle.entry:
            saved_entry = ExportedTaskFhirEntry()
            saved_entry.exported_task_fhir_id = self.exported_task_fhir.id
            saved_entry.status = entry.response.status
            saved_entry.location = entry.response.location
            saved_entry.etag = entry.response.etag
            if entry.response.lastModified is not None:
                # ... of type :class:`fhirclient.models.fhirdate.FHIRDate`
                saved_entry.last_modified = entry.response.lastModified.date

            self.request.dbsession.add(saved_entry)


# =============================================================================
# Helper functions for building FHIR component objects
# =============================================================================


def fhir_pk_identifier(
    req: "CamcopsRequest", tablename: str, pk: int, value_within_task: str
) -> Identifier:
    """
    Creates a "fallback" identifier -- this is poor, but allows unique
    identification of anything (such as a patient with no proper ID numbers)
    based on its CamCOPS table name and server PK.
    """
    return Identifier(
        jsondict={
            Fc.SYSTEM: req.route_url(
                Routes.FHIR_TABLENAME_PK_ID, table_name=tablename, server_pk=pk
            ),
            Fc.VALUE: value_within_task,
        }
    )


def fhir_system_value(system: str, value: str) -> str:
    """
    How FHIR expresses system/value pairs.
    """
    return f"{system}|{value}"


def fhir_sysval_from_id(identifier: Identifier) -> str:
    """
    How FHIR expresses system/value pairs.
    """
    return f"{identifier.system}|{identifier.value}"


def fhir_reference_from_identifier(identifier: Identifier) -> str:
    """
    Returns a reference to a specific FHIR identifier.
    """
    return f"{Fc.IDENTIFIER}={fhir_sysval_from_id(identifier)}"


def fhir_observation_component_from_snomed(
    req: "CamcopsRequest", expr: SnomedExpression
) -> Dict:
    """
    Returns a FHIR ObservationComponent (as a dict in JSON format) for a SNOMED
    CT expression.
    """
    observable_entity = req.snomed(SnomedLookup.OBSERVABLE_ENTITY)
    expr_longform = expr.as_string(longform=True)
    # For SNOMED, we are providing an observation where the "value" is a code
    # -- thus, we use "valueCodeableConcept" as the specific value (the generic
    # being "value<something>" or what FHIR calls "value[x]"). But there also
    # needs to be a coding system, specified via "code".
    return ObservationComponent(
        jsondict={
            # code = "the type of thing reported here"
            # Per https://www.hl7.org/fhir/observation.html#code-interop, we
            # use SNOMED 363787002 = Observable entity.
            Fc.CODE: CodeableConcept(
                jsondict={
                    Fc.CODING: [
                        Coding(
                            jsondict={
                                Fc.SYSTEM: Fc.CODE_SYSTEM_SNOMED_CT,
                                Fc.CODE: str(observable_entity.identifier),
                                Fc.DISPLAY: observable_entity.as_string(
                                    longform=True
                                ),
                                Fc.USER_SELECTED: False,
                            }
                        ).as_json()
                    ],
                    Fc.TEXT: observable_entity.term,
                }
            ).as_json(),
            # value = "the value of the thing"; the actual SNOMED code of
            # interest:
            Fc.VALUE_CODEABLE_CONCEPT: CodeableConcept(
                jsondict={
                    Fc.CODING: [
                        Coding(
                            jsondict={
                                # http://www.hl7.org/fhir/snomedct.html
                                Fc.SYSTEM: Fc.CODE_SYSTEM_SNOMED_CT,
                                Fc.CODE: expr.as_string(longform=False),
                                Fc.DISPLAY: expr_longform,
                                Fc.USER_SELECTED: False,
                                # ... means "did the user choose it
                                # themselves?"
                                # version: not used
                            }
                        ).as_json()
                    ],
                    Fc.TEXT: expr_longform,
                }
            ).as_json(),
        }
    ).as_json()


def make_fhir_bundle_entry(
    resource_type_url: str,
    identifier: Identifier,
    resource: Dict,
    identifier_is_list: bool = True,
) -> Dict:
    """
    Builds a FHIR BundleEntry, as a JSON dict.

    This also takes care of the identifier, by ensuring (a) that the resource
    is labelled with the identifier, and (b) that the BundleEntryRequest has
    an ifNoneExist condition referring to that identifier.
    """
    if Fc.IDENTIFIER in resource:
        log.warning(
            f"Duplication: {Fc.IDENTIFIER!r} specified in resource "
            f"but would be auto-added by make_fhir_bundle_entry()"
        )
    if identifier_is_list:
        # Some, like Observation, Patient, and Questionnaire, need lists here.
        resource[Fc.IDENTIFIER] = [identifier.as_json()]
    else:
        # Others, like QuestionnaireResponse, don't.
        resource[Fc.IDENTIFIER] = identifier.as_json()
    bundle_request = BundleEntryRequest(
        jsondict={
            Fc.METHOD: HttpMethod.POST,
            Fc.URL: resource_type_url,
            Fc.IF_NONE_EXIST: fhir_reference_from_identifier(identifier),
            # "If this resource doesn't exist, as determined by this
            # identifier, then create it:"
            # https://www.hl7.org/fhir/http.html#ccreate
        }
    )
    return BundleEntry(
        jsondict={Fc.REQUEST: bundle_request.as_json(), Fc.RESOURCE: resource}
    ).as_json()


# =============================================================================
# Helper classes for building FHIR component objects
# =============================================================================


class FHIRQuestionType(Enum):
    """
    An enum for value type keys of QuestionnaireResponseItemAnswer.
    """

    ATTACHMENT = Fc.QITEM_TYPE_ATTACHMENT
    BOOLEAN = Fc.QITEM_TYPE_BOOLEAN
    CHOICE = Fc.QITEM_TYPE_CHOICE
    DATE = Fc.QITEM_TYPE_DATE
    DATETIME = Fc.QITEM_TYPE_DATETIME
    DECIMAL = Fc.QITEM_TYPE_DECIMAL
    DISPLAY = Fc.QITEM_TYPE_DISPLAY
    GROUP = Fc.QITEM_TYPE_GROUP
    INTEGER = Fc.QITEM_TYPE_INTEGER
    OPEN_CHOICE = Fc.QITEM_TYPE_OPEN_CHOICE
    QUANTITY = Fc.QITEM_TYPE_QUANTITY
    QUESTION = Fc.QITEM_TYPE_QUESTION
    REFERENCE = Fc.QITEM_TYPE_REFERENCE
    STRING = Fc.QITEM_TYPE_STRING
    TIME = Fc.QITEM_TYPE_TIME
    URL = Fc.QITEM_TYPE_URL


class FHIRAnswerType(Enum):
    """
    An enum for value type keys of QuestionnaireResponseItemAnswer.
    """

    ATTACHMENT = Fc.VALUE_ATTACHMENT
    BOOLEAN = Fc.VALUE_BOOLEAN
    CODING = Fc.VALUE_CODING
    DATE = Fc.VALUE_DATE
    DATETIME = Fc.VALUE_DATETIME
    DECIMAL = Fc.VALUE_DECIMAL
    INTEGER = Fc.VALUE_INTEGER
    QUANTITY = Fc.VALUE_QUANTITY  # e.g. real number
    REFERENCE = Fc.VALUE_REFERENCE
    STRING = Fc.VALUE_STRING
    TIME = Fc.VALUE_TIME
    URI = Fc.VALUE_URI


class FHIRAnsweredQuestion:
    """
    Represents a question in a questionnaire-based task. That includes both the
    abstract aspects:

    - What kind of question is it (e.g. multiple-choice, real-value answer,
      text)? That can go into some detail, e.g. possible responses for a
      multiple-choice question. (Thus, the FHIR Questionnaire.)

    and the concrete aspects:

    - what is the response/answer for a specific task instance?
      (Thus, the FHIR QuestionnaireResponse.)

    Used for autodiscovery.
    """

    def __init__(
        self,
        qname: str,
        qtext: str,
        qtype: FHIRQuestionType,
        answer_type: FHIRAnswerType,
        answer: Any,
        answer_options: Dict[Any, str] = None,
    ) -> None:
        """
        Args:
            qname:
                Name (task attribute name) of the question, e.g. "q1".
            qtext:
                Question text (e.g. "How was your day?").
            qtype:
                Question type, e.g. multiple-choice.
            answer_type:
                Answer type, e.g. integer.
            answer:
                Actual answer.
            answer_options:
                For multiple-choice questions (MCQs), a dictionary mapping
                answer codes to human-legible display text.
        """
        self.qname = qname
        self.qtext = qtext
        self.qtype = qtype
        self.answer = answer
        self.answer_type = answer_type
        self.answer_options = answer_options or {}  # type: Dict[Any, str]

        # Checks
        if self.is_mcq:
            assert self.answer_options, (
                f"Multiple choice item {self.qname!r} needs mcq_qa parameter, "
                f"currently {answer_options!r}"
            )

    def __str__(self) -> str:
        if self.is_mcq:
            options = " / ".join(
                f"{code} = {display}"
                for code, display in self.answer_options.items()
            )
        else:
            options = "N/A"
        return (
            f"{self.qname} "
            f"// QUESTION: {self.qtext} "
            f"// OPTIONS: {options} "
            f"// ANSWER: {self.answer!r}, of type {self.answer_type.value}"
        )

    @property
    def is_mcq(self) -> bool:
        """
        Is this a multiple-choice question?
        """
        return self.qtype in (
            FHIRQuestionType.CHOICE,
            FHIRQuestionType.OPEN_CHOICE,
        )

    # -------------------------------------------------------------------------
    # Abstract (class)
    # -------------------------------------------------------------------------

    def questionnaire_item(self) -> Dict:
        """
        Returns a JSON/dict representation of a FHIR QuestionnaireItem.
        """
        qtype = self.qtype
        # Basics
        qitem_dict = {
            Fc.LINK_ID: self.qname,
            Fc.TEXT: self.qtext,
            Fc.TYPE: qtype.value,
        }

        # Extras for multiple-choice questions: what are the possible answers?
        if self.is_mcq:
            # Add permitted answers.
            options = []  # type: List[Dict]
            # We asserted mcq_qa earlier.
            for code, display in self.answer_options.items():
                options.append(
                    QuestionnaireItemAnswerOption(
                        jsondict={
                            Fc.VALUE_CODING: {
                                Fc.CODE: str(code),
                                Fc.DISPLAY: display,
                            }
                        }
                    ).as_json()
                )
            qitem_dict[Fc.ANSWER_OPTION] = options

        return QuestionnaireItem(jsondict=qitem_dict).as_json()

    # -------------------------------------------------------------------------
    # Concrete (instance)
    # -------------------------------------------------------------------------

    def _qr_item_answer(self) -> QuestionnaireResponseItemAnswer:
        """
        Returns a QuestionnaireResponseItemAnswer.
        """
        # Look things up
        raw_answer = self.answer
        answer_type = self.answer_type

        # Convert the value
        if raw_answer is None:
            # Deal with null values first, otherwise we will get
            # mis-conversion, e.g. str(None) == "None", bool(None) == False.
            fhir_answer = None
        elif answer_type == FHIRAnswerType.BOOLEAN:
            fhir_answer = bool(raw_answer)
        elif answer_type == FHIRAnswerType.DATE:
            fhir_answer = FHIRDate(
                format_datetime(raw_answer, DateFormat.FHIR_DATE)
            ).as_json()
        elif answer_type == FHIRAnswerType.DATETIME:
            fhir_answer = FHIRDate(raw_answer.isoformat()).as_json()
        elif answer_type == FHIRAnswerType.DECIMAL:
            fhir_answer = float(raw_answer)
        elif answer_type == FHIRAnswerType.INTEGER:
            fhir_answer = int(raw_answer)
        elif answer_type == FHIRAnswerType.QUANTITY:
            fhir_answer = Quantity(
                jsondict={
                    Fc.VALUE: float(raw_answer)
                    # More sophistication is possible -- units, for example.
                }
            ).as_json()
        elif answer_type == FHIRAnswerType.STRING:
            fhir_answer = str(raw_answer)
        elif answer_type == FHIRAnswerType.TIME:
            fhir_answer = FHIRDate(
                format_datetime(raw_answer, DateFormat.FHIR_TIME)
            ).as_json()
        elif answer_type == FHIRAnswerType.URI:
            fhir_answer = str(raw_answer)
        else:
            raise NotImplementedError(
                f"Don't know how to handle FHIR answer type {answer_type}"
            )

        # Build the FHIR object
        return QuestionnaireResponseItemAnswer(
            jsondict={answer_type.value: fhir_answer}
        )

    def questionnaire_response_item(self) -> Dict:
        """
        Returns a JSON/dict representation of a FHIR QuestionnaireResponseItem.
        """
        answer = self._qr_item_answer()
        return QuestionnaireResponseItem(
            jsondict={
                Fc.LINK_ID: self.qname,
                Fc.TEXT: self.qtext,  # question text
                Fc.ANSWER: [answer.as_json()],
                # Not supported yet: nesting, via "item".
            }
        ).as_json()
