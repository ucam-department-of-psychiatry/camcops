#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_reportschema.py

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

**Common reports schema nodes.**

"""

from typing import Any, Dict

from cardinal_pythonlib.colander_utils import BooleanNode
from colander import SchemaNode

from camcops_server.cc_modules.cc_forms import RequestAwareMixin


DEFAULT_BY_YEAR = True
DEFAULT_BY_MONTH = True
DEFAULT_BY_TASK = True
DEFAULT_BY_USER = False


class ByYearSelector(BooleanNode, RequestAwareMixin):
    """
    Split report by year?
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, default=DEFAULT_BY_YEAR, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        _ = self.gettext
        self.title = self.label = _("Split by year?")


class ByMonthSelector(BooleanNode, RequestAwareMixin):
    """
    Split report by month?
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, default=DEFAULT_BY_MONTH, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        _ = self.gettext
        self.title = self.label = _("Split by month?")


class ByTaskSelector(BooleanNode, RequestAwareMixin):
    """
    Split report by task type?
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, default=DEFAULT_BY_TASK, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        _ = self.gettext
        self.title = self.label = _("Split by task type?")


class ByUserSelector(BooleanNode, RequestAwareMixin):
    """
    Split report by user?
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, default=DEFAULT_BY_USER, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        _ = self.gettext
        self.title = self.label = _("Split by user?")
