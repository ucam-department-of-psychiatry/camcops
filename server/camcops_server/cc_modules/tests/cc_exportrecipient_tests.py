"""
camcops_server/cc_modules/tests/cc_exportrecipient_tests.py

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

from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.cc_modules.cc_testfactories import ExportRecipientFactory


class ExportRecipientTests(DemoRequestTestCase):
    def test_there_can_only_be_one_current_recipient(self) -> None:
        recipient_1 = ExportRecipientFactory(
            current=True, recipient_name="test"
        )
        self.assertTrue(recipient_1.current)
        recipient_2 = ExportRecipientFactory(
            current=True, recipient_name="test"
        )
        self.assertTrue(recipient_2.current)
        self.assertFalse(recipient_1.current)
