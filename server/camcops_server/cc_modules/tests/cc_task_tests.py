"""
camcops_server/cc_modules/tests/cc_task_tests.py

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

import logging
import os
from pathlib import Path
from unittest import mock, TestCase

from cardinal_pythonlib.logs import BraceStyleAdapter
from pendulum import Date, DateTime as Pendulum

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_dummy_database import DummyDataInserter
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_pyramid import ViewParam
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_text import SS
from camcops_server.cc_modules.cc_testfactories import UserFactory
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase
from camcops_server.cc_modules.cc_validators import validate_task_tablename
from camcops_server.cc_modules.cc_task import Task
from camcops_server.tasks.apeq_cpft_perinatal import APEQCPFTPerinatal
from camcops_server.tasks.bmi import Bmi

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Unit testing
# =============================================================================


class TaskTests(DemoDatabaseTestCase):

    def test_query_phq9(self) -> None:
        self.announce("test_query_phq9")
        from camcops_server.tasks import Phq9

        phq9_query = self.dbsession.query(Phq9)
        results = phq9_query.all()
        log.info("{}", results)

    def test_all_tasks(self) -> None:
        self.announce("test_all_tasks")
        from datetime import date
        import hl7
        from sqlalchemy.sql.schema import Column
        from camcops_server.cc_modules.cc_ctvinfo import CtvInfo
        from camcops_server.cc_modules.cc_patient import Patient
        from camcops_server.cc_modules.cc_simpleobjects import (
            IdNumReference,
            TaskExportOptions,
        )
        from camcops_server.cc_modules.cc_snomed import (
            SnomedExpression,
        )
        from camcops_server.cc_modules.cc_string import APPSTRING_TASKNAME
        from camcops_server.cc_modules.cc_summaryelement import SummaryElement
        from camcops_server.cc_modules.cc_trackerhelpers import (
            TrackerInfo,
        )
        from camcops_server.cc_modules.cc_spreadsheet import (
            SpreadsheetPage,
        )
        from camcops_server.cc_modules.cc_xml import XmlElement

        user = UserFactory()

        subclasses = Task.all_subclasses_by_tablename()
        tables = [cls.tablename for cls in subclasses]
        log.info("Actual task table names: {!r} (n={})", tables, len(tables))
        req = self.req
        recipdef = self.recipdef
        dummy_data_factory = DummyDataInserter()
        task_doc_root = os.path.join(
            Path(__file__).resolve().parents[4], "docs", "source", "tasks"
        )
        export_options = TaskExportOptions(
            include_blobs=True,
            xml_include_ancillary=True,
            xml_include_calculated=True,
            xml_include_comments=True,
            xml_include_patient=True,
            xml_include_plain_columns=True,
            xml_include_snomed=True,
            xml_with_header_comments=True,
        )
        for cls in subclasses:
            log.info("Testing {}", cls)
            assert cls.extrastring_taskname != APPSTRING_TASKNAME
            q = self.dbsession.query(cls)
            t = q.first()  # type: Task

            self.assertIsNotNone(t, "Missing task!")

            # Name validity
            validate_task_tablename(t.tablename)

            # Core functions
            self.assertIsInstance(t.is_complete(), bool)
            self.assertIsInstance(t.get_task_html(req), str)
            for trackerinfo in t.get_trackers(req):
                self.assertIsInstance(trackerinfo, TrackerInfo)
            ctvlist = t.get_clinical_text(req)
            if ctvlist is not None:
                for ctvinfo in ctvlist:
                    self.assertIsInstance(ctvinfo, CtvInfo)
            for est in t.get_all_summary_tables(req):
                self.assertIsInstance(
                    est.get_spreadsheet_page(), SpreadsheetPage
                )
                self.assertIsInstance(est.get_xml_element(), XmlElement)

            self.assertIsInstance(t.has_patient, bool)
            self.assertIsInstance(t.is_anonymous, bool)
            self.assertIsInstance(t.has_clinician, bool)
            self.assertIsInstance(t.has_respondent, bool)
            self.assertIsInstance(t.tablename, str)
            for fn in t.get_fieldnames():
                self.assertIsInstance(fn, str)
            self.assertIsInstance(t.field_contents_valid(), bool)
            for msg in t.field_contents_invalid_because():
                self.assertIsInstance(msg, str)
            for fn in t.get_blob_fields():
                self.assertIsInstance(fn, str)

            self.assertIsInstance(t.pk, int)  # all our examples do have PKs
            self.assertIsInstance(t.is_preserved(), bool)
            self.assertIsInstance(t.was_forcibly_preserved(), bool)
            self.assertIsInstanceOrNone(t.get_creation_datetime(), Pendulum)
            self.assertIsInstanceOrNone(
                t.get_creation_datetime_utc(), Pendulum
            )
            self.assertIsInstanceOrNone(
                t.get_seconds_from_creation_to_first_finish(), float
            )

            self.assertIsInstance(t.get_adding_user_id(), int)
            self.assertIsInstance(t.get_adding_user_username(), str)
            self.assertIsInstance(t.get_removing_user_username(), str)
            self.assertIsInstance(t.get_preserving_user_username(), str)
            self.assertIsInstance(t.get_manually_erasing_user_username(), str)

            # Summaries
            for se in t.standard_task_summary_fields():
                self.assertIsInstance(se, SummaryElement)

            # SNOMED-CT
            if req.snomed_supported:
                for snomed_code in t.get_snomed_codes(req):
                    self.assertIsInstance(snomed_code, SnomedExpression)

            # Clinician
            self.assertIsInstance(t.get_clinician_name(), str)

            # Respondent
            self.assertIsInstance(t.is_respondent_complete(), bool)

            # Patient
            self.assertIsInstanceOrNone(t.patient, Patient)
            self.assertIsInstance(t.is_female(), bool)
            self.assertIsInstance(t.is_male(), bool)
            self.assertIsInstanceOrNone(t.get_patient_server_pk(), int)
            self.assertIsInstance(t.get_patient_forename(), str)
            self.assertIsInstance(t.get_patient_surname(), str)
            dob = t.get_patient_dob()
            assert (
                dob is None or isinstance(dob, date) or isinstance(dob, Date)
            )
            self.assertIsInstanceOrNone(t.get_patient_dob_first11chars(), str)
            self.assertIsInstance(t.get_patient_sex(), str)
            self.assertIsInstance(t.get_patient_address(), str)
            for idnum in t.get_patient_idnum_objects():
                self.assertIsInstance(
                    idnum.get_idnum_reference(), IdNumReference
                )
                self.assertIsInstance(idnum.is_superficially_valid(), bool)
                self.assertIsInstance(idnum.description(req), str)
                self.assertIsInstance(idnum.short_description(req), str)
                self.assertIsInstance(idnum.get_filename_component(req), str)

            # HL7 v2
            pidseg = t.get_patient_hl7_pid_segment(req, recipdef)
            assert isinstance(pidseg, str) or isinstance(pidseg, hl7.Segment)
            for dataseg in t.get_hl7_data_segments(req, recipdef):
                self.assertIsInstance(dataseg, hl7.Segment)
            for dataseg in t.get_hl7_extra_data_segments(recipdef):
                self.assertIsInstance(dataseg, hl7.Segment)

            # FHIR
            self.assertIsInstance(
                t.get_fhir_bundle(req, recipdef).as_json(), dict
            )  # the main test is not crashing!

            # Other properties
            self.assertIsInstance(t.is_erased(), bool)
            self.assertIsInstance(t.is_live_on_tablet(), bool)
            for attrname, col in t.gen_text_filter_columns():
                self.assertIsInstance(attrname, str)
                self.assertIsInstance(col, Column)

            # Views
            for page in t.get_spreadsheet_pages(req):
                self.assertIsInstance(page.get_tsv(), str)
            self.assertIsInstance(t.get_xml(req, export_options), str)
            self.assertIsInstance(t.get_html(req), str)
            self.assertIsInstance(t.get_pdf(req), bytes)
            self.assertIsInstance(t.get_pdf_html(req), str)
            self.assertIsInstance(t.suggested_pdf_filename(req), str)
            self.assertIsInstance(
                t.get_rio_metadata(
                    req,
                    which_idnum=1,
                    uploading_user_id=user.id,
                    document_type="some_doc_type",
                ),
                str,
            )

            # Help
            help_file = f"{t.help_url_basename()}.rst"
            task_help_file = os.path.join(task_doc_root, help_file)
            self.assertTrue(
                os.path.exists(task_help_file),
                msg=f"Task help not found at {task_help_file}",
            )

            # Special operations
            t.apply_special_note(
                req, "Debug: Special note! (1)", from_console=True
            )
            t.apply_special_note(
                req, "Debug: Special note! (2)", from_console=False
            )
            self.assertIsInstance(t.special_notes, list)
            t.cancel_from_export_log(req, from_console=True)
            t.cancel_from_export_log(req, from_console=False)

            # Insert random data and check it doesn't crash.
            dummy_data_factory.fill_in_task_fields(t)
            self.assertIsInstance(t.get_html(req), str)

            # Destructive special operations
            self.assertFalse(t.is_erased())
            t.manually_erase(req)
            self.assertTrue(t.is_erased())
            t.delete_entirely(req)


class GetPdfTests(TestCase):
    anonymised_text = "anonymised patient"
    anonymous_text = "anonymous task"
    formatted_date = "formatted date"
    missing_patient_text = "missing patient"
    mock_timestamp = "timestamp"
    page_counter_css = "page counter css"
    patient_text = "patient text"

    def setUp(self) -> None:
        super().setUp()

        self.request = mock.Mock(spec=CamcopsRequest)
        self.mock_timestamp_string = mock.Mock(spec=str)
        self.mock_format_datetime = mock.Mock()
        self.mock_timestamp_string.format.return_value = self.mock_timestamp
        self.mock_format_datetime.return_value = self.formatted_date

    def test_weasyprint_stylesheet_for_anonymous_task(self) -> None:
        task = APEQCPFTPerinatal()

        self.request.sstring.return_value = self.anonymous_text
        self.request.gettext.side_effect = [
            self.page_counter_css,
            self.mock_timestamp_string,
        ]

        mock_fn = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.cc_task",
            weasyprint_page_stylesheet=mock_fn,
            format_datetime=self.mock_format_datetime,
        ):
            task.get_weasyprint_stylesheet(self.request)

        mock_fn.assert_called_once_with(
            top_left_content=f'"{self.anonymous_text}"',
            bottom_left_content=self.mock_timestamp,
            bottom_right_content=self.page_counter_css,
        )
        self.request.sstring.assert_called_once_with(SS.ANONYMOUS_TASK)

        self.request.gettext.assert_has_calls(
            [
                mock.call('"Page " counter(page) " of " counter(pages)'),
                mock.call('"{task_shortname} created {timestamp}"'),
            ],
        )

    def test_weasyprint_stylesheet_for_anonymised_patient(self) -> None:
        task = Bmi()

        self.request.get_bool_param.return_value = True
        self.request.gettext.side_effect = [
            self.anonymised_text,
            self.page_counter_css,
            self.mock_timestamp_string,
        ]

        mock_fn = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.cc_task",
            weasyprint_page_stylesheet=mock_fn,
            format_datetime=self.mock_format_datetime,
        ):
            task.get_weasyprint_stylesheet(self.request)

        mock_fn.assert_called_once_with(
            top_left_content=f'"{self.anonymised_text}"',
            bottom_left_content=self.mock_timestamp,
            bottom_right_content=self.page_counter_css,
        )

        self.request.get_bool_param.assert_called_once_with(
            ViewParam.ANONYMISE, False
        )

        self.mock_timestamp_string.format.assert_called_with(
            task_shortname="BMI", timestamp=self.formatted_date
        )
        self.mock_format_datetime.assert_called_with(
            task.when_created, DateFormat.LONG_DATETIME
        )

        self.request.gettext.assert_has_calls(
            [
                mock.call("Patient details hidden at user’s request!"),
                mock.call('"Page " counter(page) " of " counter(pages)'),
                mock.call('"{task_shortname} created {timestamp}"'),
            ],
        )

    def test_weasyprint_stylesheet_for_patient(self) -> None:
        task = Bmi()
        task.patient = mock.Mock(spec=Patient)
        task.patient.prettystr.return_value = self.patient_text

        self.request.get_bool_param.return_value = False
        self.request.gettext.side_effect = [
            self.page_counter_css,
            self.mock_timestamp_string,
        ]

        mock_fn = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.cc_task",
            weasyprint_page_stylesheet=mock_fn,
            format_datetime=self.mock_format_datetime,
        ):
            task.get_weasyprint_stylesheet(self.request)

        mock_fn.assert_called_once_with(
            top_left_content=f'"{self.patient_text}"',
            bottom_left_content=self.mock_timestamp,
            bottom_right_content=self.page_counter_css,
        )
        task.patient.prettystr.assert_called_with(self.request)
        self.request.get_bool_param.assert_called_once_with(
            ViewParam.ANONYMISE, False
        )

        self.mock_timestamp_string.format.assert_called_with(
            task_shortname="BMI", timestamp=self.formatted_date
        )
        self.mock_format_datetime.assert_called_with(
            task.when_created, DateFormat.LONG_DATETIME
        )

        self.request.gettext.assert_has_calls(
            [
                mock.call('"Page " counter(page) " of " counter(pages)'),
                mock.call('"{task_shortname} created {timestamp}"'),
            ],
        )

    def test_weasyprint_stylesheet_for_missing_patient(self) -> None:
        task = Bmi()

        self.request.get_bool_param.return_value = False
        self.request.gettext.side_effect = [
            self.missing_patient_text,
            self.page_counter_css,
            self.mock_timestamp_string,
        ]

        mock_fn = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.cc_task",
            weasyprint_page_stylesheet=mock_fn,
            format_datetime=self.mock_format_datetime,
        ):
            task.get_weasyprint_stylesheet(self.request)

        mock_fn.assert_called_once_with(
            top_left_content=f'"{self.missing_patient_text}"',
            bottom_left_content=self.mock_timestamp,
            bottom_right_content=self.page_counter_css,
        )
        self.request.get_bool_param.assert_called_once_with(
            ViewParam.ANONYMISE, False
        )

        self.mock_timestamp_string.format.assert_called_with(
            task_shortname="BMI", timestamp=self.formatted_date
        )
        self.mock_format_datetime.assert_called_with(
            task.when_created, DateFormat.LONG_DATETIME
        )

        self.request.gettext.assert_has_calls(
            [
                mock.call("Missing patient!"),
                mock.call('"Page " counter(page) " of " counter(pages)'),
                mock.call('"{task_shortname} created {timestamp}"'),
            ],
        )
