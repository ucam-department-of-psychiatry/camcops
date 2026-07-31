"""
camcops_server/cc_modules/tests/cc_tracker_tests.py

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

from unittest import mock, TestCase

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_simpleobjects import IdNumReference
from camcops_server.cc_modules.cc_taskcollection import TaskFilter
from camcops_server.cc_modules.cc_tracker import ClinicalTextView, Tracker
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase

# =============================================================================
# Unit tests
# =============================================================================


class TrackerCtvTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def setUp(self) -> None:
        super().setUp()

        self.taskfilter = TaskFilter()

        idnum_ref = IdNumReference(which_idnum=0, idnum_value=0)

        self.taskfilter.idnum_criteria = [idnum_ref]
        self.taskfilter.tasks_with_patient_only = True

    def test_tracker(self) -> None:
        self.announce("test_tracker")
        req = self.req
        t = Tracker(req, self.taskfilter)

        self.assertIsInstance(t.get_html(), str)
        self.assertIsInstance(t.get_pdf(), bytes)
        self.assertIsInstance(t.get_pdf_html(), str)
        self.assertIsInstance(t.get_xml(), str)
        self.assertIsInstance(t.suggested_pdf_filename(), str)

    def test_ctv(self) -> None:
        self.announce("test_ctv")
        req = self.req
        c = ClinicalTextView(req, self.taskfilter)

        self.assertIsInstance(c.get_html(), str)
        self.assertIsInstance(c.get_pdf(), bytes)
        self.assertIsInstance(c.get_pdf_html(), str)
        self.assertIsInstance(c.get_xml(), str)
        self.assertIsInstance(c.suggested_pdf_filename(), str)


class TestTracker(Tracker):
    def __init__(
        self,
        req: "CamcopsRequest",
        taskfilter: TaskFilter,
        via_index: bool = True,
    ) -> None:
        # Stub out unwanted stuff in constructor
        self.request = req
        self.as_ctv = False


class TestCtv(ClinicalTextView):
    def __init__(
        self,
        req: "CamcopsRequest",
        taskfilter: TaskFilter,
        via_index: bool = True,
    ) -> None:
        # Stub out unwanted stuff in constructor
        self.request = req
        self.as_ctv = True


class GetPdfTests(TestCase):
    ctv_text = "ctv text"
    formatted_date = "formatted date"
    missing_patient_text = "missing patient"
    mock_timestamp = "timestamp"
    page_counter_css = "page counter css"
    patient_text = "patient text"
    tracker_text = "tracker text"

    def setUp(self) -> None:
        super().setUp()

        self.request = mock.Mock(spec=CamcopsRequest)
        self.task_filter = mock.Mock(spec=TaskFilter)
        self.mock_timestamp_string = mock.Mock(spec=str)
        self.mock_format_datetime = mock.Mock()
        self.mock_timestamp_string.format.return_value = self.mock_timestamp
        self.mock_format_datetime.return_value = self.formatted_date

    def test_weasyprint_stylesheet_for_ctv(self) -> None:
        ctv = TestCtv(self.request, self.task_filter)
        ctv.patient = mock.Mock(spec=Patient)
        ctv.patient.prettystr.return_value = self.patient_text
        self.request.gettext.side_effect = [
            self.page_counter_css,
            self.mock_timestamp_string,
            self.ctv_text,
        ]

        mock_fn = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.cc_tracker",
            weasyprint_page_stylesheet=mock_fn,
            format_datetime=self.mock_format_datetime,
        ):
            ctv.get_weasyprint_stylesheet(self.request)

        mock_fn.assert_called_once_with(
            top_left_content=f'"{self.patient_text}"',
            bottom_left_content=self.mock_timestamp,
            bottom_right_content=self.page_counter_css,
        )
        ctv.patient.prettystr.assert_called_with(self.request)

        self.mock_timestamp_string.format.assert_called_with(
            label=self.ctv_text, timestamp=self.formatted_date
        )
        self.mock_format_datetime.assert_called_with(
            self.request.now, DateFormat.LONG_DATETIME
        )

        self.request.gettext.assert_has_calls(
            [
                mock.call('"Page " counter(page) " of " counter(pages)'),
                mock.call('"{label} accessed {timestamp}"'),
                mock.call("CTV"),
            ],
        )

    def test_weasyprint_stylesheet_for_tracker(self) -> None:
        tracker = TestTracker(self.request, self.task_filter)
        tracker.patient = mock.Mock(spec=Patient)
        tracker.patient.prettystr.return_value = self.patient_text
        self.request.gettext.side_effect = [
            self.page_counter_css,
            self.mock_timestamp_string,
            self.tracker_text,
        ]

        mock_fn = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.cc_tracker",
            weasyprint_page_stylesheet=mock_fn,
            format_datetime=self.mock_format_datetime,
        ):
            tracker.get_weasyprint_stylesheet(self.request)

        mock_fn.assert_called_once_with(
            top_left_content=f'"{self.patient_text}"',
            bottom_left_content=self.mock_timestamp,
            bottom_right_content=self.page_counter_css,
        )
        tracker.patient.prettystr.assert_called_with(self.request)

        self.mock_timestamp_string.format.assert_called_with(
            label=self.tracker_text, timestamp=self.formatted_date
        )
        self.mock_format_datetime.assert_called_with(
            self.request.now, DateFormat.LONG_DATETIME
        )

        self.request.gettext.assert_has_calls(
            [
                mock.call('"Page " counter(page) " of " counter(pages)'),
                mock.call('"{label} accessed {timestamp}"'),
                mock.call("Tracker"),
            ],
        )

    def test_weasyprint_stylesheet_for_missing_patient(self) -> None:
        ctv = TestCtv(self.request, self.task_filter)
        ctv.patient = None
        self.request.gettext.side_effect = [
            self.missing_patient_text,
            self.page_counter_css,
            self.mock_timestamp_string,
            self.ctv_text,
        ]

        mock_fn = mock.Mock()
        with mock.patch.multiple(
            "camcops_server.cc_modules.cc_tracker",
            weasyprint_page_stylesheet=mock_fn,
            format_datetime=self.mock_format_datetime,
        ):
            ctv.get_weasyprint_stylesheet(self.request)

        mock_fn.assert_called_once_with(
            top_left_content=f'"{self.missing_patient_text}"',
            bottom_left_content=self.mock_timestamp,
            bottom_right_content=self.page_counter_css,
        )

        self.mock_timestamp_string.format.assert_called_with(
            label=self.ctv_text, timestamp=self.formatted_date
        )
        self.mock_format_datetime.assert_called_with(
            self.request.now, DateFormat.LONG_DATETIME
        )

        self.request.gettext.assert_has_calls(
            [
                mock.call("Missing patient!"),
                mock.call('"Page " counter(page) " of " counter(pages)'),
                mock.call('"{label} accessed {timestamp}"'),
                mock.call("CTV"),
            ],
        )
