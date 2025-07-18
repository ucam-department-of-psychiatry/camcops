"""
camcops_server/tasks/tests/edeq_tests.py

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

from unittest import mock, TestCase

from camcops_server.tasks.edeq import Edeq


class EdeqTests(TestCase):
    def test_restraint_subscale(self) -> None:
        edeq = Edeq()

        edeq.q1 = 1  # type: ignore[attr-defined]
        edeq.q2 = 2  # type: ignore[attr-defined]
        edeq.q3 = 3  # type: ignore[attr-defined]
        edeq.q4 = 4  # type: ignore[attr-defined]
        edeq.q5 = 6  # type: ignore[attr-defined]

        # 1 + 2 + 3 + 4 + 6 = 16
        # 16 / 5 = 3.2

        self.assertEqual(edeq.restraint(), 3.2)

    def test_subscale_none_if_answer_none(self) -> None:
        edeq = Edeq()

        edeq.q1 = None  # type: ignore[attr-defined]
        edeq.q2 = 2  # type: ignore[attr-defined]
        edeq.q3 = 3  # type: ignore[attr-defined]
        edeq.q4 = 4  # type: ignore[attr-defined]
        edeq.q5 = 6  # type: ignore[attr-defined]

        self.assertIsNone(edeq.restraint())

    def test_eating_concern_subscale(self) -> None:
        edeq = Edeq()

        edeq.q7 = 1  # type: ignore[attr-defined]
        edeq.q9 = 2  # type: ignore[attr-defined]
        edeq.q19 = 3  # type: ignore[attr-defined]
        edeq.q21 = 4  # type: ignore[attr-defined]
        edeq.q20 = 6  # type: ignore[attr-defined]

        # 1 + 2 + 3 + 4 + 6 = 16
        # 16 / 5 = 3.2

        self.assertEqual(edeq.eating_concern(), 3.2)

    def test_shape_concern_subscale(self) -> None:
        edeq = Edeq()

        edeq.q6 = 1  # type: ignore[attr-defined]
        edeq.q8 = 2  # type: ignore[attr-defined]
        edeq.q23 = 3  # type: ignore[attr-defined]
        edeq.q10 = 4  # type: ignore[attr-defined]
        edeq.q26 = 5  # type: ignore[attr-defined]
        edeq.q27 = 6  # type: ignore[attr-defined]
        edeq.q28 = 3  # type: ignore[attr-defined]
        edeq.q11 = 4  # type: ignore[attr-defined]

        # 1 + 2 + 3 + 4 + 5 + 6 + 3 + 4 = 28
        # 28 / 8 = 3.5

        self.assertEqual(edeq.shape_concern(), 3.5)

    def test_weight_concern_subscale(self) -> None:
        edeq = Edeq()

        edeq.q8 = 1  # type: ignore[attr-defined]
        edeq.q12 = 2  # type: ignore[attr-defined]
        edeq.q22 = 3  # type: ignore[attr-defined]
        edeq.q24 = 4  # type: ignore[attr-defined]
        edeq.q25 = 6  # type: ignore[attr-defined]

        # 1 + 2 + 3 + 4 + 6 = 16
        # 16 / 5 = 3.2

        self.assertEqual(edeq.weight_concern(), 3.2)

    def test_complete_when_all_answers_valid_for_female(self) -> None:
        edeq = Edeq()
        edeq.patient = mock.Mock(sex="F")

        for q_num in range(1, 28 + 1):
            setattr(edeq, f"q{q_num}", 0)

        edeq.mass_kg = 67.0  # type: ignore[attr-defined]
        edeq.height_m = 1.83  # type: ignore[attr-defined]

        edeq.num_periods_missed = 1  # type: ignore[attr-defined]
        edeq.pill = False  # type: ignore[attr-defined]

        self.assertTrue(edeq.is_complete())

    def test_incomplete_when_female_misses_female_questions(self) -> None:
        edeq = Edeq()
        edeq.patient = mock.Mock(sex="F")

        for q_num in range(1, 28 + 1):
            setattr(edeq, f"q{q_num}", 0)

        edeq.mass_kg = 67.0  # type: ignore[attr-defined]
        edeq.height_m = 1.83  # type: ignore[attr-defined]

        edeq.num_periods_missed = None  # type: ignore[attr-defined]
        edeq.pill = None  # type: ignore[attr-defined]

        self.assertFalse(edeq.is_complete())

    def test_complete_when_all_answers_valid_for_male(self) -> None:
        edeq = Edeq()
        edeq.patient = mock.Mock(sex="M")

        for q_num in range(1, 28 + 1):
            setattr(edeq, f"q{q_num}", 0)

        edeq.mass_kg = 67.0  # type: ignore[attr-defined]
        edeq.height_m = 1.83  # type: ignore[attr-defined]

        edeq.num_periods_missed = None  # type: ignore[attr-defined]
        edeq.pill = None  # type: ignore[attr-defined]

        self.assertTrue(edeq.is_complete())

    def test_is_complete_false_when_not_finished(self) -> None:
        edeq = Edeq()

        self.assertFalse(edeq.is_complete())

    def test_global_score_is_mean_of_subscales(self) -> None:
        edeq = Edeq()

        edeq.restraint = mock.Mock(return_value=1)  # type: ignore[method-assign]  # noqa: E501
        edeq.eating_concern = mock.Mock(return_value=2)  # type: ignore[method-assign]  # noqa: E501
        edeq.shape_concern = mock.Mock(return_value=3)  # type: ignore[method-assign]  # noqa: E501
        edeq.weight_concern = mock.Mock(return_value=4)  # type: ignore[method-assign]  # noqa: E501

        # (1 + 2 + 3 + 4) / 4
        self.assertEqual(edeq.global_score(), 2.5)

    def test_global_score_none_if_any_subscale_none(self) -> None:
        edeq = Edeq()

        edeq.restraint = mock.Mock(return_value=1)  # type: ignore[method-assign]  # noqa: E501
        edeq.eating_concern = mock.Mock(return_value=2)  # type: ignore[method-assign]  # noqa: E501
        edeq.shape_concern = mock.Mock(return_value=3)  # type: ignore[method-assign]  # noqa: E501
        edeq.weight_concern = mock.Mock(return_value=None)  # type: ignore[method-assign]  # noqa: E501

        self.assertIsNone(edeq.global_score())
