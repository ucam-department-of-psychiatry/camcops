#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_formatter.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

**Safe alternative to str.format() that rejects anything not in the list of
  allowed keys.**

"""

from string import Formatter
from unittest import TestCase

from typing import Any, Mapping, Sequence


class SafeFormatter(Formatter):
    def __init__(self, allowed_keys: Sequence[str]) -> None:
        self._allowed_keys = allowed_keys

        super().__init__()

    def get_valid_parameters_string(self) -> str:
        return ", ".join(f"{{{k}}}" for k in self._allowed_keys)

    def get_field(self, field_name: str, args: Sequence[Any],
                  kwargs: Mapping[str, Any]):
        if field_name not in self._allowed_keys:
            raise KeyError(field_name)

        return super().get_field(field_name, args, kwargs)

    def validate(self, format_string: str) -> None:
        # Raises KeyError for unknown key or ValueError for
        # unmatched {

        test_dict = {k: "" for k in self._allowed_keys}

        self.format(format_string, **test_dict)


class SafeFormatterTests(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.formatter = SafeFormatter(["forename", "surname", "email"])

    def test_formats_with_allowed_keys(self) -> None:
        output = self.formatter.format("{forename} {surname} <{email}>",
                                       forename="Erin", surname="Byrne",
                                       email="erin.byrne@example.com")
        self.assertEqual(output, "Erin Byrne <erin.byrne@example.com>")

    def test_format_raises_with_disallowed_keys(self) -> None:
        with self.assertRaises(KeyError):
            self.formatter.format("{email.__class__}")

    def test_returns_valid_parameters_string(self) -> None:
        self.assertEqual(self.formatter.get_valid_parameters_string(),
                         "{forename}, {surname}, {email}")

    def test_validate_raises_key_error_for_unknown_key(self) -> None:
        with self.assertRaises(KeyError):
            self.formatter.validate("{phone}")

    def test_validate_raises_value_error_for_mismatched_brackets(self) -> None:
        with self.assertRaises(ValueError):
            self.formatter.validate("{forename")
