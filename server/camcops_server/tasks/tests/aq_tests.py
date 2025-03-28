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

    ALL_QUESTIONS = range(1, 50 + 1)

    DEFINITELY_AGREE = 0
    DEFINITELY_DISAGREE = 3

    SOCIAL_SKILL_QUESTIONS = [1, 11, 13, 15, 22, 36, 44, 45, 47, 48]
    ATTENTION_SWITCHING_QUESTIONS = [2, 4, 10, 16, 25, 32, 34, 37, 43, 46]
    ATTENTION_TO_DETAIL_QUESTIONS = [5, 6, 9, 12, 19, 23, 28, 29, 30, 49]
    COMMUNICATION_QUESTIONS = [7, 17, 18, 26, 27, 31, 33, 35, 38, 39]
    IMAGINATION_QUESTIONS = [3, 8, 14, 20, 21, 24, 40, 41, 42, 50]

    def test_max_score_is_50(self) -> None:
        aq = Aq()
        for q_num in self.AGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_AGREE)

        for q_num in self.DISAGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_DISAGREE)

        self.assertEqual(aq.score(), 50)

    def test_min_score_is_0(self) -> None:
        aq = Aq()

        for q_num in self.AGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_DISAGREE)

        for q_num in self.DISAGREE_SCORING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_AGREE)

        self.assertEqual(aq.score(), 0)

    def test_score_is_none_if_any_none(self) -> None:
        aq = Aq()

        for q_num in self.ALL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_AGREE)

        aq.q1 = None  # type: ignore[attr-defined]

        self.assertIsNone(aq.score())

    def test_incomplete_when_answers_missing(self) -> None:
        aq = Aq()

        self.assertFalse(aq.is_complete())

    def test_complete_when_all_answered(self) -> None:
        aq = Aq()

        for q_num in self.ALL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.DEFINITELY_AGREE)

        self.assertTrue(aq.is_complete())

    def test_social_skill_score_is_none_if_any_none(self) -> None:
        aq = Aq()

        for q_num in self.SOCIAL_SKILL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.non_scoring_answer(q_num))

        aq.q1 = None  # type: ignore[attr-defined]

        self.assertIsNone(aq.social_skill_score())

    def test_min_social_skill_score_is_0(self) -> None:
        aq = Aq()

        for q_num in self.SOCIAL_SKILL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.non_scoring_answer(q_num))

        self.assertEqual(aq.social_skill_score(), 0)

    def test_max_social_skill_score_is_10(self) -> None:
        aq = Aq()

        for q_num in self.SOCIAL_SKILL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.scoring_answer(q_num))

        self.assertEqual(aq.social_skill_score(), 10)

    def test_min_attention_switching_score_is_0(self) -> None:
        aq = Aq()

        for q_num in self.ATTENTION_SWITCHING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.non_scoring_answer(q_num))

        self.assertEqual(aq.attention_switching_score(), 0)

    def test_max_attention_switching_score_is_10(self) -> None:
        aq = Aq()

        for q_num in self.ATTENTION_SWITCHING_QUESTIONS:
            setattr(aq, f"q{q_num}", self.scoring_answer(q_num))

        self.assertEqual(aq.attention_switching_score(), 10)

    def test_min_attention_to_detail_score_is_0(self) -> None:
        aq = Aq()

        for q_num in self.ATTENTION_TO_DETAIL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.non_scoring_answer(q_num))

        self.assertEqual(aq.attention_to_detail_score(), 0)

    def test_max_attention_to_detail_score_is_10(self) -> None:
        aq = Aq()

        for q_num in self.ATTENTION_TO_DETAIL_QUESTIONS:
            setattr(aq, f"q{q_num}", self.scoring_answer(q_num))

        self.assertEqual(aq.attention_to_detail_score(), 10)

    def test_min_communication_score_is_0(self) -> None:
        aq = Aq()

        for q_num in self.COMMUNICATION_QUESTIONS:
            setattr(aq, f"q{q_num}", self.non_scoring_answer(q_num))

        self.assertEqual(aq.communication_score(), 0)

    def test_max_communication_score_is_10(self) -> None:
        aq = Aq()

        for q_num in self.COMMUNICATION_QUESTIONS:
            setattr(aq, f"q{q_num}", self.scoring_answer(q_num))

        self.assertEqual(aq.communication_score(), 10)

    def test_min_imagination_score_is_0(self) -> None:
        aq = Aq()

        for q_num in self.IMAGINATION_QUESTIONS:
            setattr(aq, f"q{q_num}", self.non_scoring_answer(q_num))

        self.assertEqual(aq.imagination_score(), 0)

    def test_max_imagination_score_is_10(self) -> None:
        aq = Aq()

        for q_num in self.IMAGINATION_QUESTIONS:
            setattr(aq, f"q{q_num}", self.scoring_answer(q_num))

        self.assertEqual(aq.imagination_score(), 10)

    def non_scoring_answer(self, q_num: int) -> int:
        if q_num in self.AGREE_SCORING_QUESTIONS:
            return self.DEFINITELY_DISAGREE

        return self.DEFINITELY_AGREE

    def scoring_answer(self, q_num: int) -> int:
        if q_num in self.AGREE_SCORING_QUESTIONS:
            return self.DEFINITELY_AGREE

        return self.DEFINITELY_DISAGREE
