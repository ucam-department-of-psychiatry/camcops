"""camcops_server/cc_modules/tests/cc_pdf_tests.py

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

from camcops_server.cc_modules.cc_pdf import weasyprint_page_stylesheet


class WeasyprintPageStylesheetTests(TestCase):
    def test_content_appears_in_css(self) -> None:
        mock_css_object = mock.Mock()
        mock_css_class = mock.Mock(return_value=mock_css_object)

        with mock.patch.multiple(
            "camcops_server.cc_modules.cc_pdf",
            CSS=mock_css_class,
        ):
            ret = weasyprint_page_stylesheet(
                top_left_content="top left",
                top_right_content="top right",
                bottom_left_content="bottom left",
                bottom_right_content="bottom right",
            )

        self.assertEqual(ret, mock_css_object)
        string = mock_css_class.call_args.kwargs["string"]

        self.assertIn("top left", string)
        self.assertIn("top right", string)
        self.assertIn("bottom left", string)
        self.assertIn("bottom right", string)
