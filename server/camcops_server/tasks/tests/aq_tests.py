"""
camcops_server/tasks/tests/aq_tests.py

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

from camcops_server.tasks.aq import Aq


class AqTests(TestCase):
    AGREE_SCORING_QUESTIONS = [
        2,
        4,
        5,
        6,
        7,
        9,
        12,
        13,
        16,
        18,
        19,
        20,
        21,
        22,
        23,
        26,
        33,
        35,
        39,
        41,
        42,
        43,
        45,
        46,
    ]

    DISAGREE_SCORING_QUESTIONS = [
        1,
        3,
        8,
        10,
        11,
        14,
        15,
        17,
        24,
        25,
        27,
        28,
        29,
        30,
        31,
        32,
        34,
        36,
        37,
        38,
        40,
        44,
        47,
        48,
        49,
        50,
    ]

    def test_max_score_is_50(self):
        aq = Aq()
        for q_num in self.AGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", 0)

        for q_num in self.DISAGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", 2)

        self.assertEqual(aq.score(), 50)

    def test_min_score_is_0(self):
        aq = Aq()

        for q_num in self.AGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", 2)

        for q_num in self.DISAGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", 0)

        self.assertEqual(aq.score(), 0)

    def test_incomplete_when_answers_missing(self):
        aq = Aq()

        self.assertFalse(aq.is_complete())

    def test_complete_when_all_answered(self):
        aq = Aq()

        for q_num in range(1, 50 + 1):
            setattr(aq, f"q{q_num}", 0)

        self.assertTrue(aq.is_complete())
