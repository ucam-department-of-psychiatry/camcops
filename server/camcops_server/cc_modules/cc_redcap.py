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
from typing import Any, Dict, Generator, List, TYPE_CHECKING, Union
from unittest import mock, TestCase
import xml.etree.cElementTree as ET

from asteval import Interpreter, make_symbol_table
from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
from pandas import DataFrame
import pendulum
import redcap

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_exportrecipientinfo import ExportRecipientInfo
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase

if TYPE_CHECKING:
    from configparser import ConfigParser
    from camcops_server.cc_modules.cc_exportmodels import ExportedTaskRedcap
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_task import Task

log = BraceStyleAdapter(logging.getLogger(__name__))


class RedcapExportException(Exception):
    pass


class RedcapFieldmap(object):
    """
    Internal representation of the fieldmap XML file.
    This describes how the task fields should be translated to
    the REDCap record.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.fields = {}
        self.files = {}
        self.instruments = {}

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
        if root.tag != "fieldmap":
            raise RedcapExportException(
                (f"Expected the root tag to be 'fieldmap' instead of "
                 f"'{root.tag}' in {filename}")
            )

        # TODO: Missing identifier and missing attributes
        identifier_element = root.find("identifier")

        self.identifier = identifier_element.attrib

        try:
            instrument_elements = root.find("instruments")
        except ET.ParseError:
            raise RedcapExportException(
                f"No 'instruments' tag in {filename}"
            )

        for instrument_element in instrument_elements:
            task = instrument_element.get("task")
            # TODO: name empty
            instrument_name = instrument_element.get("name")
            self.fields[task] = {}
            self.files[task] = {}
            self.instruments[task] = instrument_name

            # TODO: task empty
            field_elements = instrument_element.find("fields") or []

            for field_element in field_elements:
                name = field_element.get("name")
                formula = field_element.get("formula")

                self.fields[task][name] = formula

            file_elements = instrument_element.find("files") or []
            for file_element in file_elements:
                name = file_element.get("name")
                formula = file_element.get("formula")
                self.files[task][name] = formula

    def instrument_names(self) -> List:
        return list(self.instruments.values())


class RedcapTaskExporter(object):
    """
    Main entry point for task export to REDCap. Works out which record needs
    updating or creating. Creates the fieldmap and initiates upload.
    """
    def export_task(self,
                    req: "CamcopsRequest",
                    exported_task_redcap: "ExportedTaskRedcap") -> None:
        exported_task = exported_task_redcap.exported_task
        recipient = exported_task.recipient
        task = exported_task.task
        which_idnum = recipient.primary_idnum
        idnum_object = task.patient.get_idnum_object(which_idnum)

        project = self.get_project(recipient)
        fieldmap = self.get_fieldmap(req)

        existing_records = self._get_existing_records(fieldmap)
        record_id = self._get_existing_record_id(existing_records,
                                                 fieldmap,
                                                 idnum_object.idnum_value)

        instrument_name = fieldmap.instruments[task.tablename]
        next_instance_id = self._get_next_instance_id(existing_records,
                                                      instrument_name,
                                                      record_id)

        uploader_class = RedcapNewRecordUploader
        if record_id != 0:
            uploader_class = RedcapUpdatedRecordUploader

        uploader = uploader_class(req, project)

        new_record_id = uploader.upload(task, record_id, next_instance_id,
                                        fieldmap)

        exported_task_redcap.redcap_record_id = new_record_id

    def _get_existing_records(self,
                              fieldmap: "RedcapFieldmap") -> "DataFrame":
        # Arguments to pandas read_csv()
        df_kwargs = {"index_col": None}  # don't index by record_id

        project = self.get_project()
        forms = (fieldmap.instrument_names() +
                 [fieldmap.identifier['instrument']])

        return project.export_records(format='df', forms=forms,
                                      df_kwargs=df_kwargs)

    def _get_existing_record_id(self,
                                records: "DataFrame",
                                fieldmap,
                                idnum_value) -> Union[int, None]:
        # TODO: Handle missing 'redcap_field' column
        has_identifier = records[
            fieldmap.identifier['redcap_field']
        ] == idnum_value

        if len(records[has_identifier]) == 0:
            return 0

        return records[has_identifier].iat[0, 0]

    def _get_next_instance_id(self,
                              records: "DataFrame",
                              instrument: str,
                              record_id: int) -> int:
        if record_id == 0:
            # no existing records so it's 1
            return 1

        max_values = records[
            (records["redcap_repeat_instrument"] == instrument) &
            (records["record_id"] == record_id)
        ].max()

        return max_values['redcap_repeat_instance'] + 1

    def get_fieldmap(self, req: "CamcopsRequest") -> RedcapFieldmap:
        fieldmap = RedcapFieldmap(self.get_fieldmap_filename(req))

        return fieldmap

    def get_fieldmap_filename(self, req: "CamcopsRequest") -> str:
        filename = req.config.redcap_fieldmap_filename
        if filename is None:
            raise RedcapExportException(
                "REDCAP_FIELDMAP_FILENAME is not set in the config file"
            )

        if filename == "":
            raise RedcapExportException(
                "REDCAP_FIELDMAP_FILENAME is empty in the config file"
            )

        return filename

    def get_project(self, recipient: ExportRecipient):
        try:
            project = redcap.project.Project(
                recipient.redcap_api_url, recipient.redcap_api_key
            )
        except redcap.RedcapError as e:
            raise RedcapExportException(str(e))

        return project


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
    fieldmap.

    Knows nothing about ExportedTaskRedcap, ExportedTask, ExportRecipient
    """
    def __init__(self,
                 req: "CamcopsRequest",
                 project: "redcap.project.Project") -> None:
        self.req = req
        self.project = project

    def upload(self, task: "Task", record_id: int,
               next_instance_id: int, fieldmap: RedcapFieldmap) -> int:
        complete_status = RedcapRecordStatus.INCOMPLETE

        if task.is_complete():
            complete_status = RedcapRecordStatus.COMPLETE
        instrument_name = fieldmap.instruments[task.tablename]

        repeat_instance = next_instance_id

        record = {
            "record_id": record_id,
            "redcap_repeat_instrument": instrument_name,
            # https://community.projectredcap.org/questions/74561/unexpected-behaviour-with-import-records-repeat-in.html  # noqa
            # REDCap won't create instance IDs automatically so we have to
            # assume no one else is writing to this record
            "redcap_repeat_instance": repeat_instance,
            f"{instrument_name}_complete": complete_status.value,
        }

        self.transform_fields(record, task, fieldmap.fields[task.tablename])

        response = self.upload_record(record)
        new_record_id = self.get_new_record_id(record_id, response)

        file_dict = {}
        self.transform_fields(file_dict, task, fieldmap.files[task.tablename])

        self.upload_files(task,
                          new_record_id,
                          repeat_instance,
                          file_dict)

        self.log_success(new_record_id)

        return new_record_id

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
                         formula_dict: Dict) -> None:
        extra_symbols = self.get_extra_symbols()

        symbol_table = make_symbol_table(
            task=task,
            **extra_symbols
        )
        interpreter = Interpreter(symtable=symbol_table)

        for redcap_field, formula in formula_dict.items():
            v = interpreter(f"{formula}", show_errors=True)
            if interpreter.error:
                message = "\n".join([e.msg for e in interpreter.error])
                raise RedcapExportException(
                    (
                        f"Fieldmap:\n"
                        f"Error in formula '{formula}': {message}\n"
                        f"Task: '{task.tablename}'\n"
                        f"REDCap field: '{redcap_field}'\n"
                    )
                )
            field_dict[redcap_field] = v

    def get_extra_symbols(self):
        return dict(
            format_datetime=format_datetime,
            DateFormat=DateFormat,
            request=self.req
        )


class RedcapNewRecordUploader(RedcapUploader):
    force_auto_number = True
    # import_records returns ["<redcap record id>, 0"]
    return_content = "auto_ids"

    def get_new_record_id(self, record_id: int, response: List[str]):
        id_pair = response[0]

        record_id = int(id_pair.split(",")[0])

        return record_id

    def log_success(self, record_id: int):
        log.info(f"Created new REDCap record {record_id}")


class RedcapUpdatedRecordUploader(RedcapUploader):
    force_auto_number = False
    # import_records returns {'count': 1}
    return_content = "count"

    def get_new_record_id(self, old_record_id: int, response: Any):
        return old_record_id

    def log_success(self, record_id: int):
        log.info(f"Updated REDCap record {record_id}")


# =============================================================================
# Unit testing
# =============================================================================

class MockProject(mock.Mock):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.export_records = mock.Mock()
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

        task = mock.Mock(tablename="bmi")
        fieldmap = {"pa_height": "sys.platform"}

        field_dict = {}

        with self.assertRaises(RedcapExportException) as cm:
            exporter.transform_fields(field_dict, task, fieldmap)

        message = str(cm.exception)
        self.assertIn("Error in formula 'sys.platform':", message)
        self.assertIn("Task: 'bmi'", message)
        self.assertIn("REDCap field: 'pa_height'", message)
        self.assertIn("'sys' is not defined", message)

    def test_raises_when_fieldmap_empty_in_config(self) -> None:

        exporter = MockRedcapTaskExporter()

        mock_config = mock.Mock(redcap_fieldmap_filename="")
        req = mock.Mock(config=mock_config)
        with self.assertRaises(RedcapExportException) as cm:
            exporter.get_fieldmap_filename(req)

        message = str(cm.exception)
        self.assertIn("REDCAP_FIELDMAP_FILENAME is empty in the config file",
                      message)

    def test_raises_when_fieldmap_not_set_in_config(self) -> None:

        exporter = MockRedcapTaskExporter()

        mock_config = mock.Mock(redcap_fieldmap_filename=None)
        req = mock.Mock(config=mock_config)
        with self.assertRaises(RedcapExportException) as cm:
            exporter.get_fieldmap_filename(req)

        message = str(cm.exception)
        self.assertIn("REDCAP_FIELDMAP_FILENAME is not set in the config file",
                      message)

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

    def test_raises_when_fieldmap_missing(self):
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
        self.assertIn(("Expected the root tag to be 'fieldmap' instead of "
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
    fieldmap = ""

    def override_config_settings(self, parser: "ConfigParser"):
        parser.set("site", "REDCAP_FIELDMAP_FILENAME", self.fieldmap_filename)

    def setUp(self) -> None:
        self.fieldmap_filename = os.path.join(
            self.tmpdir_obj.name, "redcap_fieldmap.xml")
        self.write_fieldmaps()

        recipientinfo = ExportRecipientInfo()

        self.recipient = ExportRecipient(recipientinfo)
        self.recipient.primary_idnum = 1001

        # auto increment doesn't work for BigInteger with SQLite
        self.recipient.id = 1
        self.recipient.recipient_name = "test"

        super().setUp()

    def write_fieldmaps(self) -> None:
        with open(self.fieldmap_filename, "w") as f:
            f.write(self.fieldmap)

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
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <identifier instrument="patient_record" redcap_field="patient_id" />
  <instruments>
    <instrument task="bmi" name="bmi">
      <fields>
        <field name="pa_height" formula="format(task.height_m, '.1f')" />
        <field name="pa_weight" formula="format(task.mass_kg, '.1f')" />
        <field name="bmi_date" formula="format_datetime(task.when_created, DateFormat.ISO8601_DATE_ONLY)" />
        </fields>
    </instrument>
  </instruments>
</fieldmap>"""  # noqa: E501


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
        project.export_records.return_value = DataFrame({'patient_id': []})
        project.import_records.return_value = ["123,0"]

        exporter.export_task(self.req, exported_task_redcap)
        self.assertEquals(exported_task_redcap.redcap_record_id, 123)

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
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]

        exported_task1 = ExportedTask(task=self.task1, recipient=self.recipient)
        exported_task_redcap1 = ExportedTaskRedcap(exported_task1)
        exporter.export_task(self.req, exported_task_redcap1)
        self.assertEquals(exported_task_redcap1.redcap_record_id, 123)

        project.export_records.return_value = DataFrame({
            "record_id": [123],
            "patient_id": [555],
            "redcap_repeat_instrument": ["bmi"],
            "redcap_repeat_instance": [1],
        })
        exported_task2 = ExportedTask(task=self.task2, recipient=self.recipient)
        exported_task_redcap2 = ExportedTaskRedcap(exported_task2)

        exporter.export_task(self.req, exported_task_redcap2)
        args, kwargs = project.import_records.call_args

        rows = args[0]
        record = rows[0]

        self.assertEquals(record["record_id"], 123)
        self.assertEquals(record["redcap_repeat_instance"], 2)


class Phq9RedcapExportTests(RedcapExportTestCase):
    """
    These are more of a test of the fieldmap code than anything
    related to the PHQ9 task
    """
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <identifier instrument="patient_record" redcap_field="patient_id" />
  <instruments>
    <instrument task="phq9" name="patient_health_questionnaire_9">
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
    </instrument>
  </instruments>
</fieldmap>"""  # noqa: E501

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
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]
        exporter.export_task(self.req, exported_task_redcap)
        self.assertEquals(exported_task_redcap.redcap_record_id, 123)

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
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <identifier instrument="patient_record" redcap_field="patient_id" />
  <instruments>
    <instrument task="khandaker_mojo_medicationtherapy" name="medication_table">
      <files>
        <field name="medtbl_medication_items" formula="task.get_pdf(request)" />
      </files>
    </instrument>
  </instruments>
</fieldmap>"""  # noqa: E501

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
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]

        # We can't just look at the call_args here because the file will already
        # have been closed by then
        def read_pdf_bytes(*args, **kwargs):
            file_obj = args[3]
            read_pdf_bytes.pdf_header = file_obj.read(5)

        project.import_file.side_effect = read_pdf_bytes

        exporter.export_task(self.req, exported_task_redcap)
        self.assertEquals(exported_task_redcap.redcap_record_id, 123)

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
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <identifier instrument="patient_record" redcap_field="patient_id" />
  <instruments>
    <instrument task="bmi" name="bmi">
      <fields>
        <field name="pa_height" formula="format(task.height_m, '.1f')" />
        <field name="pa_weight" formula="format(task.mass_kg, '.1f')" />
        <field name="bmi_date" formula="format_datetime(task.when_created, DateFormat.ISO8601_DATE_ONLY)" />
      </fields>
    </instrument>
    <instrument task="khandaker_mojo_medicationtherapy" name="medication_table">
      <files>
        <field name="medtbl_medication_items" formula="task.get_pdf(request)" />
      </files>
    </instrument>
  </instruments>
</fieldmap>
"""  # noqa: E501

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
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]

        exported_task1 = ExportedTask(task=self.task1, recipient=self.recipient)
        exported_task_redcap1 = ExportedTaskRedcap(exported_task1)
        exporter.export_task(self.req, exported_task_redcap1)
        self.assertEquals(exported_task_redcap1.redcap_record_id, 123)
        args, kwargs = project.import_file.call_args

        self.assertEquals(kwargs["repeat_instance"], 1)

        exported_task2 = ExportedTask(task=self.task2, recipient=self.recipient)
        exported_task_redcap2 = ExportedTaskRedcap(exported_task2)

        exporter.export_task(self.req, exported_task_redcap2)
        args, kwargs = project.import_records.call_args

        rows = args[0]
        record = rows[0]

        self.assertEquals(record["redcap_repeat_instance"], 1)
