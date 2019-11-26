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

import csv
import logging
import os
from typing import Dict, List, TYPE_CHECKING
from unittest import mock, TestCase

from asteval import Interpreter, make_symbol_table
from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
import pendulum
import redcap
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, Integer

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_exportrecipientinfo import ExportRecipientInfo
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
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


class RedcapExportException(Exception):
    pass


class RedcapExporter(object):
    INCOMPLETE = 0
    UNVERIFIED = 1
    COMPLETE = 2

    def __init__(self,
                 req: "CamcopsRequest",
                 api_url: str,
                 api_key: str) -> None:
        self.req = req

        # TODO: Catch RedcapError (eg invalid API Key)
        self.project = redcap.project.Project(api_url, api_key)

    def export_task(self, exported_task_redcap: "ExportedTaskRedcap") -> None:
        exported_task = exported_task_redcap.exported_task
        task = exported_task.task

        self.fieldmap_filename = self.get_task_fieldmap_filename(task)
        fieldmap = self.get_task_fieldmap(self.fieldmap_filename)

        instrument_name = fieldmap.pop("redcap_repeat_instrument", None)

        if instrument_name is None:
            raise RedcapExportException(
                (f"'redcap_repeat_instrument' is missing from "
                 f"{self.fieldmap_filename}")
            )

        which_idnum = exported_task.recipient.primary_idnum
        idnum_object = task.patient.get_idnum_object(which_idnum)
        redcap_record = self._get_existing_record(idnum_object)

        complete_status = self.INCOMPLETE

        if task.is_complete():
            complete_status = self.COMPLETE

        record = {
            "redcap_repeat_instrument": instrument_name,
            f"{instrument_name}_complete": complete_status,
        }

        self.add_task_fields_to_record(record, task, fieldmap)

        if redcap_record is None:
            return self._import_record(exported_task_redcap, record,
                                       idnum_object)

        return self._update_record(exported_task_redcap, record, redcap_record)

    def add_task_fields_to_record(self, record: Dict,
                                  task: "Task", fieldmap: Dict) -> None:
        extra_symbols = self.get_extra_symbols()

        symbol_table = make_symbol_table(
            task=task,
            **extra_symbols
        )
        interpreter = Interpreter(symtable=symbol_table)

        # TODO: Some safety checks here:
        #
        # Check redcap_field is in the data dictionary...
        #
        for redcap_field, formula in fieldmap.items():
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
        )

    def _import_record(self,
                       exported_task_redcap: "ExportedTaskRedcap",
                       record: Dict,
                       idnum_object: "PatientIdNum") -> None:
        # redcap_record_id will be ignored if force_auto_number is True
        # but has to be present
        record["record_id"] = 0

        # TODO: Catch RedcapError
        # Returns [redcap record id, 0]
        try:
            id_pair_list = self.project.import_records(
                [record],
                return_content="auto_ids", force_auto_number=True,
            )
        except redcap.RedcapError as e:
            raise RedcapExportException(str(e))

        id_pair = id_pair_list[0]

        redcap_record_id = int(id_pair.split(",")[0])
        log.info(f"Created new REDCap record {redcap_record_id}")
        redcap_record = RedcapRecord(
            redcap_record_id=redcap_record_id,
            which_idnum=idnum_object.which_idnum,
            idnum_value=idnum_object.idnum_value
        )
        self.req.dbsession.add(redcap_record)
        self.req.dbsession.commit()

        exported_task_redcap.redcap_record = redcap_record

        # TODO: Return some sort of meaningful status

    def _update_record(self,
                       exported_task_redcap: "ExportedTaskRedcap",
                       record: Dict,
                       redcap_record: "RedcapRecord") -> None:
        record["record_id"] = redcap_record.redcap_record_id

        # TODO: Catch RedcapError
        # Returns {'count': 1}
        self.project.import_records([record])
        log.info(f"Updated REDCap record {redcap_record.redcap_record_id}")

        exported_task_redcap.redcap_record = redcap_record

        # TODO: Return some sort of meaningful status

    def _get_existing_record(self, idnum_object: PatientIdNum) -> int:
        return (
            self.req.dbsession.query(RedcapRecord)
            .filter(RedcapRecord.which_idnum == idnum_object.which_idnum)
            .filter(RedcapRecord.idnum_value == idnum_object.idnum_value)
        ).first()

    def get_task_fieldmap(self, filename: str) -> Dict:
        # TODO: Optimise this

        # redcap field, formula
        fieldmap = {}

        try:
            with open(filename) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    fieldmap[row['redcap_field_name']] = row['formula']
        except FileNotFoundError:
            raise RedcapExportException(
                f"Unable to open fieldmap file '{filename}'"
            )

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
                                f"{task.tablename}.csv")

        return filename


class TestRedcapExporter(RedcapExporter):
    def __init__(self,
                 req: "CamcopsRequest") -> None:
        self.req = req
        self.project = mock.Mock()
        self.project.import_records = mock.Mock()


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

        super().setUp()

    def write_fieldmap(self) -> None:
        fieldmap = os.path.join(self.tmpdir_obj.name,
                                self.fieldmap_filename)

        with open(fieldmap, "w") as csvfile:
            writer = csv.writer(csvfile)

            rows = [
                ["redcap_field_name", "formula"],
            ] + self.fieldmap_rows

            for row in rows:
                writer.writerow(row)

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
        exporter.fieldmap_filename = "bmi.csv"

        task = mock.Mock(tablename="bmi")
        fieldmap = {"pa_height": "sys.platform"}

        record = {}

        with self.assertRaises(RedcapExportException) as cm:
            exporter.add_task_fields_to_record(record, task, fieldmap)

        message = str(cm.exception)
        self.assertIn("Error in formula 'sys.platform':", message)
        self.assertIn("bmi.csv", message)
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
