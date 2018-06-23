#!/usr/bin/env python
# camcops_server/cc_modules/cc_tsv.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
"""

from collections import OrderedDict
import logging
from typing import Any, Dict, List, Union

from cardinal_pythonlib.logs import BraceStyleAdapter

from .cc_convert import tsv_escape

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# TSV output holding structures
# =============================================================================

class TsvPage(object):
    def __init__(self, name: str,
                 rows: List[Union[Dict[str, Any], OrderedDict]]) -> None:
        assert name, "Missing name"
        self.name = name
        self.rows = rows
        self.headings = []  # type: List[str]
        for row in rows:
            self._add_headings_if_absent(row.keys())

    def __str__(self) -> str:
        return "TsvPage: name={}\n{}\n".format(self.name, self.get_tsv())

    @property
    def empty(self) -> bool:
        return len(self.rows) == 0

    def _add_headings_if_absent(self, headings: List[str]) -> None:
        for h in headings:
            if h not in self.headings:
                self.headings.append(h)

    def add_or_set_value(self, heading: str, value: Any) -> None:
        assert len(self.rows) == 1, "add_value can only be used if #row == 1"
        self._add_headings_if_absent([heading])
        self.rows[0][heading] = value

    def add_or_set_column(self, heading: str, values: List[Any]) -> None:
        assert len(values) == len(self.rows), "#values != #existing rows"
        self._add_headings_if_absent([heading])
        for i, row in enumerate(self.rows):
            row[heading] = values[i]

    def add_or_set_columns_from_page(self, other: "TsvPage") -> None:
        assert len(self.rows) == len(other.rows), "Mismatched #rows"
        self._add_headings_if_absent(other.headings)
        for i, row in enumerate(self.rows):
            for k, v in other.rows[i].items():
                row[k] = v

    def add_rows_from_page(self, other: "TsvPage") -> None:
        self._add_headings_if_absent(other.headings)
        self.rows.extend(other.rows)

    def sort_headings(self) -> None:
        self.headings.sort()

    def get_tsv_headings(self) -> str:
        return "\t".join(tsv_escape(h) for h in self.headings)

    def get_tsv_row(self, rownum: int) -> str:
        assert 0 <= rownum < len(self.rows)
        row = self.rows[rownum]  # type: OrderedDict
        values = [tsv_escape(row.get(h)) for h in self.headings]
        return "\t".join(values)

    def get_tsv(self) -> str:
        lines = (
            [self.get_tsv_headings()] +
            [self.get_tsv_row(i) for i in range(len(self.rows))]
        )
        return "\n".join(lines)


class TsvCollection(object):
    def __init__(self) -> None:
        self.pages = []  # type: List[TsvPage]

    def __str__(self) -> str:
        return (
            "TsvCollection:\n" +
            "\n\n".join(page.get_tsv() for page in self.pages)
        )

    def page_with_name(self, page_name: str) -> TsvPage:
        return next((page for page in self.pages if page.name == page_name),
                    None)

    def add_page(self, page: TsvPage) -> None:
        if page.empty:
            return
        existing_page = self.page_with_name(page.name)
        if existing_page:
            # Blend with existing page
            existing_page.add_rows_from_page(page)
        else:
            # New page
            self.pages.append(page)

    def add_pages(self, pages: List[TsvPage]) -> None:
        for page in pages:
            self.add_page(page)

    def sort_headings_within_all_pages(self) -> None:
        for page in self.pages:
            page.sort_headings()

    def sort_pages(self) -> None:
        self.pages.sort(key=lambda p: p.name)

    def get_page_names(self) -> List[str]:
        return [p.name for p in self.pages]

    def get_tsv_file(self, page_name: str) -> str:
        page = self.page_with_name(page_name)
        assert page is not None, "No such page with name {}".format(page_name)
        return page.get_tsv()
