"""
camcops_server/cc_modules/tests/cc_exportrecipientinfo_tests.py

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

from unittest import TestCase

from camcops_server.cc_modules.cc_exportrecipientinfo import (
    ExportRecipientInfo,
)


class ExportRecipientInfoTests(TestCase):
    def test_objects_with_same_attributes_equal(self) -> None:
        info_1 = ExportRecipientInfo()
        info_2 = ExportRecipientInfo(other=info_1)

        self.assertEqual(info_1, info_2)

    def test_objects_with_different_attributes_not_equal(self) -> None:
        info_1 = ExportRecipientInfo()
        info_1.recipient_name = "name 1"
        info_2 = ExportRecipientInfo()
        info_1.recipient_name = "name 2"

        self.assertNotEqual(info_1, info_2)

    def test_objects_with_different_ignored_attributes_equal(self) -> None:
        info_1 = ExportRecipientInfo()
        info_1.email_host_password = "password 1"
        info_2 = ExportRecipientInfo(other=info_1)
        info_2.email_host_password = "password 2"

        self.assertEqual(info_1, info_2)

    def test_non_export_recipient_not_equal(self) -> None:
        info_1 = ExportRecipientInfo()

        self.assertNotEqual(info_1, "not a recipient")
