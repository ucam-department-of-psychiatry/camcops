#!/usr/bin/env python
# camcops_server/cc_modules/cc_tsv.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

import logging
from typing import Any, Dict, List

from cardinal_pythonlib.lists import (
    index_list_for_sort_order,
    sort_list_by_index_list,
)
from cardinal_pythonlib.logs import BraceStyleAdapter

from .cc_convert import tsv_escape

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# TSV output holding structures
# =============================================================================

class TsvChunk(object):
    def __init__(self,
                 filename_stem: str,
                 headings: List[str],
                 rows: List[List[Any]]) -> None:
        assert filename_stem, "Missing filename_stem"
        self.filename_stem = filename_stem
        self.headings = [tsv_escape(heading) for heading in headings]
        self.rows = [[tsv_escape(value) for value in row] for row in rows]
        self.empty = len(rows) == 0

    def add_value(self, heading: str, value: Any) -> None:
        assert len(self.rows) == 1, "add_value can only be used if #row == 1"
        self.headings.append(heading)
        self.rows[0].append(tsv_escape(value))

    def add_column(self, heading: str, values: List[Any]) -> None:
        assert len(values) == len(self.rows), "#values != #existing rows"
        self.headings.append(heading)
        for i, row in enumerate(self.rows):
            row.append(tsv_escape(values[i]))

    def add_tsv_chunk(self, other: "TsvChunk") -> None:
        assert len(self.rows) == len(other.rows), "Mismatched #rows"
        self.headings.extend(other.headings)
        for i, row in enumerate(self.rows):
            row.extend(other.rows[i])

    def sort_by_headings(self) -> None:
        # Determine order in which to sort headings
        indexes = index_list_for_sort_order(self.headings)
        # Sort the headings
        sort_list_by_index_list(self.headings, indexes)
        # Sort the rows in the same order as the headings!
        for row in self.rows:
            sort_list_by_index_list(row, indexes)


class TsvCollection(object):
    def __init__(self) -> None:
        self.filename_stems = []  # type: List[str]
        self.headings = {}  # type: Dict[str, List[str]]
        self.content_pages = {}  # type: Dict[str, List[List[str]]]

    def add_chunk(self, element: TsvChunk,
                  check_headings: bool = True) -> None:
        if element.empty:
            return
        fs = element.filename_stem
        if fs not in self.filename_stems:
            self.filename_stems.append(fs)
            self.headings[fs] = element.headings
            # ... the assumption being that any other tasks with the same
            # filename_stem must have the same headings
            self.content_pages[fs] = []
        elif check_headings:
            assert element.headings == self.headings[fs]
        self.content_pages[fs].extend(element.rows)

    def add_chunks(self, elements: List[TsvChunk]) -> None:
        for element in elements:
            self.add_chunk(element)

    def sort_by_headings(self) -> None:
        # See TsvChunk.sort_by_headings
        for fs in self.filename_stems:
            headings = self.headings[fs]
            rows = self.content_pages[fs]
            indexes = index_list_for_sort_order(headings)
            sort_list_by_index_list(headings, indexes)
            for row in rows:
                sort_list_by_index_list(row, indexes)

    def get_filename_stems(self) -> List[str]:
        return self.filename_stems

    def get_tsv_file(self, filename_stem: str) -> str:
        headings = self.headings[filename_stem]
        rows = self.content_pages[filename_stem]
        lines = ["\t".join(headings)] + ["\t".join(row) for row in rows]
        return "\n".join(lines)
