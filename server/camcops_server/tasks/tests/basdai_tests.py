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

from unittest import mock, TestCase

from camcops_server.tasks.basdai import Basdai


# =============================================================================
# Unit tests
# =============================================================================


class BasdaiTests(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.request = mock.Mock()

    def test_basdai_calculation(self) -> None:
        basdai = Basdai()

        basdai.q1 = 2  # type: ignore[attr-defined]
        basdai.q2 = 10  # type: ignore[attr-defined]
        basdai.q3 = 7  # type: ignore[attr-defined]
        basdai.q4 = 1  # type: ignore[attr-defined]

        basdai.q5 = 9  # type: ignore[attr-defined]
        basdai.q6 = 3  # type: ignore[attr-defined]

        # 2 + 10 + 7 + 1 = 20
        # (9 + 3) / 2 = 6
        # 20 + 6 = 26
        # 26 / 5 = 5.2

        self.assertEqual(basdai.basdai(), 5.2)

    def test_basdai_none_when_field_none(self) -> None:
        basdai = Basdai()

        self.assertIsNone(basdai.basdai())

    def test_basdai_complete_when_all_answers_valid(self) -> None:
        basdai = Basdai()

        basdai.q1 = 0  # type: ignore[attr-defined]
        basdai.q2 = 0  # type: ignore[attr-defined]
        basdai.q3 = 0  # type: ignore[attr-defined]
        basdai.q4 = 0  # type: ignore[attr-defined]

        basdai.q5 = 0  # type: ignore[attr-defined]
        basdai.q6 = 0  # type: ignore[attr-defined]

        self.assertTrue(basdai.is_complete())

    def test_basdai_incomplete_when_a_field_none(self) -> None:
        basdai = Basdai()

        basdai.q1 = None  # type: ignore[attr-defined]
        basdai.q2 = 0  # type: ignore[attr-defined]
        basdai.q3 = 0  # type: ignore[attr-defined]
        basdai.q4 = 0  # type: ignore[attr-defined]

        basdai.q5 = 0  # type: ignore[attr-defined]
        basdai.q6 = 0  # type: ignore[attr-defined]

        self.assertFalse(basdai.is_complete())

    def test_basdai_incomplete_when_a_field_invalid(self) -> None:
        basdai = Basdai()

        basdai.q1 = 11  # type: ignore[attr-defined]
        basdai.q2 = 0  # type: ignore[attr-defined]
        basdai.q3 = 0  # type: ignore[attr-defined]
        basdai.q4 = 0  # type: ignore[attr-defined]

        basdai.q5 = 0  # type: ignore[attr-defined]
        basdai.q6 = 0  # type: ignore[attr-defined]

        self.assertFalse(basdai.is_complete())

    def test_activity_state_qmark_for_none(self) -> None:
        basdai = Basdai()

        with mock.patch.object(basdai, "basdai") as mock_basdai:
            mock_basdai.return_value = None
            self.assertEqual(basdai.activity_state(self.request), "?")

    def test_activity_state_inactive_for_less_than_4(self) -> None:
        basdai = Basdai()

        with mock.patch.object(basdai, "basdai") as mock_basdai:
            mock_basdai.return_value = 3.8
            with mock.patch.object(basdai, "wxstring") as mock_wxstring:
                basdai.activity_state(self.request)

        mock_wxstring.assert_called_once_with(self.request, "inactive")

    def test_activity_state_active_for_4(self) -> None:
        basdai = Basdai()

        with mock.patch.object(basdai, "basdai") as mock_basdai:
            mock_basdai.return_value = 4
            with mock.patch.object(basdai, "wxstring") as mock_wxstring:
                basdai.activity_state(self.request)

        mock_wxstring.assert_called_once_with(self.request, "active")
