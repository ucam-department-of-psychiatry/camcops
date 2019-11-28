#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_redcap.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

**Implements communication with REDCap.**

(Thoughts from 2019-01-27, RNC.)

- For general information about REDCap, see https://www.project-redcap.org/.

- The API documentation seems not to be provided there, but is available from
  your local REDCap server. Pick a project. Choose "API" from the left-hand
  menu.

- In Python, we have PyCap (https://pycap.readthedocs.io/ or
  https://github.com/redcap-tools/PyCap). See also
  http://redcap-tools.github.io/projects/.

- There are also Python examples in the "API Examples" section of the API
  documentation. See, for example, ``import_records.py``.

*REDCap concepts*

- **Project:** the basic security grouping. Represents a research study.

- **Arms:** not an abbreviation. Groups study events into a sequence (an "arm"
  of a study). See
  https://labkey.med.ualberta.ca/labkey/wiki/REDCap%20Support/page.view?name=rcarms.

- **Instruments:** what we call tasks in CamCOPS. Data entry forms.

- **Metadata/data dictionary:** you can download all the fields used by the
  project.

- **REDCap Shared Library:** a collection of public instruments.

*My exploration*

- A "record" has lots of "instruments". The concept seems to be a "study
  visit". If you add three instruments to your project (e.g. a PHQ-9 from the
  Shared Library plus a couple of made-up things) then it will allow you to
  have all three instruments for Record 1.

- Each instrument can be marked complete/incomplete/unverified etc. There's a
  Record Status Dashboard showing these by record ID. Record ID is an integer,
  and its field name is ``record_id``. This is the first variable in the data
  dictionary.

- The standard PHQ-9 (at least, the most popular in the Shared Library) doesn't
  autocalculate its score ("Enter Total Score:")...

- If you import a task from the Shared Library twice, you get random fieldnames
  like this (see ``patient_health_questionnaire_9b``):

  .. code-block:: none

    Variable / Field Name	    Form Name
    record_id	                my_first_instrument
    name	                    my_first_instrument
    age	                        my_first_instrument
    ipsum	                    my_first_instrument
    v1	                        my_first_instrument
    v2	                        my_first_instrument
    v3	                        my_first_instrument
    v4	                        my_first_instrument
    phq9_date_enrolled	        patient_health_questionnaire_9
    phq9_first_name	            patient_health_questionnaire_9
    phq9_last_name	            patient_health_questionnaire_9
    phq9_1	                    patient_health_questionnaire_9
    phq9_2	                    patient_health_questionnaire_9
    phq9_3	                    patient_health_questionnaire_9
    phq9_4	                    patient_health_questionnaire_9
    phq9_5	                    patient_health_questionnaire_9
    phq9_6	                    patient_health_questionnaire_9
    phq9_7	                    patient_health_questionnaire_9
    phq9_8	                    patient_health_questionnaire_9
    phq9_9	                    patient_health_questionnaire_9
    phq9_total_score	        patient_health_questionnaire_9
    phq9_how_difficult	        patient_health_questionnaire_9
    phq9_date_enrolled_cdda47	patient_health_questionnaire_9b
    phq9_first_name_e31fec	    patient_health_questionnaire_9b
    phq9_last_name_cf0517	    patient_health_questionnaire_9b
    phq9_1_911f02	            patient_health_questionnaire_9b
    phq9_2_258760	            patient_health_questionnaire_9b
    phq9_3_931d98	            patient_health_questionnaire_9b
    phq9_4_8aa17a	            patient_health_questionnaire_9b
    phq9_5_efc4eb	            patient_health_questionnaire_9b
    phq9_6_7dc2c4	            patient_health_questionnaire_9b
    phq9_7_90821d	            patient_health_questionnaire_9b
    phq9_8_1e8954	            patient_health_questionnaire_9b
    phq9_9_9b8700	            patient_health_questionnaire_9b
    phq9_total_score_721d17	    patient_health_questionnaire_9b
    phq9_how_difficult_7c7fbd	patient_health_questionnaire_9b

*The REDCap API*

- The basic access method is a URL for a server/project plus a project-specific
  security token.

- Note that the API allows you to download the data dictionary.

*Other summaries*

- https://github.com/nutterb/redcapAPI/wiki/Importing-Data-to-REDCap is good.

*So, for an arbitrary CamCOPS-to-REDCap mapping, we'd need:*

#.  An export type of "redcap" with a definition including a URL and a project
    token.

#.  A configurable patient ID mapping, e.g. mapping CamCOPS forename to a
    REDCap field named ``forename``, CamCOPS ID number 7 to REDCap field
    ``my_study_id``, etc.

#.  Across all tasks, a configurable CamCOPS-to-REDCap field mapping
    (potentially incorporating value translation).

    - A specimen translation could contain the "default" instrument fieldnames,
      e.g. "phq9_1" etc. as above.

    - This mapping file should be separate from the patient ID mapping, as the
      user is quite likely to want to reuse the task mapping and alter the
      patient ID mapping for a different study.

    - UNCLEAR: how REDCap will cope with structured sub-data for tasks.

#.  A method for batching multiple CamCOPS tasks into the same REDCap record,
    e.g. "same day" (configurable?), for new uploads.

#.  Perhaps more tricky: a method for retrieving a matching record to add a
    new task to it.

"""

import logging
import os
import tempfile
from typing import Any, Dict, List, Tuple, TYPE_CHECKING
from unittest import mock, TestCase
import xml.etree.cElementTree as ET

from asteval import Interpreter, make_symbol_table
from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
import pendulum
import redcap
from sqlalchemy.sql.schema import Column, ForeignKey
from camcops_server.cc_modules.cc_sqla_coltypes import (
    ExportRecipientNameColType,
)
from sqlalchemy.sql.sqltypes import BigInteger, Integer

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_exportrecipientinfo import ExportRecipientInfo
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_sqla_coltypes import CamcopsColumn
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase

if TYPE_CHECKING:
    from configparser import ConfigParser
    from camcops_server.cc_modules.cc_exportmodels import ExportedTaskRedcap
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_task import Task


log = BraceStyleAdapter(logging.getLogger(__name__))


class RedcapRecord(Base):
    """
    Maps REDCap records to patients
    """
    __tablename__ = "_redcap_record"

    id = Column(
        "id", Integer, primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )

    redcap_record_id = Column(
        "redcap_record_id", Integer,
        comment="REDCap record ID"
    )

    which_idnum = Column(
        "which_idnum", Integer, ForeignKey(IdNumDefinition.which_idnum),
        nullable=False,
        comment="Which of the server's ID numbers is this?"
    )

    idnum_value = CamcopsColumn(
        "idnum_value", BigInteger,
        identifies_patient=True,
        comment="The value of the ID number"
    )

    recipient_name = Column(
        "recipient_name", ExportRecipientNameColType, nullable=False,
        comment="Name of export recipient"
    )

    next_instance_id = Column(
        "next_instance_id", Integer,
        comment="The instance ID for the next repeating records"
    )


class RedcapExportException(Exception):
    pass


class RedcapFieldmap(object):
    def __init__(self, *args, **kwargs):
        self.fieldmap = {}
        self.file_fieldmap = {}
        self.instrument_name = ""

    def init_from_file(self, filename: str):
        parser = ET.XMLParser(encoding="UTF-8")
        try:
            tree = ET.parse(filename, parser=parser)
        except FileNotFoundError:
            raise RedcapExportException(
                f"Unable to open fieldmap file '{filename}'"
            )
        except ET.ParseError:
            raise RedcapExportException(
                f"'instrument' is missing from {filename}"
            )

        root = tree.getroot()
        if root.tag != "instrument":
            raise RedcapExportException(
                (f"Expected the root tag to be 'instrument' instead of "
                 f"'{root.tag}' in {filename}")
            )

        self.instrument_name = root.get("name")

        fields = root.find("fields")

        for field in fields:
            self.fieldmap[field.get("name")] = field.get("formula")

        files = root.find("files") or []
        for file_field in files:
            self.file_fieldmap[file_field.get("name")] = file_field.get(
                "formula")


class RedcapExporter(object):
    def export_task(self,
                    req: "CamcopsRequest",
                    exported_task_redcap: "ExportedTaskRedcap") -> None:
        redcap_record, created = self._get_or_create_redcap_record(
            req, exported_task_redcap
        )

        if created:
            thing = RedcapImportyThing(req, exported_task_redcap, redcap_record)
        else:
            thing = RedcapUpdateyThing(req, exported_task_redcap, redcap_record)

        return thing.do_the_thing()

    def _get_or_create_redcap_record(
            self,
            req: "CamcopsRequest",
            exported_task_redcap: "ExportedTaskRedcap"
    ) -> Tuple[RedcapRecord, bool]:
        created = False

        exported_task = exported_task_redcap.exported_task

        which_idnum = exported_task.recipient.primary_idnum
        task = exported_task.task
        idnum_object = task.patient.get_idnum_object(which_idnum)
        recipient = exported_task.recipient

        record = (
            req.dbsession.query(RedcapRecord)
            .filter(RedcapRecord.which_idnum == idnum_object.which_idnum)
            .filter(RedcapRecord.idnum_value == idnum_object.idnum_value)
            .filter(RedcapRecord.recipient_name == recipient.recipient_name)
        ).first()

        if record is None:
            record = RedcapRecord(
                redcap_record_id=0,
                which_idnum=idnum_object.which_idnum,
                idnum_value=idnum_object.idnum_value,
                recipient_name=recipient.recipient_name,
                next_instance_id=2
            )

            created = True

        return record, created


# TODO: Better name
class RedcapThing(object):
    INCOMPLETE = 0
    UNVERIFIED = 1
    COMPLETE = 2

    def __init__(self,
                 req: "CamcopsRequest",
                 exported_task_redcap: "ExportedTaskRedcap",
                 redcap_record: RedcapRecord) -> None:
        self.req = req
        self.task = exported_task_redcap.exported_task.task
        self.redcap_record = redcap_record

        exported_task = self.exported_task
        recipient = exported_task.recipient

        try:
            self.project = redcap.project.Project(
                recipient.redcap_api_url, recipient.redcap_api_key
            )
        except redcap.RedcapError as e:
            raise RedcapExportException(str(e))

    def do_the_thing(self):
        complete_status = self.INCOMPLETE

        if self.task.is_complete():
            complete_status = self.COMPLETE
        self.fieldmap_filename = self.get_task_fieldmap_filename(self.task)

        fieldmap = self.get_task_fieldmap(self.fieldmap_filename)
        instrument_name = fieldmap.instrument_name

        record = {
            "record_id": self.redcap_record.redcap_record_id,
            "redcap_repeat_instrument": instrument_name,
            # REDCap won't create instance IDs automatically so we have to
            # assume no one else is writing to this record
            "redcap_repeat_instance": self.redcap_record.next_instance_id,
            f"{instrument_name}_complete": complete_status,
        }

        self.add_task_fields_to_record(record, self.task, fieldmap)

        try:
            response = self.project.import_records(
                [record],
                return_content=self.return_content,
                force_auto_number=self.force_auto_number
            )
        except redcap.RedcapError as e:
            raise RedcapExportException(str(e))

        self.save_redcap_record(response)

    def add_task_fields_to_record(self, record: Dict, task: "Task",
                                  fieldmap: RedcapFieldmap) -> None:
        extra_symbols = self.get_extra_symbols()

        symbol_table = make_symbol_table(
            task=task,
            **extra_symbols
        )
        interpreter = Interpreter(symtable=symbol_table)

        for redcap_field, formula in fieldmap.fieldmap.items():
            v = interpreter(f"{formula}", show_errors=True)
            if interpreter.error:
                message = "\n".join([e.msg for e in interpreter.error])
                raise RedcapExportException(
                    (
                        f"Fieldmap '{self.fieldmap_filename}':\n"
                        f"Error in formula '{formula}': {message}"
                    )
                )
            record[redcap_field] = v

    def get_extra_symbols(self):
        return dict(
            format_datetime=format_datetime,
            DateFormat=DateFormat,
            request=self.req
        )

    def save_redcap_record(self, response: Any):
        next_instance_id = self.redcap_record.next_instance_id + 1
        self.redcap_record.next_instance_id = next_instance_id
        self.req.dbsession.add(self.redcap_record)
        self.req.dbsession.commit()

        self.exported_task_redcap.redcap_record = self.redcap_record

    def get_task_fieldmap(self, filename: str) -> Dict:
        fieldmap = RedcapFieldmap()
        fieldmap.init_from_file(filename)

        return fieldmap

    def get_task_fieldmap_filename(self, task: "Task") -> str:
        fieldmap_dir = self.req.config.redcap_fieldmaps
        if fieldmap_dir is None:
            raise RedcapExportException(
                "REDCAP_FIELDMAPS is not set in the config file"
            )

        if fieldmap_dir == "":
            raise RedcapExportException(
                "REDCAP_FIELDMAPS is empty in the config file"
            )

        filename = os.path.join(fieldmap_dir,
                                f"{task.tablename}.xml")

        return filename


# TODO: Better name
class RedcapImportyThing(RedcapThing):
    force_auto_number = True
    # Returns [redcap record id, 0]
    return_content = "auto_ids"

    def save_redcap_record(self, response: List[str]):
        id_pair = response[0]

        redcap_record_id = int(id_pair.split(",")[0])
        log.info(f"Created new REDCap record {redcap_record_id}")

        self.redcap_record.redcap_record_id = redcap_record_id

        super().save_redcap_record(response)


# TODO: Better name
class RedcapUpdateyThing(RedcapThing):
    force_auto_number = False
    # Returns {'count': 1}
    return_content = "count"

    def save_redcap_record(self, response: Any):
        log.info(f"Updated REDCap record {self.redcap_record.redcap_record_id}")
        super().save_redcap_record(response)


class TestRedcapExporter(RedcapImportyThing):
    def __init__(self,
                 req: "CamcopsRequest") -> None:
        self.req = req
        self.project = mock.Mock()
        self.project.import_records = mock.Mock()
        self.project.import_file = mock.Mock()


class RedcapExportTestCase(DemoDatabaseTestCase):
    fieldmap_filename = None

    def override_config_settings(self, parser: "ConfigParser"):
        parser.set("site", "REDCAP_FIELDMAPS", self.tmpdir_obj.name)

    def setUp(self) -> None:
        if self.fieldmap_filename is not None:
            self.write_fieldmap()

        recipientinfo = ExportRecipientInfo()

        self.recipient = ExportRecipient(recipientinfo)
        self.recipient.primary_idnum = 1001

        # auto increment doesn't work for BigInteger with SQLite
        self.recipient.id = 1
        self.recipient.recipient_name = "test"

        super().setUp()

    def write_fieldmap(self) -> None:
        fieldmap = os.path.join(self.tmpdir_obj.name,
                                self.fieldmap_filename)

        with open(fieldmap, "w") as f:
            f.write(self.fieldmap_xml)

    @property
    def fieldmap_rows(self) -> List[List[str]]:
        raise NotImplementedError("You must define fieldmap_rows property")

    def create_patient_with_idnum_1001(self) -> None:
        from camcops_server.cc_modules.cc_patient import Patient
        from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
        patient = Patient()
        patient.id = 2
        self._apply_standard_db_fields(patient)
        patient.forename = "Forename2"
        patient.surname = "Surname2"
        patient.dob = pendulum.parse("1975-12-12")
        self.dbsession.add(patient)
        patient_idnum1 = PatientIdNum()
        patient_idnum1.id = 3
        self._apply_standard_db_fields(patient_idnum1)
        patient_idnum1.patient_id = patient.id
        patient_idnum1.which_idnum = 1001
        patient_idnum1.idnum_value = 555
        self.dbsession.add(patient_idnum1)
        self.dbsession.commit()

        return patient


class RedcapExportErrorTests(TestCase):
    def test_raises_when_fieldmap_has_unknown_symbols(self):
        exporter = TestRedcapExporter(None)
        exporter.fieldmap_filename = "bmi.xml"

        task = mock.Mock(tablename="bmi")
        fieldmap = RedcapFieldmap()
        fieldmap.fieldmap = {"pa_height": "sys.platform"}

        record = {}

        with self.assertRaises(RedcapExportException) as cm:
            exporter.add_task_fields_to_record(record, task, fieldmap)

        message = str(cm.exception)
        self.assertIn("Error in formula 'sys.platform':", message)
        self.assertIn("bmi.xml", message)
        self.assertIn("'sys' is not defined", message)

    def test_raises_when_fieldmap_missing_from_config(self):
        config = mock.Mock(redcap_fieldmaps="")
        request = mock.Mock(config=config)
        task = mock.Mock()

        exporter = TestRedcapExporter(request)
        with self.assertRaises(RedcapExportException) as cm:
            exporter.get_task_fieldmap_filename(task)

        message = str(cm.exception)
        self.assertIn("REDCAP_FIELDMAPS is empty in the config file", message)

    def test_raises_when_error_from_redcap_on_import(self):
        req = mock.Mock()
        exporter = TestRedcapExporter(req)
        exporter.project.import_records.side_effect = redcap.RedcapError(
            "Something went wrong"
        )

        exporter.task = mock.Mock()
        exporter.task.is_complete = mock.Mock(return_value=True)

        with self.assertRaises(RedcapExportException) as cm:
            exporter.do_the_thing()
        message = str(cm.exception)

        self.assertIn("Something went wrong", message)

    def test_raises_when_error_from_redcap_on_init(self):
        with mock.patch("redcap.project.Project.__init__") as mock_init:
            mock_init.side_effect = redcap.RedcapError(
                "Something went wrong"
            )

            with self.assertRaises(RedcapExportException) as cm:
                req = mock.Mock()
                api_url = api_key = ""
                RedcapExporter(req, api_url, api_key)

            message = str(cm.exception)

            self.assertIn("Something went wrong", message)


class RedcapFieldmapTests(TestCase):
    def test_raises_when_xml_file_missing(self) -> None:
        fieldmap = RedcapFieldmap()
        with self.assertRaises(RedcapExportException) as cm:
            fieldmap.init_from_file("/does/not/exist/bmi.xml")

        message = str(cm.exception)

        self.assertIn("Unable to open fieldmap file", message)
        self.assertIn("bmi.xml", message)

    def test_raises_when_instrument_missing(self):
        with tempfile.NamedTemporaryFile(
                mode="w", suffix="xml") as fieldmap_file:
            fieldmap_file.write("""<?xml version="1.0" encoding="UTF-8"?>
<someothertag></someothertag>
""")
            fieldmap_file.flush()

            fieldmap = RedcapFieldmap()

            with self.assertRaises(RedcapExportException) as cm:
                fieldmap.init_from_file(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn(("Expected the root tag to be 'instrument' instead of "
                       "'someothertag'"), message)
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_root_tag_missing(self):
        with tempfile.NamedTemporaryFile(
                mode="w", suffix="xml") as fieldmap_file:
            fieldmap_file.write("""<?xml version="1.0" encoding="UTF-8"?>
""")
            fieldmap_file.flush()

            fieldmap = RedcapFieldmap()

            with self.assertRaises(RedcapExportException) as cm:
                fieldmap.init_from_file(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn("'instrument' is missing from", message)
        self.assertIn(fieldmap_file.name, message)
