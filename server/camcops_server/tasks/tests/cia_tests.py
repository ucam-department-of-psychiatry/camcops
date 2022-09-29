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

    def test_not_complete_when_not_started(self) -> None:
        cia = Cia()

        self.assertFalse(cia.is_complete())

    def test_complete_when_all_mandatory_answers_valid(self) -> None:
        cia = Cia()

        for q_num in (1, 2, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16):
            setattr(cia, f"q{q_num}", 3)

        self.assertTrue(cia.is_complete())

    def test_max_global_score_for_all_answers(self) -> None:
        cia = Cia()

        for q_num in range(1, 16 + 1):
            setattr(cia, f"q{q_num}", 3)

        self.assertEqual(cia.global_score(), 48)

    def test_global_score_is_prorated_for_mandatory_questions(self) -> None:
        cia = Cia()

        for q_num in (1, 2, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16):
            setattr(cia, f"q{q_num}", 3)

        self.assertEqual(cia.global_score(), 48)

    def test_global_score_is_not_rated_when_mandatory_questions_not_answered(
        self,
    ) -> None:
        cia = Cia()

        for q_num in (3, 4, 7, 10):
            setattr(cia, f"q{q_num}", 3)

        self.assertIsNone(cia.global_score())

    def test_global_score_is_not_rated_for_any_unanswered_questions(
        self,
    ) -> None:
        cia = Cia()

        self.assertIsNone(cia.global_score())
