#!/usr/bin/env python

"""
camcops_server/tasks/tests/cia_tests.py

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

from camcops_server.tasks.cia import Cia


class CiaTests(TestCase):
    def test_complete_when_all_answers_valid(self) -> None:
        cia = Cia()

        for q_num in range(1, 16 + 1):
            setattr(cia, f"q{q_num}", 0)

        self.assertTrue(cia.is_complete())

    def test_is_complete_false_when_not_finished(self) -> None:
        cia = Cia()

        self.assertFalse(cia.is_complete())

    def test_max_global_score_for_all_answers(self) -> None:
        cia = Cia()

        for q_num in range(1, 16 + 1):
            setattr(cia, f"q{q_num}", 3)

        self.assertEqual(cia.global_score(), 48)

    def test_global_score_is_prorated_for_applicable_questions(self) -> None:
        cia = Cia()

        for q_num in range(1, 12 + 1):
            setattr(cia, f"q{q_num}", 3)

        for q_num in range(13, 16 + 1):
            setattr(cia, f"q{q_num}", Cia.NOT_APPLICABLE)

        self.assertEqual(cia.global_score(), 48)

    def test_global_score_is_not_rated_for_less_than_12_questions(
        self,
    ) -> None:
        cia = Cia()

        for q_num in range(1, 11 + 1):
            setattr(cia, f"q{q_num}", 3)

        for q_num in range(12, 16 + 1):
            setattr(cia, f"q{q_num}", Cia.NOT_APPLICABLE)

        self.assertIsNone(cia.global_score())

    def test_global_score_is_not_rated_for_any_unanswered_questions(
        self,
    ) -> None:
        cia = Cia()

        self.assertIsNone(cia.global_score())
