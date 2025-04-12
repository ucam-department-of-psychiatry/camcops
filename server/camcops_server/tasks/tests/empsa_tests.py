"""
camcops_server/tasks/tests/empsa_tests.py

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

from camcops_server.tasks.empsa import Empsa


class EmpsaTests(TestCase):
    def test_complete_when_all_questions_answered(self) -> None:
        empsa = Empsa()

        for field in empsa.ALL_MANDATORY_FIELD_NAMES:
            setattr(empsa, field, 1)

        self.assertTrue(empsa.is_complete())

    def test_not_complete_when_not_all_questions_answered(self) -> None:
        empsa = Empsa()

        empsa.q1_ability = None

        self.assertFalse(empsa.is_complete())
