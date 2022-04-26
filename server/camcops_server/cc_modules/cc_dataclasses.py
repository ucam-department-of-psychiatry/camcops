#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_dataclasses.py

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

**Dataclasses.**

"""

from dataclasses import dataclass
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import Column
    from camcops_server.cc_modules.cc_summaryelement import SummaryElement


# =============================================================================
# SummarySchemaInfo
# =============================================================================


@dataclass(eq=True, frozen=True, order=True)  # hashable, sortable
class SummarySchemaInfo:
    """
    Information to be given to the user about the schema for spreadsheet-style
    downloads, including database and summary columns.
    """

    # Summary schema values:
    SSV_DB = "database"
    SSV_SUMMARY = "summary"
    VALID_SOURCES = {SSV_DB, SSV_SUMMARY}

    table_name: str
    source: str
    column_name: str
    data_type: str
    comment: str

    def __post_init__(self) -> None:
        assert (
            self.source in self.VALID_SOURCES
        ), f"Bad source: {self.source!r}"

    @property
    def as_dict(self) -> Dict[str, str]:
        """
        Used to create spreadsheet rows. Maps spreadsheet headings to values.
        """
        return {
            "table_name": self.table_name,
            "source": self.source,
            "column_name": self.column_name,
            "data_type": self.data_type,
            "comment": self.comment,
        }

    @classmethod
    def from_column(
        cls,
        column: "Column",
        table_name: str = "",
        source: str = "",
        column_name_prefix: str = "",
    ) -> "SummarySchemaInfo":
        """
        Create from an SQLAlchemy column.
        """
        if not table_name:
            if column.table is not None:
                table_name = column.table.name
            else:
                raise ValueError(
                    f"table_name not specified and column not "
                    f"attached to a table: {column!r}"
                )
        source = source or cls.SSV_DB
        return cls(
            table_name=table_name,
            source=source,
            column_name=column_name_prefix + column.name,
            data_type=str(column.type),
            comment=column.comment,
        )

    @classmethod
    def from_summary_element(
        cls,
        table_name: str,
        element: "SummaryElement",
        source: str = "",
        column_name_prefix: str = "",
    ) -> "SummarySchemaInfo":
        """
        Create from a
        :class:`camcops_server.cc_modules.cc_summaryelement.SummarySchemaInfo`.
        """
        source = source or cls.SSV_SUMMARY
        return cls(
            table_name=table_name,
            source=source,
            column_name=column_name_prefix + element.name,
            data_type=str(element.coltype),
            comment=element.decorated_comment,
        )
