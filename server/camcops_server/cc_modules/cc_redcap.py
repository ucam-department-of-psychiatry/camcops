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
  menu. Follow the "REDCap API documentation" link.

- In Python, we have PyCap (https://pycap.readthedocs.io/ or
  https://github.com/redcap-tools/PyCap). See also
  http://redcap-tools.github.io/projects/. This is no longer being actively
  developed.

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

from enum import Enum
import io
import logging
import os
import tempfile
from typing import Any, Dict, Generator, List, Tuple, TYPE_CHECKING
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
    TableNameColType,
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
        comment="ID of the record on REDCap"
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


class RedcapNextInstance(Base):
    """
    For each task/instrument in a REDCap record, holds the instance
    ID to be used for the next upload.

    Unfortunately REDCap won't create these automatically
    https://community.projectredcap.org/questions/74561/unexpected-behaviour-with-import-records-repeat-in.html

    """  # noqa
    __tablename__ = "_redcap_next_instance"

    id = Column(
        "id", Integer, primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )

    task_table_name = Column(
        "task_table_name", TableNameColType,
        index=True,
        comment="Table name of the task's base table"
    )

    redcap_record_pk = Column(
        "redcap_record_pk", Integer, ForeignKey(RedcapRecord.id),
        nullable=False,
        comment="Primary key of associated RedcapRecord"
    )

    next_instance_id = Column(
        "next_instance_id", Integer,
        comment="The instance ID for the next repeating records"
    )


class RedcapExportException(Exception):
    pass


class RedcapFieldmap(object):
    """
    Internal representation of the fieldmap XML file.
    This describes how the task fields should be translated to
    the REDCap record.
    """

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


class RedcapTaskExporter(object):
    """
    Main entry point for task export to REDCap. Keeps a record of what
    has been exported already and initiates upload, determining whether a
    record should be created or updated
    """
    def export_task(self,
                    req: "CamcopsRequest",
                    exported_task_redcap: "ExportedTaskRedcap") -> None:
        redcap_record, created = self._get_or_create_redcap_record(
            req, exported_task_redcap
        )
        exported_task = exported_task_redcap.exported_task
        recipient = exported_task.recipient

        project = self.get_project(recipient)

        uploader_class = RedcapNewRecordUploader
        if not created:
            uploader_class = RedcapUpdatedRecordUploader

        task = exported_task.task
        uploader = uploader_class(req, project)

        next_instance, _ = self._get_or_create_next_instance(
            req, task, redcap_record
        )

        new_redcap_record_id = uploader.upload(
            task, redcap_record.redcap_record_id,
            next_instance.next_instance_id
        )

        self._save_redcap_record(req, redcap_record, new_redcap_record_id)
        self._save_next_instance(req, next_instance, redcap_record)

        exported_task_redcap.redcap_record = redcap_record

    def get_project(self, recipient: ExportRecipient):
        try:
            project = redcap.project.Project(
                recipient.redcap_api_url, recipient.redcap_api_key
            )
        except redcap.RedcapError as e:
            raise RedcapExportException(str(e))

        return project

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
                recipient_name=recipient.recipient_name
            )

            created = True

        return record, created

    def _get_or_create_next_instance(
            self,
            req: "CamcopsRequest",
            task: "Task",
            redcap_record: RedcapRecord) -> Tuple[RedcapNextInstance, bool]:
        created = False

        next_instance = (
            req.dbsession.query(RedcapNextInstance)
            .filter(RedcapNextInstance.task_table_name == task.tablename)
            .filter(RedcapNextInstance.redcap_record_pk == redcap_record.id)
        ).first()

        if next_instance is None:
            next_instance = RedcapNextInstance(
                task_table_name=task.tablename,
                redcap_record_pk=redcap_record.id,
                next_instance_id=1
            )

            created = True

        return next_instance, created

    def _save_redcap_record(self,
                            req: "CamcopsRequest",
                            redcap_record: RedcapRecord,
                            redcap_record_id: int) -> None:
        redcap_record.redcap_record_id = redcap_record_id
        req.dbsession.add(redcap_record)
        req.dbsession.commit()

    def _save_next_instance(self,
                            req: "CamcopsRequest",
                            next_instance: RedcapNextInstance,
                            redcap_record: RedcapRecord) -> None:
        next_instance.next_instance_id = next_instance.next_instance_id + 1
        next_instance.redcap_record_pk = redcap_record.id

        req.dbsession.add(next_instance)
        req.dbsession.commit()


class RedcapRecordStatus(Enum):
    """
    Corresponds to valid values of Form Status -> Complete? field in REDCap
    """
    INCOMPLETE = 0
    UNVERIFIED = 1
    COMPLETE = 2


class RedcapUploader(object):
    """
    Uploads records and files into REDCap, transforming the fields via the
    fieldmap XML file.

    Knows nothing about RedcapRecord, ExportedTaskRedcap, ExportedTask
    ExportRecipient
    """
    def __init__(self,
                 req: "CamcopsRequest",
                 project: "redcap.project.Project") -> None:
        self.req = req
        self.project = project

    def upload(self, task: "Task", redcap_record_id: int,
               next_instance_id: int):
        complete_status = RedcapRecordStatus.INCOMPLETE

        if task.is_complete():
            complete_status = RedcapRecordStatus.COMPLETE
        fieldmap = self.get_task_fieldmap(task)
        instrument_name = fieldmap.instrument_name

        repeat_instance = next_instance_id

        record = {
            "record_id": redcap_record_id,
            "redcap_repeat_instrument": instrument_name,
            # https://community.projectredcap.org/questions/74561/unexpected-behaviour-with-import-records-repeat-in.html  # noqa
            # REDCap won't create instance IDs automatically so we have to
            # assume no one else is writing to this record
            "redcap_repeat_instance": repeat_instance,
            f"{instrument_name}_complete": complete_status.value,
        }

        self.transform_fields(record, task, fieldmap.fieldmap)

        response = self.upload_record(record)
        new_redcap_record_id = self.get_new_redcap_record_id(redcap_record_id,
                                                             response)

        file_dict = {}
        self.transform_fields(file_dict, task, fieldmap.file_fieldmap)

        self.upload_files(task,
                          new_redcap_record_id,
                          repeat_instance,
                          file_dict)

        self.log_success(new_redcap_record_id)

        return new_redcap_record_id

    def upload_record(self, record: Dict) -> Any:
        try:
            response = self.project.import_records(
                [record],
                return_content=self.return_content,
                force_auto_number=self.force_auto_number
            )
        except redcap.RedcapError as e:
            raise RedcapExportException(str(e))

        return response

    def upload_files(self, task: "Task", record_id: int, repeat_instance: int,
                     file_dict: Dict):
        for fieldname, value in file_dict.items():
            with io.BytesIO(value) as file_obj:
                filename = f"{task.tablename}_{record_id}_{fieldname}"

                try:
                    self.project.import_file(
                        record_id, fieldname, filename, file_obj,
                        repeat_instance=repeat_instance
                    )
                # ValueError if the field does not exist or is not
                # a file field
                except (redcap.RedcapError, ValueError) as e:
                    raise RedcapExportException(str(e))

    def transform_fields(self, field_dict: Dict, task: "Task",
                         fieldmap: Dict) -> None:
        extra_symbols = self.get_extra_symbols()

        symbol_table = make_symbol_table(
            task=task,
            **extra_symbols
        )
        interpreter = Interpreter(symtable=symbol_table)

        for redcap_field, formula in fieldmap.items():
            v = interpreter(f"{formula}", show_errors=True)
            if interpreter.error:
                message = "\n".join([e.msg for e in interpreter.error])
                raise RedcapExportException(
                    (
                        f"Fieldmap '{self.get_task_fieldmap_filename(task)}':\n"
                        f"Error in formula '{formula}': {message}"
                    )
                )
            field_dict[redcap_field] = v

    def get_extra_symbols(self):
        return dict(
            format_datetime=format_datetime,
            DateFormat=DateFormat,
            request=self.req
        )

    def get_task_fieldmap(self, task: "Task") -> Dict:
        fieldmap = RedcapFieldmap()
        fieldmap.init_from_file(self.get_task_fieldmap_filename(task))

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


class RedcapNewRecordUploader(RedcapUploader):
    force_auto_number = True
    # import_records returns ["<redcap record id>, 0"]
    return_content = "auto_ids"

    def get_new_redcap_record_id(self, redcap_record_id: int,
                                 response: List[str]):
        id_pair = response[0]

        redcap_record_id = int(id_pair.split(",")[0])

        return redcap_record_id

    def log_success(self, redcap_record_id: int):
        log.info(f"Created new REDCap record {redcap_record_id}")


class RedcapUpdatedRecordUploader(RedcapUploader):
    force_auto_number = False
    # import_records returns {'count': 1}
    return_content = "count"

    def get_new_redcap_record_id(self, old_redcap_record_id: int,
                                 response: Any):
        return old_redcap_record_id

    def log_success(self, redcap_record_id: int):
        log.info(f"Updated REDCap record {redcap_record_id}")


# =============================================================================
# Unit testing
# =============================================================================

class MockProject(mock.Mock):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.import_records = mock.Mock()
        self.import_file = mock.Mock()


class MockRedcapTaskExporter(RedcapTaskExporter):
    def __init__(self) -> None:
        mock_project = MockProject()
        self.get_project = mock.Mock(return_value=mock_project)

        config = mock.Mock()
        self.req = mock.Mock(config=config)


class MockRedcapNewRecordUploader(RedcapNewRecordUploader):
    def __init__(self) -> None:
        self.req = mock.Mock()
        self.project = MockProject()
        self.task = mock.Mock(tablename="mock_task")


class RedcapExportErrorTests(TestCase):
    def test_raises_when_fieldmap_has_unknown_symbols(self) -> None:
        exporter = MockRedcapNewRecordUploader()
        exporter.req.config.redcap_fieldmaps = "/some/path/fieldmaps"

        task = mock.Mock(tablename="bmi")
        fieldmap = {"pa_height": "sys.platform"}

        field_dict = {}

        with self.assertRaises(RedcapExportException) as cm:
            exporter.transform_fields(field_dict, task, fieldmap)

        message = str(cm.exception)
        self.assertIn("Error in formula 'sys.platform':", message)
        self.assertIn("bmi.xml", message)
        self.assertIn("'sys' is not defined", message)

    def test_raises_when_fieldmap_missing_from_config(self) -> None:

        exporter = MockRedcapNewRecordUploader()
        exporter.req.config.redcap_fieldmaps = ""
        task = mock.Mock()
        with self.assertRaises(RedcapExportException) as cm:
            exporter.get_task_fieldmap_filename(task)

        message = str(cm.exception)
        self.assertIn("REDCAP_FIELDMAPS is empty in the config file", message)

    def test_raises_when_error_from_redcap_on_import(self) -> None:
        exporter = MockRedcapNewRecordUploader()
        exporter.project.import_records.side_effect = redcap.RedcapError(
            "Something went wrong"
        )

        with self.assertRaises(RedcapExportException) as cm:
            record = {}
            exporter.upload_record(record)
        message = str(cm.exception)

        self.assertIn("Something went wrong", message)

    def test_raises_when_error_from_redcap_on_init(self) -> None:
        with mock.patch("redcap.project.Project.__init__") as mock_init:
            mock_init.side_effect = redcap.RedcapError(
                "Something went wrong"
            )

            with self.assertRaises(RedcapExportException) as cm:
                exporter = RedcapTaskExporter()
                recipient = mock.Mock()
                exporter.get_project(recipient)

            message = str(cm.exception)

            self.assertIn("Something went wrong", message)

    def test_raises_when_field_not_a_file_field(self) -> None:
        exporter = MockRedcapNewRecordUploader()
        exporter.project.import_file.side_effect = ValueError(
            "Error with file field"
        )

        task = mock.Mock()

        with self.assertRaises(RedcapExportException) as cm:
            record_id = 1
            repeat_instance = 1
            file_dict = {"medication_items": b"not a real file"}
            exporter.upload_files(task, record_id, repeat_instance, file_dict)
        message = str(cm.exception)

        self.assertIn("Error with file field", message)

    def test_raises_when_error_from_redcap_on_import_file(self) -> None:
        exporter = MockRedcapNewRecordUploader()
        exporter.project.import_file.side_effect = redcap.RedcapError(
            "Something went wrong"
        )

        task = mock.Mock()

        with self.assertRaises(RedcapExportException) as cm:
            record_id = 1
            repeat_instance = 1
            file_dict = {"medication_items": b"not a real file"}
            exporter.upload_files(task, record_id, repeat_instance, file_dict)
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


# =============================================================================
# Integration testing
# =============================================================================

class RedcapExportTestCase(DemoDatabaseTestCase):
    fieldmaps = {}

    def get_next_instance(
            self,
            exported_task_redcap: "ExportedTaskRedcap") -> RedcapNextInstance:

        task = exported_task_redcap.exported_task.task
        redcap_record = exported_task_redcap.redcap_record

        next_instance = (
            self.req.dbsession.query(RedcapNextInstance)
            .filter(RedcapNextInstance.task_table_name == task.tablename)
            .filter(RedcapNextInstance.redcap_record_pk == redcap_record.id)
        ).first()

        self.assertIsNotNone(next_instance)

        return next_instance

    def override_config_settings(self, parser: "ConfigParser"):
        parser.set("site", "REDCAP_FIELDMAPS", self.tmpdir_obj.name)

    def setUp(self) -> None:
        self.write_fieldmaps()

        recipientinfo = ExportRecipientInfo()

        self.recipient = ExportRecipient(recipientinfo)
        self.recipient.primary_idnum = 1001

        # auto increment doesn't work for BigInteger with SQLite
        self.recipient.id = 1
        self.recipient.recipient_name = "test"

        super().setUp()

    def write_fieldmaps(self) -> None:
        for filename, xml in self.fieldmaps.items():
            fieldmap = os.path.join(self.tmpdir_obj.name,
                                    filename)

            with open(fieldmap, "w") as f:
                f.write(xml)

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


class BmiRedcapExportTestCase(RedcapExportTestCase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id_sequence = self.get_id()

    @staticmethod
    def get_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1


class BmiRedcapValidFieldmapTestCase(BmiRedcapExportTestCase):
    fieldmaps = {"bmi.xml": """<?xml version="1.0" encoding="UTF-8"?>
<instrument name="bmi">
  <fields>
    <field name="pa_height" formula="format(task.height_m, '.1f')" />
    <field name="pa_weight" formula="format(task.mass_kg, '.1f')" />
    <field name="bmi_date" formula="format_datetime(task.when_created, DateFormat.ISO8601_DATE_ONLY)" />
  </fields>
</instrument>"""}  # noqa: E501


class BmiRedcapExportTests(BmiRedcapValidFieldmapTestCase):
    """
    These are more of a test of the fieldmap code than anything
    related to the BMI task
    """

    def create_tasks(self) -> None:
        from camcops_server.tasks.bmi import Bmi

        patient = self.create_patient_with_idnum_1001()
        self.task = Bmi()
        self.apply_standard_task_fields(self.task)
        self.task.id = next(self.id_sequence)
        self.task.height_m = 1.83
        self.task.mass_kg = 67.57
        self.task.patient_id = patient.id
        self.dbsession.add(self.task)
        self.dbsession.commit()

    def test_record_exported(self) -> None:
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTask,
            ExportedTaskRedcap
        )

        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()
        project.import_records.return_value = ["123,0"]
        exporter.export_task(self.req, exported_task_redcap)
        self.assertEquals(exported_task_redcap.redcap_record.redcap_record_id,
                          123)

        args, kwargs = project.import_records.call_args

        rows = args[0]
        record = rows[0]

        self.assertEquals(record["redcap_repeat_instrument"], "bmi")
        self.assertEquals(record["redcap_repeat_instance"], 1)
        self.assertEquals(record["record_id"], 0)
        self.assertEquals(record["bmi_complete"],
                          RedcapRecordStatus.COMPLETE.value)
        self.assertEquals(record["bmi_date"], "2010-07-07")

        self.assertEquals(record["pa_height"], "1.8")
        self.assertEquals(record["pa_weight"], "67.6")

        self.assertEquals(kwargs["return_content"], "auto_ids")
        self.assertTrue(kwargs["force_auto_number"])

    def test_matching_redcap_id_from_other_recipient_ignored(self) -> None:
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTask,
            ExportedTaskRedcap
        )
        from camcops_server.cc_modules.cc_exportrecipient import (
            ExportRecipient
        )
        from camcops_server.cc_modules.cc_exportrecipientinfo import (
            ExportRecipientInfo
        )

        other_recipientinfo = ExportRecipientInfo()
        other_recipientinfo.recipient_name = "test2"
        other_recipient = ExportRecipient(other_recipientinfo)
        other_recipient.primary_idnum = self.recipient.primary_idnum
        # auto increment doesn't work for BigInteger with SQLite
        other_recipient.id = 2

        self.dbsession.add(other_recipient)
        self.dbsession.commit()

        # Create an existing record for the same patient but for a different
        # REDCap instance (different export recipient)
        redcap_record = RedcapRecord(
            redcap_record_id=123, which_idnum=1001,
            idnum_value=555,
            recipient_name=other_recipient.recipient_name)
        self.dbsession.add(redcap_record)
        self.dbsession.commit()

        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()
        project.import_records.return_value = ["456,0"]
        exporter.export_task(self.req, exported_task_redcap)

        # Would be 123 if the existing record was not ignored
        self.assertEquals(exported_task_redcap.redcap_record.redcap_record_id,
                          456)

        next_instance = self.get_next_instance(exported_task_redcap)
        self.assertEquals(next_instance.next_instance_id, 2)


class BmiRedcapUpdateTests(BmiRedcapValidFieldmapTestCase):
    def create_tasks(self) -> None:
        from camcops_server.tasks.bmi import Bmi
        patient = self.create_patient_with_idnum_1001()
        self.task1 = Bmi()
        self.apply_standard_task_fields(self.task1)
        self.task1.id = next(self.id_sequence)
        self.task1.height_m = 1.83
        self.task1.mass_kg = 67.57
        self.task1.patient_id = patient.id
        self.dbsession.add(self.task1)

        self.task2 = Bmi()
        self.apply_standard_task_fields(self.task2)
        self.task2.id = next(self.id_sequence)
        self.task2.height_m = 1.83
        self.task2.mass_kg = 68.5
        self.task2.patient_id = patient.id
        self.dbsession.add(self.task2)
        self.dbsession.commit()

    def test_existing_record_id_used_for_update(self) -> None:
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTask,
            ExportedTaskRedcap,
        )

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()
        project.import_records.return_value = ["123,0"]

        exported_task1 = ExportedTask(task=self.task1, recipient=self.recipient)
        exported_task_redcap1 = ExportedTaskRedcap(exported_task1)
        exporter.export_task(self.req, exported_task_redcap1)
        self.assertEquals(exported_task_redcap1.redcap_record.redcap_record_id,
                          123)

        exported_task2 = ExportedTask(task=self.task2, recipient=self.recipient)
        exported_task_redcap2 = ExportedTaskRedcap(exported_task2)

        exporter.export_task(self.req, exported_task_redcap2)
        args, kwargs = project.import_records.call_args

        rows = args[0]
        record = rows[0]

        self.assertEquals(record["record_id"], 123)
        self.assertEquals(record["redcap_repeat_instance"], 2)

        next_instance = self.get_next_instance(exported_task_redcap2)

        self.assertEquals(next_instance.next_instance_id, 3)


class Phq9RedcapExportTests(RedcapExportTestCase):
    """
    These are more of a test of the fieldmap code than anything
    related to the PHQ9 task
    """
    fieldmaps = {"phq9.xml": """<?xml version="1.0" encoding="UTF-8"?>
<instrument name="patient_health_questionnaire_9">
  <fields>
        <field name="phq9_how_difficult" formula="task.q10 + 1" />
        <field name="phq9_total_score" formula="task.total_score()" />
        <field name="phq9_first_name" formula="task.patient.forename" />
        <field name="phq9_last_name" formula="task.patient.surname" />
        <field name="phq9_date_enrolled" formula="format_datetime(task.when_created,DateFormat.ISO8601_DATE_ONLY)" />
        <field name="phq9_1" formula="task.q1" />
        <field name="phq9_2" formula="task.q2" />
        <field name="phq9_3" formula="task.q3" />
        <field name="phq9_4" formula="task.q4" />
        <field name="phq9_5" formula="task.q5" />
        <field name="phq9_6" formula="task.q6" />
        <field name="phq9_7" formula="task.q7" />
        <field name="phq9_8" formula="task.q8" />
        <field name="phq9_9" formula="task.q9" />
  </fields>
</instrument>"""}  # noqa: E501

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id_sequence = self.get_id()

    @staticmethod
    def get_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1

    def create_tasks(self) -> None:
        from camcops_server.tasks.phq9 import Phq9
        patient = self.create_patient_with_idnum_1001()
        self.task = Phq9()
        self.apply_standard_task_fields(self.task)
        self.task.id = next(self.id_sequence)
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
        self.task.patient_id = patient.id
        self.dbsession.add(self.task)
        self.dbsession.commit()

    def test_record_exported(self) -> None:
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTask,
            ExportedTaskRedcap,
        )

        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()
        project.import_records.return_value = ["123,0"]
        exporter.export_task(self.req, exported_task_redcap)
        self.assertEquals(exported_task_redcap.redcap_record.redcap_record_id,
                          123)

        args, kwargs = project.import_records.call_args

        rows = args[0]
        record = rows[0]

        self.assertEquals(record["redcap_repeat_instrument"],
                          "patient_health_questionnaire_9")
        self.assertEquals(record["record_id"], 0)
        self.assertEquals(record["patient_health_questionnaire_9_complete"],
                          RedcapRecordStatus.COMPLETE.value)
        self.assertEquals(record["phq9_how_difficult"], 4)
        self.assertEquals(record["phq9_total_score"], 12)
        self.assertEquals(record["phq9_first_name"], "Forename2")
        self.assertEquals(record["phq9_last_name"], "Surname2")
        self.assertEquals(record["phq9_date_enrolled"], "2010-07-07")

        self.assertEquals(record["phq9_1"], 0)
        self.assertEquals(record["phq9_2"], 1)
        self.assertEquals(record["phq9_3"], 2)
        self.assertEquals(record["phq9_4"], 3)
        self.assertEquals(record["phq9_5"], 0)
        self.assertEquals(record["phq9_6"], 1)
        self.assertEquals(record["phq9_7"], 2)
        self.assertEquals(record["phq9_8"], 3)
        self.assertEquals(record["phq9_9"], 0)

        self.assertEquals(kwargs["return_content"], "auto_ids")
        self.assertTrue(kwargs["force_auto_number"])


class MedicationTherapyRedcapExportTests(RedcapExportTestCase):
    """
    These are more of a test of the file upload code than anything
    related to the KhandakerMojoMedicationTherapy task
    """
    fieldmaps = {
        "khandaker_mojo_medicationtherapy.xml": """<?xml version="1.0" encoding="UTF-8"?>
<instrument name="medication_table">
  <fields>
  </fields>
  <files>
    <field name="medtbl_medication_items" formula="task.get_pdf(request)" />
  </files>
</instrument>"""}  # noqa: E501

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id_sequence = self.get_id()

    @staticmethod
    def get_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1

    def create_tasks(self) -> None:
        from camcops_server.tasks.khandaker_mojo_medicationtherapy import (
            KhandakerMojoMedicationTherapy,
        )

        patient = self.create_patient_with_idnum_1001()
        self.task = KhandakerMojoMedicationTherapy()
        self.apply_standard_task_fields(self.task)
        self.task.id = next(self.id_sequence)
        self.task.patient_id = patient.id
        self.dbsession.add(self.task)
        self.dbsession.commit()

    def test_record_exported(self) -> None:
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTask,
            ExportedTaskRedcap
        )

        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()
        project.import_records.return_value = ["123,0"]

        # We can't just look at the call_args here because the file will already
        # have been closed by then
        def read_pdf_bytes(*args, **kwargs):
            file_obj = args[3]
            read_pdf_bytes.pdf_header = file_obj.read(5)

        project.import_file.side_effect = read_pdf_bytes

        exporter.export_task(self.req, exported_task_redcap)
        self.assertEquals(exported_task_redcap.redcap_record.redcap_record_id,
                          123)

        args, kwargs = project.import_file.call_args

        record_id = args[0]
        fieldname = args[1]
        filename = args[2]

        self.assertEquals(record_id, 123)
        self.assertEquals(fieldname, "medtbl_medication_items")
        self.assertEquals(
            filename,
            "khandaker_mojo_medicationtherapy_123_medtbl_medication_items"
        )

        self.assertEquals(kwargs["repeat_instance"], 1)
        self.assertEquals(read_pdf_bytes.pdf_header, b"%PDF-")


class MultipleTaskRedcapExportTests(RedcapExportTestCase):
    fieldmaps = {
"bmi.xml": """<?xml version="1.0" encoding="UTF-8"?>
<instrument name="bmi">
  <fields>
    <field name="pa_height" formula="format(task.height_m, '.1f')" />
    <field name="pa_weight" formula="format(task.mass_kg, '.1f')" />
    <field name="bmi_date" formula="format_datetime(task.when_created, DateFormat.ISO8601_DATE_ONLY)" />
  </fields>
</instrument>""",  # noqa: E501
"khandaker_mojo_medicationtherapy.xml": """<?xml version="1.0" encoding="UTF-8"?>
<instrument name="medication_table">
  <fields>
  </fields>
  <files>
    <field name="medtbl_medication_items" formula="task.get_pdf(request)" />
  </files>
</instrument>"""}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id_sequence = self.get_id()

    @staticmethod
    def get_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1

    def create_tasks(self) -> None:
        from camcops_server.tasks.khandaker_mojo_medicationtherapy import (
            KhandakerMojoMedicationTherapy,
        )

        patient = self.create_patient_with_idnum_1001()
        self.task1 = KhandakerMojoMedicationTherapy()
        self.apply_standard_task_fields(self.task1)
        self.task1.id = next(self.id_sequence)
        self.task1.patient_id = patient.id
        self.dbsession.add(self.task1)
        self.dbsession.commit()

        from camcops_server.tasks.bmi import Bmi
        self.task2 = Bmi()
        self.apply_standard_task_fields(self.task2)
        self.task2.id = next(self.id_sequence)
        self.task2.height_m = 1.83
        self.task2.mass_kg = 67.57
        self.task2.patient_id = patient.id
        self.dbsession.add(self.task2)
        self.dbsession.commit()

    def test_instance_ids_on_different_tasks_in_same_record(self) -> None:
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTask,
            ExportedTaskRedcap,
        )
        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()
        project.import_records.return_value = ["123,0"]

        exported_task1 = ExportedTask(task=self.task1, recipient=self.recipient)
        exported_task_redcap1 = ExportedTaskRedcap(exported_task1)
        exporter.export_task(self.req, exported_task_redcap1)
        self.assertEquals(exported_task_redcap1.redcap_record.redcap_record_id,
                          123)
        args, kwargs = project.import_file.call_args

        self.assertEquals(kwargs["repeat_instance"], 1)

        next_instance = self.get_next_instance(exported_task_redcap1)

        self.assertEquals(next_instance.next_instance_id, 2)

        exported_task2 = ExportedTask(task=self.task2, recipient=self.recipient)
        exported_task_redcap2 = ExportedTaskRedcap(exported_task2)

        exporter.export_task(self.req, exported_task_redcap2)
        args, kwargs = project.import_records.call_args

        rows = args[0]
        record = rows[0]

        self.assertEquals(record["redcap_repeat_instance"], 1)
        next_instance = self.get_next_instance(exported_task_redcap2)

        self.assertEquals(next_instance.next_instance_id, 2)
