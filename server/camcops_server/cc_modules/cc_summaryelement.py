#!/usr/bin/env python
# camcops_server/cc_modules/cc_simpleobjects.py

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

from typing import Any, Type

from sqlalchemy.sql.type_api import TypeEngine


# =============================================================================
# SummaryElement
# =============================================================================

class SummaryElement(object):
    """
    Returned by tasks to represent extra summary information that they
    calculate.
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
