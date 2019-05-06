#!/usr/bin/env python

"""
camcops_server/tasks/kirby.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import Any, Dict, Tuple, Type

import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import (
    bold,
    get_yes_no_none,
    tr_span_col,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import BoolColumn
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin


# =============================================================================
# KirbyRewardPair
# =============================================================================

class KirbyRewardPair(object):
    """
    Represents a pair of rewards: a small immediate reward (SIR) and a large
    delayed reward (LDR).
    """
    def __init__(self, sir: int, ldr: int, delay_days: int,
                 currency: str = "£") -> None:
        """
        Args:
            sir: amount of the small immediate reward (SIR)
            ldr: amount of the large delayed reward (LDR)
            delay_days: delay to the LDR, in days
            currency: currency symbol
        """
        self.sir = sir
        self.ldr = ldr
        self.delay_days = delay_days
        self.currency = currency

    def k_indifference(self) -> float:
        """
        Returns the value of k, the discounting parameter (units: days ^ -1)
        if the subject is indifferent between the two choices.

        For calculations see kirby.cpp.
        """
        a1 = self.sir
        a2 = self.ldr
        d2 = self.delay_days
        return ((a2 / a1) - 1) / d2

    def question(self) -> str:
        """
        The question posed for this reward pair.
        """
        return (
            f"Would you prefer {self.currency}{self.sir} today, "
            f"or {self.currency}{self.ldr} in {self.delay_days} days?"
        )


# =============================================================================
# Kirby
# =============================================================================

class Kirby(TaskHasPatientMixin, Task):
    """
    Server implementation of the Kirby Monetary Choice Questionnaire task.
    """
    __tablename__ = "kirby"
    shortname = "KirbyMCQ"
    longname = "Kirby et al. Monetary Choice Questionnaire"

    # *** fields
    # *** trackers etc.

    def is_complete(self) -> bool:
        return False # ***

    def get_task_html(self, req: CamcopsRequest) -> str:
        return "" # ***
