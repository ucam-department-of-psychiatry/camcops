"""
camcops_server/tasks/tests/bmi_tests.py

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

from camcops_server.tasks.bmi import Bmi


class BmiTests(TestCase):
    def test_bmi_calculation_for_healthy_mass_and_height(self) -> None:
        bmi = Bmi()

        bmi.mass_kg = 70.0
        bmi.height_m = 1.83

        self.assertAlmostEqual(bmi.bmi(), 20.902, places=3)

    def test_bmi_none_for_zero_height(self) -> None:
        bmi = Bmi()

        bmi.mass_kg = 70.0
        bmi.height_m = 0

        self.assertIsNone(bmi.bmi())

    def test_bmi_none_when_not_complete(self) -> None:
        bmi = Bmi()

        self.assertIsNone(bmi.bmi())
