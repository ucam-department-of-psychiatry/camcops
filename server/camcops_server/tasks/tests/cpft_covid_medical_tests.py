#!/usr/bin/env python

"""
camcops_server/tasks/tests/cpft_covid_medical_tests.py

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

from unittest import mock
import unittest

from camcops_server.tasks.cpft_covid_medical import CpftCovidMedical


class CpftCovidMedicalTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.request = mock.Mock()

    def test_complete_when_all_answers_valid(self) -> None:
        task = CpftCovidMedical()

        task.how_and_when_symptoms = 0

        self.assertTrue(task.is_complete())

    def test_incomplete_when_symptoms_null(self) -> None:
        task = CpftCovidMedical()

        self.assertFalse(task.is_complete())

    def test_incomplete_when_any_field_invalid(self) -> None:
        all_fields = ["how_and_when_symptoms"]

        for invalid_field in all_fields:
            task = CpftCovidMedical()

            for field in all_fields:
                setattr(task, field, 0)

            self.assertTrue(task.is_complete())

            setattr(task, invalid_field, 10.5)
            self.assertFalse(
                task.is_complete(),
                msg=f"Failed when setting {invalid_field} invalid",
            )
