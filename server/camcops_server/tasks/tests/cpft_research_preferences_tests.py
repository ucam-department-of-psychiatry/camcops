#!/usr/bin/env python

"""
camcops_server/tasks/tests/cpft_research_preferences_tests.py

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

from camcops_server.tasks.cpft_research_preferences import (
    CpftResearchPreferences,
)


class CpftResearchPreferencesTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.request = mock.Mock()

    def test_complete_when_all_answers_valid(self) -> None:
        task = CpftResearchPreferences()

        task.contact_preference = "Y"
        task.contact_by_email = True
        task.research_opt_out = False

        self.assertTrue(task.is_complete())

    def test_complete_when_red_and_email_null(self) -> None:
        task = CpftResearchPreferences()

        task.contact_preference = "R"

        self.assertTrue(task.is_complete())

    def test_incomplete_when_contact_preference_null(self) -> None:
        task = CpftResearchPreferences()
        task.contact_by_email = True
        task.research_opt_out = False

        self.assertFalse(task.is_complete())

    def test_incomplete_when_yellow_and_email_null(self) -> None:
        task = CpftResearchPreferences()
        task.contact_preference = "Y"
        task.research_opt_out = False

        self.assertFalse(task.is_complete())

    def test_incomplete_when_any_field_invalid(self) -> None:
        all_fields = [
            "contact_preference",
            "contact_by_email",
            "research_opt_out",
        ]

        for invalid_field in all_fields:
            task = CpftResearchPreferences()

            task.contact_preference = "G"
            task.contact_by_email = True
            task.research_opt_out = False
            self.assertTrue(task.is_complete())

            setattr(task, invalid_field, 10.5)
            self.assertFalse(
                task.is_complete(),
                msg=f"Failed when setting {invalid_field} invalid",
            )
