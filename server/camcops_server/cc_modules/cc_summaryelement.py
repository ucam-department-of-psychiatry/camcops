#!/usr/bin/env python
# camcops_server/cc_modules/cc_simpleobjects.py

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
from typing import Any, Dict, List, Union

from cardinal_pythonlib.reprfunc import auto_repr
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.type_api import TypeEngine

from .cc_tsv import TsvPage
from .cc_xml import XmlElement


# =============================================================================
# SummaryElement
# =============================================================================

class SummaryElement(object):
    """
    Returned by tasks to represent extra summary information that they
    calculate.

    Use this for extra information that can be added to a row represented by a
    task or its ancillary object.
    """
    def __init__(self,
                 name: str,
                 coltype: TypeEngine,  # e.g. Integer(), String(length=50)
                 value: Any,
                 comment: str = None) -> None:
        self.name = name
        self.coltype = coltype
        self.value = value
        self.comment = comment


# =============================================================================
# ExtraSummaryTable
# =============================================================================

class ExtraSummaryTable(object):
    """
    Additional summary information returned by a task.

    Use this to represent an entire table that doesn't have a 1:1 relationship
    with rows of a task or ancillary object.
    """
    def __init__(self,
                 tablename: str,
                 xmlname: str,
                 columns: List[Column],
                 rows: List[Union[Dict[str, Any], OrderedDict]]) -> None:
        self.tablename = tablename
        self.xmlname = xmlname
        self.columns = columns
        self.rows = rows

    def get_xml_element(self) -> XmlElement:
        itembranches = []  # type: List[XmlElement]
        for valuedict in self.rows:
            leaves = []  # type: List[XmlElement]
            for k, v in valuedict.items():
                leaves.append(XmlElement(name=k, value=v))
            branch = XmlElement(name=self.tablename, value=leaves)
            itembranches.append(branch)
        return XmlElement(name=self.xmlname, value=itembranches)

    def get_tsv_page(self) -> TsvPage:
        return TsvPage(name=self.tablename, rows=self.rows)

    def __repr__(self) -> str:
        return auto_repr(self)
