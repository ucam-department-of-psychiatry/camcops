"""camcops_server/cc_modules/tests/cc_redcap_tests.py

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
"""

import os
import tempfile
from typing import Any, Dict, Generator
from unittest import mock, TestCase

from pandas import DataFrame
import pendulum
import redcap

from camcops_server.cc_modules.cc_constants import ConfigParamExportRecipient
from camcops_server.cc_modules.cc_exportmodels import (
    ExportedTask,
    ExportedTaskRedcap,
)
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_exportrecipientinfo import (
    ExportRecipientInfo,
)
from camcops_server.cc_modules.cc_redcap import (
    MISSING_EVENT_TAG_OR_ATTRIBUTE,
    RedcapExportException,
    RedcapFieldmap,
    RedcapNewRecordUploader,
    RedcapRecordStatus,
    RedcapTaskExporter,
)
from camcops_server.cc_modules.cc_testfactories import (
    NHSPatientIdNumFactory,
    PatientFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.tasks.tests.factories import (
    APEQCPFTPerinatalFactory,
    BmiFactory,
    KhandakerMojoMedicationTherapyFactory,
    Phq9Factory,
)

# =============================================================================
# Unit testing
# =============================================================================


class MockProject(mock.Mock):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.export_project_info = mock.Mock()
        self.export_records = mock.Mock()
        self.generate_next_record_name = mock.Mock()
        self.import_file = mock.Mock()
        self.import_records = mock.Mock()
        self.is_longitudinal = mock.Mock(return_value=False)


class MockRedcapTaskExporter(RedcapTaskExporter):
    def __init__(self) -> None:
        mock_project = MockProject()
        self.get_project = mock.Mock(return_value=mock_project)  # type: ignore[method-assign]  # noqa: E501

        config = mock.Mock()
        self.req = mock.Mock(config=config)


class MockRedcapNewRecordUploader(RedcapNewRecordUploader):
    # noinspection PyMissingConstructor
    def __init__(self) -> None:
        self.req = mock.Mock()
        self.project = MockProject()
        self.task = mock.Mock(tablename="mock_task")


class RedcapExporterTests(TestCase):
    def test_next_instance_id_converted_to_int(self) -> None:
        import numpy

        records = DataFrame(
            {
                "record_id": ["1", "1", "1", "1", "1"],
                "redcap_repeat_instrument": [
                    "bmi",
                    "bmi",
                    "bmi",
                    "bmi",
                    "bmi",
                ],
                "redcap_repeat_instance": [
                    numpy.float64(1.0),
                    numpy.float64(2.0),
                    numpy.float64(3.0),
                    numpy.float64(4.0),
                    numpy.float64(5.0),
                ],
            }
        )

        next_instance_id = RedcapTaskExporter._get_next_instance_id(
            records, "bmi", "record_id", "1"
        )

        self.assertEqual(next_instance_id, 6)
        self.assertEqual(type(next_instance_id), int)


class RedcapExportErrorTests(TestCase):
    def test_raises_when_fieldmap_has_unknown_symbols(self) -> None:
        exporter = MockRedcapNewRecordUploader()

        task = mock.Mock(tablename="bmi")
        fieldmap = {"pa_height": "sys.platform"}

        field_dict: Dict[str, Any] = {}

        with self.assertRaises(RedcapExportException) as cm:
            exporter.transform_fields(field_dict, task, fieldmap)

        message = str(cm.exception)
        self.assertIn("Error in formula 'sys.platform':", message)
        self.assertIn("Task: 'bmi'", message)
        self.assertIn("REDCap field: 'pa_height'", message)
        self.assertIn("'sys' is not defined", message)

    def test_raises_when_fieldmap_empty_in_config(self) -> None:

        exporter = MockRedcapTaskExporter()

        recipient = mock.Mock(redcap_fieldmap_filename="")
        with self.assertRaises(RedcapExportException) as cm:
            exporter.get_fieldmap_filename(recipient)

        message = str(cm.exception)
        self.assertIn(
            f"{ConfigParamExportRecipient.REDCAP_FIELDMAP_FILENAME} "
            f"is empty in the config file",
            message,
        )

    def test_raises_when_fieldmap_not_set_in_config(self) -> None:

        exporter = MockRedcapTaskExporter()

        recipient = mock.Mock(redcap_fieldmap_filename=None)
        with self.assertRaises(RedcapExportException) as cm:
            exporter.get_fieldmap_filename(recipient)

        message = str(cm.exception)
        self.assertIn(
            f"{ConfigParamExportRecipient.REDCAP_FIELDMAP_FILENAME} "
            f"is not set in the config file",
            message,
        )

    def test_raises_when_error_from_redcap_on_import(self) -> None:
        exporter = MockRedcapNewRecordUploader()
        exporter.project.import_records.side_effect = redcap.RedcapError(
            "Something went wrong"
        )

        with self.assertRaises(RedcapExportException) as cm:
            record: Dict[str, Any] = {}
            exporter.upload_record(record)
        message = str(cm.exception)

        self.assertIn("Something went wrong", message)

    def test_raises_when_error_from_redcap_on_init(self) -> None:
        with mock.patch("redcap.project.Project.__init__") as mock_init:
            mock_init.side_effect = redcap.RedcapError("Something went wrong")

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
        with self.assertRaises(RedcapExportException) as cm:
            RedcapFieldmap("/does/not/exist/bmi.xml")

        message = str(cm.exception)

        self.assertIn("Unable to open fieldmap file", message)
        self.assertIn("bmi.xml", message)

    def test_raises_when_fieldmap_missing(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<someothertag></someothertag>
"""
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn(
            (
                "Expected the root tag to be 'fieldmap' instead of "
                "'someothertag'"
            ),
            message,
        )
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_root_tag_missing(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
"""
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn("There was a problem parsing", message)
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_patient_missing(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <fieldmap>
                </fieldmap>
                """
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn("'patient' is missing from", message)
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_patient_missing_attributes(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <fieldmap>
                <patient />
                </fieldmap>
                """
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn(
            "'patient' must have attributes: instrument, redcap_field", message
        )
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_record_missing(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <fieldmap>
                    <patient instrument="patient_record" redcap_field="patient_id" />
                </fieldmap>
                """  # noqa: E501
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn("'record' is missing from", message)
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_record_missing_attributes(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <fieldmap>
                   <patient instrument="patient_record" redcap_field="patient_id" />
                   <record />
                </fieldmap>
                """  # noqa: E501
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn(
            "'record' must have attributes: instrument, redcap_field", message
        )
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_instruments_missing(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <fieldmap>
                    <patient instrument="patient_record" redcap_field="patient_id" />
                    <record instrument="patient_record" redcap_field="record_id" />
                </fieldmap>
                """  # noqa: E501
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn("'instruments' tag is missing from", message)
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_instruments_missing_attributes(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <fieldmap>
                    <patient instrument="patient_record" redcap_field="patient_id" />
                    <record instrument="patient_record" redcap_field="record_id" />
                    <instruments>
                        <instrument />
                    </instruments>
                </fieldmap>
                """  # noqa: E501
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn("'instrument' must have attributes: name, task", message)
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_file_fields_missing_attributes(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <fieldmap>
                    <patient instrument="patient_record" redcap_field="patient_id" />
                    <record instrument="patient_record" redcap_field="record_id" />
                    <instruments>
                        <instrument name="bmi" task="bmi">
                            <files>
                                <field />
                            </files>
                        </instrument>
                    </instruments>
                </fieldmap>
                """  # noqa: E501
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn("'field' must have attributes: name, formula", message)
        self.assertIn(fieldmap_file.name, message)

    def test_raises_when_fields_missing_attributes(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="xml"
        ) as fieldmap_file:
            fieldmap_file.write(
                """<?xml version="1.0" encoding="UTF-8"?>
                <fieldmap>
                    <patient instrument="patient_record" redcap_field="patient_id" />
                    <record instrument="patient_record" redcap_field="record_id" />
                    <instruments>
                        <instrument name="bmi" task="bmi">
                            <fields>
                                <field />
                            </fields>
                        </instrument>
                    </instruments>
                </fieldmap>
                """  # noqa: E501
            )
            fieldmap_file.flush()

            with self.assertRaises(RedcapExportException) as cm:
                RedcapFieldmap(fieldmap_file.name)

        message = str(cm.exception)
        self.assertIn("'field' must have attributes: name, formula", message)
        self.assertIn(fieldmap_file.name, message)


# =============================================================================
# Integration testing
# =============================================================================


class RedcapExportTestCase(DemoRequestTestCase):
    fieldmap = ""

    def setUp(self) -> None:
        super().setUp()

        self.patient = PatientFactory()
        self.patient_idnum = NHSPatientIdNumFactory(patient=self.patient)

        recipientinfo = ExportRecipientInfo()

        self.recipient = ExportRecipient(other=recipientinfo)
        self.recipient.primary_idnum = self.patient_idnum.which_idnum

        # auto increment doesn't work for BigInteger with SQLite
        self.recipient.id = 1
        self.recipient.recipient_name = "test"
        self.recipient.redcap_fieldmap_filename = os.path.join(
            self.tmpdir_obj.name, "redcap_fieldmap.xml"  # type: ignore[attr-defined]  # noqa: E501
        )
        self.write_fieldmaps(self.recipient.redcap_fieldmap_filename)

    def write_fieldmaps(self, filename: str) -> None:
        with open(filename, "w") as f:
            f.write(self.fieldmap)


class BmiRedcapValidFieldmapTestCase(RedcapExportTestCase):
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="patient_id" />
  <record instrument="instrument_with_record_id" redcap_field="record_id" />
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

    def setUp(self) -> None:
        super().setUp()

        self.task = BmiFactory(
            patient=self.patient,
            height_m=1.83,
            mass_kg=67.57,
            when_created=pendulum.parse("2010-07-07"),
        )

    def test_record_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        exporter.export_task(self.req, exported_task_redcap)
        self.assertEqual(exported_task_redcap.redcap_record_id, "123")
        self.assertEqual(exported_task_redcap.redcap_instrument_name, "bmi")
        self.assertEqual(exported_task_redcap.redcap_instance_id, 1)

        args, kwargs = project.export_records.call_args

        self.assertIn("bmi", kwargs["forms"])
        self.assertIn("patient_record", kwargs["forms"])
        self.assertIn("instrument_with_record_id", kwargs["forms"])

        # Initial call with original record
        args, kwargs = project.import_records.call_args_list[0]

        rows = args[0]
        record = rows[0]

        self.assertEqual(record["redcap_repeat_instrument"], "bmi")
        self.assertEqual(record["redcap_repeat_instance"], 1)
        self.assertEqual(record["record_id"], "0")
        self.assertEqual(
            record["bmi_complete"], RedcapRecordStatus.COMPLETE.value
        )
        self.assertEqual(record["bmi_date"], "2010-07-07")

        self.assertEqual(record["pa_height"], "1.8")
        self.assertEqual(record["pa_weight"], "67.6")

        self.assertEqual(kwargs["return_content"], "auto_ids")
        self.assertTrue(kwargs["force_auto_number"])

        # Second call with updated patient ID
        args, kwargs = project.import_records.call_args_list[1]
        rows = args[0]
        record = rows[0]

        self.assertEqual(record["patient_id"], self.patient_idnum.idnum_value)

    def test_record_exported_with_non_integer_id(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["15-123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        exporter.export_task(self.req, exported_task_redcap)
        self.assertEqual(exported_task_redcap.redcap_record_id, "15-123")

    def test_record_id_generated_when_no_autonumbering(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = {"count": 1}
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 0
        }
        project.generate_next_record_name.return_value = "15-29"

        exporter.export_task(self.req, exported_task_redcap)

        # Initial call with original record
        args, kwargs = project.import_records.call_args_list[0]

        rows = args[0]
        record = rows[0]

        self.assertEqual(record["record_id"], "15-29")
        self.assertEqual(kwargs["return_content"], "count")
        self.assertFalse(kwargs["force_auto_number"])

    def test_record_imported_when_no_existing_records(self) -> None:
        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame()
        project.import_records.return_value = ["1,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)
        exporter.export_task(self.req, exported_task_redcap)

        self.assertEqual(exported_task_redcap.redcap_record_id, "1")
        self.assertEqual(exported_task_redcap.redcap_instrument_name, "bmi")
        self.assertEqual(exported_task_redcap.redcap_instance_id, 1)


class BmiRedcapUpdateTests(BmiRedcapValidFieldmapTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.task1 = BmiFactory(
            patient=self.patient,
        )
        self.task2 = BmiFactory(
            patient=self.patient,
        )

    def test_existing_record_id_used_for_update(self) -> None:
        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        exported_task1 = ExportedTask(
            task=self.task1, recipient=self.recipient
        )
        exported_task_redcap1 = ExportedTaskRedcap(exported_task1)
        exporter.export_task(self.req, exported_task_redcap1)
        self.assertEqual(exported_task_redcap1.redcap_record_id, "123")
        self.assertEqual(exported_task_redcap1.redcap_instrument_name, "bmi")
        self.assertEqual(exported_task_redcap1.redcap_instance_id, 1)

        project.export_records.return_value = DataFrame(
            {
                "record_id": ["123"],
                "patient_id": [self.patient_idnum.idnum_value],
                "redcap_repeat_instrument": ["bmi"],
                "redcap_repeat_instance": [1],
            }
        )
        exported_task2 = ExportedTask(
            task=self.task2, recipient=self.recipient
        )
        exported_task_redcap2 = ExportedTaskRedcap(exported_task2)

        exporter.export_task(self.req, exported_task_redcap2)
        self.assertEqual(exported_task_redcap2.redcap_record_id, "123")
        self.assertEqual(exported_task_redcap2.redcap_instrument_name, "bmi")
        self.assertEqual(exported_task_redcap2.redcap_instance_id, 2)

        # Third call (after initial record and patient ID)
        args, kwargs = project.import_records.call_args_list[2]

        rows = args[0]
        record = rows[0]

        self.assertEqual(record["record_id"], "123")
        self.assertEqual(record["redcap_repeat_instance"], 2)
        self.assertEqual(kwargs["return_content"], "count")
        self.assertFalse(kwargs["force_auto_number"])


class Phq9RedcapExportTests(RedcapExportTestCase):
    """
    These are more of a test of the fieldmap code than anything
    related to the PHQ9 task. For these we have also renamed the record_id
    field.
    """

    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="patient_id" />
  <record instrument="patient_record" redcap_field="my_record_id" />
  <instruments>
    <instrument task="phq9" name="patient_health_questionnaire_9">
      <fields>
        <field name="phq9_how_difficult" formula="task.q10 + 1 if task.q10 is not None else None" />
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

    def setUp(self) -> None:
        super().setUp()

        self.task = Phq9Factory(
            patient=self.patient,
            q1=0,
            q2=1,
            q3=2,
            q4=3,
            q5=0,
            q6=1,
            q7=2,
            q8=3,
            q9=0,
            q10=3,
            when_created=pendulum.parse("2010-07-07"),
        )

    def test_record_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        exporter.export_task(self.req, exported_task_redcap)
        self.assertEqual(exported_task_redcap.redcap_record_id, "123")
        self.assertEqual(
            exported_task_redcap.redcap_instrument_name,
            "patient_health_questionnaire_9",
        )
        self.assertEqual(exported_task_redcap.redcap_instance_id, 1)

        # Initial call with new record
        args, kwargs = project.import_records.call_args_list[0]

        rows = args[0]
        record = rows[0]

        self.assertEqual(
            record["redcap_repeat_instrument"],
            "patient_health_questionnaire_9",
        )
        self.assertEqual(record["my_record_id"], "0")
        self.assertEqual(
            record["patient_health_questionnaire_9_complete"],
            RedcapRecordStatus.COMPLETE.value,
        )
        self.assertEqual(record["phq9_how_difficult"], 4)
        self.assertEqual(record["phq9_total_score"], 12)
        self.assertEqual(record["phq9_first_name"], self.patient.forename)
        self.assertEqual(record["phq9_last_name"], self.patient.surname)
        self.assertEqual(record["phq9_date_enrolled"], "2010-07-07")

        self.assertEqual(record["phq9_1"], 0)
        self.assertEqual(record["phq9_2"], 1)
        self.assertEqual(record["phq9_3"], 2)
        self.assertEqual(record["phq9_4"], 3)
        self.assertEqual(record["phq9_5"], 0)
        self.assertEqual(record["phq9_6"], 1)
        self.assertEqual(record["phq9_7"], 2)
        self.assertEqual(record["phq9_8"], 3)
        self.assertEqual(record["phq9_9"], 0)

        self.assertEqual(kwargs["return_content"], "auto_ids")
        self.assertTrue(kwargs["force_auto_number"])

        # Second call with patient ID
        args, kwargs = project.import_records.call_args_list[1]

        rows = args[0]
        record = rows[0]
        self.assertEqual(record["patient_id"], self.patient_idnum.idnum_value)


class MedicationTherapyRedcapExportTests(RedcapExportTestCase):
    """
    These are more of a test of the file upload code than anything
    related to the KhandakerMojoMedicationTherapy task
    """

    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <event name="event_1_arm_1" />
  <patient instrument="patient_record" redcap_field="patient_id" />
  <record instrument="patient_record" redcap_field="record_id" />
  <instruments>
    <instrument task="khandaker_mojo_medicationtherapy" name="medication_table">
      <files>
        <field name="medtbl_medication_items" formula="task.get_pdf(request)" />
      </files>
    </instrument>
  </instruments>
</fieldmap>"""  # noqa: E501

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.id_sequence = self.get_id()

    @staticmethod
    def get_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1

    def setUp(self) -> None:
        super().setUp()

        self.task = KhandakerMojoMedicationTherapyFactory(
            patient=self.patient,
        )

    def test_record_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        # We can't just look at the call_args on the mock object because
        # the file will already have been closed by then
        # noinspection PyUnusedLocal
        def read_pdf_bytes(
            *import_file_args: Any, **import_file_kwargs: Any
        ) -> None:
            # record, field, fname, fobj
            file_obj = import_file_args[3]
            read_pdf_bytes.pdf_header = file_obj.read(5)  # type: ignore[attr-defined]  # noqa: E501

        project.import_file.side_effect = read_pdf_bytes

        exporter.export_task(self.req, exported_task_redcap)
        self.assertEqual(exported_task_redcap.redcap_record_id, "123")
        self.assertEqual(
            exported_task_redcap.redcap_instrument_name, "medication_table"
        )
        self.assertEqual(exported_task_redcap.redcap_instance_id, 1)

        args, kwargs = project.import_file.call_args

        record_id = args[0]
        fieldname = args[1]
        filename = args[2]

        self.assertEqual(record_id, "123")
        self.assertEqual(fieldname, "medtbl_medication_items")
        self.assertEqual(
            filename,
            "khandaker_mojo_medicationtherapy_123_medtbl_medication_items",
        )

        self.assertEqual(kwargs["repeat_instance"], 1)
        # noinspection PyUnresolvedReferences
        self.assertEqual(read_pdf_bytes.pdf_header, b"%PDF-")  # type: ignore[attr-defined]  # noqa: E501
        self.assertEqual(kwargs["event"], "event_1_arm_1")


class MultipleTaskRedcapExportTests(RedcapExportTestCase):
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="patient_id" />
  <record instrument="patient_record" redcap_field="record_id" />
  <instruments>
    <instrument task="bmi" name="bmi" event="bmi_event">
      <fields>
        <field name="pa_height" formula="format(task.height_m, '.1f')" />
        <field name="pa_weight" formula="format(task.mass_kg, '.1f')" />
        <field name="bmi_date" formula="format_datetime(task.when_created, DateFormat.ISO8601_DATE_ONLY)" />
      </fields>
    </instrument>
    <instrument task="khandaker_mojo_medicationtherapy" name="medication_table" event="mojo_event">
      <files>
        <field name="medtbl_medication_items" formula="task.get_pdf(request)" />
      </files>
    </instrument>
  </instruments>
</fieldmap>
"""  # noqa: E501

    def setUp(self) -> None:
        super().setUp()

        self.mojo_task = KhandakerMojoMedicationTherapyFactory(
            patient=self.patient
        )

        self.bmi_task = BmiFactory(patient=self.patient)

    def test_instance_ids_on_different_tasks_in_same_record(self) -> None:
        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        exported_task_mojo = ExportedTask(
            task=self.mojo_task, recipient=self.recipient
        )
        exported_task_redcap_mojo = ExportedTaskRedcap(exported_task_mojo)
        exporter.export_task(self.req, exported_task_redcap_mojo)
        self.assertEqual(exported_task_redcap_mojo.redcap_record_id, "123")
        args, kwargs = project.import_file.call_args

        self.assertEqual(kwargs["repeat_instance"], 1)

        project.export_records.return_value = DataFrame(
            {
                "record_id": ["123"],
                "patient_id": [self.patient_idnum.idnum_value],
                "redcap_repeat_instrument": [
                    "khandaker_mojo_medicationtherapy"
                ],
                "redcap_repeat_instance": [1],
            }
        )
        exported_task_bmi = ExportedTask(
            task=self.bmi_task, recipient=self.recipient
        )
        exported_task_redcap_bmi = ExportedTaskRedcap(exported_task_bmi)

        exporter.export_task(self.req, exported_task_redcap_bmi)

        # Import of second task, but is first instance
        # (third call to import_records)
        args, kwargs = project.import_records.call_args_list[2]

        rows = args[0]
        record = rows[0]

        self.assertEqual(record["redcap_repeat_instance"], 1)

    def test_imported_into_different_events(self) -> None:
        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]

        project.is_longitudinal = mock.Mock(return_value=True)
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        exported_task_mojo = ExportedTask(
            task=self.mojo_task, recipient=self.recipient
        )
        exported_task_redcap_mojo = ExportedTaskRedcap(exported_task_mojo)

        exporter.export_task(self.req, exported_task_redcap_mojo)

        args, kwargs = project.import_records.call_args_list[0]
        rows = args[0]
        record = rows[0]

        self.assertEqual(record["redcap_event_name"], "mojo_event")
        args, kwargs = project.import_file.call_args

        self.assertEqual(kwargs["event"], "mojo_event")

        exported_task_bmi = ExportedTask(
            task=self.bmi_task, recipient=self.recipient
        )
        exported_task_redcap_bmi = ExportedTaskRedcap(exported_task_bmi)

        exporter.export_task(self.req, exported_task_redcap_bmi)

        # Import of second task (third call to import_records)
        args, kwargs = project.import_records.call_args_list[2]
        rows = args[0]
        record = rows[0]
        self.assertEqual(record["redcap_event_name"], "bmi_event")


class BadConfigurationRedcapTests(RedcapExportTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.task = BmiFactory(patient=self.patient)


class MissingInstrumentRedcapTests(BadConfigurationRedcapTests):
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="patient_id" />
  <record instrument="patient_record" redcap_field="record_id" />
  <instruments>
    <instrument task="phq9" name="patient_health_questionnaire_9">
      <fields>
      </fields>
    </instrument>
  </instruments>
</fieldmap>"""

    def test_raises_when_instrument_missing_from_fieldmap(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame({"patient_id": []})
        project.import_records.return_value = ["123,0"]

        with self.assertRaises(RedcapExportException) as cm:
            exporter.export_task(self.req, exported_task_redcap)

        message = str(cm.exception)
        self.assertIn(
            "Instrument for task 'bmi' is missing from the fieldmap", message
        )


class IncorrectRecordIdRedcapTests(BadConfigurationRedcapTests):
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="patient_id" />
  <record instrument="patient_record" redcap_field="my_record_id" />
  <instruments>
    <instrument task="bmi" name="bmi">
      <fields>
      </fields>
    </instrument>
  </instruments>
</fieldmap>"""

    def test_raises_when_record_id_is_incorrect(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame(
            {
                "record_id": ["123"],
                "patient_id": [self.patient_idnum.idnum_value],
                "redcap_repeat_instrument": ["bmi"],
                "redcap_repeat_instance": [1],
            }
        )
        project.import_records.return_value = ["123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        with self.assertRaises(RedcapExportException) as cm:
            exporter.export_task(self.req, exported_task_redcap)

        message = str(cm.exception)
        self.assertIn("Field 'my_record_id' does not exist in REDCap", message)


class IncorrectPatientIdRedcapTests(BadConfigurationRedcapTests):
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="my_patient_id" />
  <record instrument="patient_record" redcap_field="record_id" />
  <instruments>
    <instrument task="bmi" name="bmi">
      <fields>
      </fields>
    </instrument>
  </instruments>
</fieldmap>"""

    def test_raises_when_patient_id_is_incorrect(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.return_value = DataFrame(
            {
                "record_id": ["123"],
                "patient_id": [self.patient_idnum.idnum_value],
                "redcap_repeat_instrument": ["bmi"],
                "redcap_repeat_instance": [1],
            }
        )
        project.import_records.return_value = ["123,0"]
        project.export_project_info.return_value = {
            "record_autonumbering_enabled": 1
        }

        with self.assertRaises(RedcapExportException) as cm:
            exporter.export_task(self.req, exported_task_redcap)

        message = str(cm.exception)
        self.assertIn(
            "Field 'my_patient_id' does not exist in REDCap", message
        )


class MissingPatientInstrumentRedcapTests(BadConfigurationRedcapTests):
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="my_patient_id" />
  <record instrument="patient_record" redcap_field="record_id" />
  <instruments>
    <instrument task="bmi" name="bmi">
      <fields>
      </fields>
    </instrument>
  </instruments>
</fieldmap>"""

    def test_raises_when_instrument_is_missing(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]
        project.export_records.side_effect = redcap.RedcapError(
            "Something went wrong"
        )

        with self.assertRaises(RedcapExportException) as cm:
            exporter.export_task(self.req, exported_task_redcap)

        message = str(cm.exception)
        self.assertIn("Something went wrong", message)


class MissingEventRedcapTests(BadConfigurationRedcapTests):
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="my_patient_id" />
  <record instrument="patient_record" redcap_field="record_id" />
  <instruments>
    <instrument task="bmi" name="bmi">
      <fields>
      </fields>
    </instrument>
  </instruments>
</fieldmap>"""

    def test_raises_for_longitudinal_project(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]

        project.is_longitudinal = mock.Mock(return_value=True)

        with self.assertRaises(RedcapExportException) as cm:
            exporter.export_task(self.req, exported_task_redcap)

        message = str(cm.exception)
        self.assertEqual(MISSING_EVENT_TAG_OR_ATTRIBUTE, message)


class MissingInstrumentEventRedcapTests(BadConfigurationRedcapTests):
    fieldmap = """<?xml version="1.0" encoding="UTF-8"?>
<fieldmap>
  <patient instrument="patient_record" redcap_field="my_patient_id" />
  <record instrument="patient_record" redcap_field="record_id" />
  <instruments>
    <instrument task="bmi" name="bmi">
      <fields>
      </fields>
    </instrument>
    <instrument task="phq9" name="phq9" event="phq9_event">
      <fields>
      </fields>
    </instrument>
  </instruments>
</fieldmap>"""

    def test_raises_when_instrument_missing_event(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()
        project = exporter.get_project()  # type: ignore[call-arg]

        project.is_longitudinal = mock.Mock(return_value=True)

        with self.assertRaises(RedcapExportException) as cm:
            exporter.export_task(self.req, exported_task_redcap)

        message = str(cm.exception)
        self.assertEqual(MISSING_EVENT_TAG_OR_ATTRIBUTE, message)


class AnonymousTaskRedcapTests(RedcapExportTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.task = APEQCPFTPerinatalFactory()

    def test_raises_when_task_is_anonymous(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_redcap = ExportedTaskRedcap(exported_task)

        exporter = MockRedcapTaskExporter()

        with self.assertRaises(RedcapExportException) as cm:
            exporter.export_task(self.req, exported_task_redcap)

        message = str(cm.exception)
        self.assertIn("Skipping anonymous task 'apeq_cpft_perinatal'", message)
