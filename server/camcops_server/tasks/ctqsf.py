#!/usr/bin/env python

"""
camcops_server/tasks/ctqsf.py

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

from typing import Dict, List, Optional

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.stringfunc import strseq
from semantic_version import Version
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo, CTV_INCOMPLETE
from camcops_server.cc_modules.cc_html import answer, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_snomed import SnomedExpression, SnomedLookup
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    ZERO_TO_FOUR_CHECKER,
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerAxisTick,
    TrackerInfo,
)


# =============================================================================
# CTQ-SF
# =============================================================================

class Ctqsf(TaskHasPatientMixin, Task):
    """
    Server implementation of the CTQ-SF task.
    """
    __tablename__ = "ctqsf"
    shortname = "CTQ-SF"
    provides_trackers = False

    # *** fields

    N_QUESTIONS = 28
    QUESTION_FIELDNAMES = strseq("q", 1, N_QUESTIONS)

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Childhood Trauma Questionnaire, Short Form")

    # noinspection PyMethodParameters
    @classproperty
    def minimum_client_version(cls) -> Version:
        return Version("2.2.8")

    def is_complete(self) -> bool:
        return self.all_fields_not_none(self.QUESTION_FIELDNAMES)

    def get_task_html(self, req: CamcopsRequest) -> str:
        return "" # *** IMPLEMENT

    # No SNOMED code for the CTQ.
