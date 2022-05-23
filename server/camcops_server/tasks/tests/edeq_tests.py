#!/usr/bin/env python

"""
camcops_server/tasks/tests/basdai_tests.py

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

from camcops_server.tasks.edeq import Edeq


class EdeqTests(TestCase):
    def test_restraint_subscale(self):
        edeq = Edeq()

        edeq.q1 = 1
        edeq.q2 = 2
        edeq.q3 = 3
        edeq.q4 = 4
        edeq.q5 = 6

        # 1 + 2 + 3 + 4 + 6 = 16
        # 16 / 5 = 3.2

        self.assertEqual(edeq.restraint(), 3.2)

    def test_eating_concern_subscale(self):
        edeq = Edeq()

        edeq.q7 = 1
        edeq.q9 = 2
        edeq.q19 = 3
        edeq.q21 = 4
        edeq.q20 = 6

        # 1 + 2 + 3 + 4 + 6 = 16
        # 16 / 5 = 3.2

        self.assertEqual(edeq.eating_concern(), 3.2)

    def test_complete_when_all_answers_valid(self) -> None:
        edeq = Edeq()

        for q_num in range(1, 28 + 1):
            setattr(edeq, f"q{q_num}", 0)

        edeq.q_weight = 67.0
        edeq.q_height = 1.83

        # TODO Male / Female differences
        # number of periods optional
        edeq.q_num_periods_missed = 1
        edeq.q_pill = False

        self.assertTrue(edeq.is_complete())

    def test_is_complete_false_when_not_finished(self) -> None:
        edeq = Edeq()

        self.assertFalse(edeq.is_complete())
