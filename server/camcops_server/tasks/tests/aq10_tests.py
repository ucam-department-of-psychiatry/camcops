"""
camcops_server/tasks/tests/aq10_tests.py

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

from camcops_server.tasks.aq10 import Aq10


class AqTests(TestCase):
    AGREE_SCORING_QUESTIONS = [1, 7, 8, 10]

    DISAGREE_SCORING_QUESTIONS = [2, 3, 4, 5, 6, 9]

    ALL_QUESTIONS = range(1, 50 + 1)

    DEFINITELY_AGREE = 0
    DEFINITELY_DISAGREE = 3

    def test_max_score_is_10(self) -> None:
        aq = Aq10()
        for q_num in self.AGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_AGREE)

        for q_num in self.DISAGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_DISAGREE)

        self.assertEqual(aq.score(), 50)

    def test_min_score_is_0(self) -> None:
        aq = Aq10()

        for q_num in self.AGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_DISAGREE)

        for q_num in self.DISAGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_AGREE)

        self.assertEqual(aq.score(), 0)

    def test_score_is_none_if_any_none(self) -> None:
        aq = Aq10()

        for q_num in self.ALL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_AGREE)

        aq.q1 = None  # type: ignore[attr-defined]

        self.assertIsNone(aq.score())

    def test_incomplete_when_answers_missing(self) -> None:
        aq = Aq10()

        self.assertFalse(aq.is_complete())

    def test_complete_when_all_answered(self) -> None:
        aq = Aq10()

        for q_num in self.ALL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_AGREE)

        self.assertTrue(aq.is_complete())
