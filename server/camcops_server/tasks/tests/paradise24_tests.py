#!/usr/bin/env python

"""
camcops_server/tasks/tests/paradise24_tests.py

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

from camcops_server.tasks.paradise24 import Paradise24


class Paradise24Tests(TestCase):
    def test_complete_when_all_answers_valid(self) -> None:
        paradise24 = Paradise24()

        for q_num in range(1, 24 + 1):
            setattr(paradise24, f"q{q_num}", 0)

        self.assertTrue(paradise24.is_complete())

    def test_is_complete_false_when_not_finished(self) -> None:
        paradise24 = Paradise24()

        self.assertFalse(paradise24.is_complete())

    def test_total_score_none_when_not_complete(self) -> None:
        paradise24 = Paradise24()

        self.assertIsNone(paradise24.total_score())

    def test_total_score_is_sum_of_all_answers(self) -> None:
        paradise24 = Paradise24()

        for q_num in range(1, 24 + 1):
            setattr(paradise24, f"q{q_num}", 2)

        self.assertEqual(paradise24.total_score(), 48)

    def test_metric_score_derived_from_total(self) -> None:
        paradise24 = Paradise24()

        # Not an exhaustive test of all values as that would not be
        # particularly useful. Enough to check the lookup
        # is working.
        paradise24.total_score = mock.Mock(return_value=48)
        self.assertEqual(paradise24.metric_score(), 100)

        paradise24.total_score = mock.Mock(return_value=24)
        self.assertEqual(paradise24.metric_score(), 64)

        paradise24.total_score = mock.Mock(return_value=0)
        self.assertEqual(paradise24.metric_score(), 0)

        paradise24.total_score = mock.Mock(return_value=None)
        self.assertIsNone(paradise24.metric_score())
