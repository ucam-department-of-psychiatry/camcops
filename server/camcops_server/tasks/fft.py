#!/usr/bin/env python
# camcops_server/tasks/fft.py

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

from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    PermittedValueChecker,
)
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)


# =============================================================================
# FFT
# =============================================================================

class Fft(TaskHasPatientMixin, Task):
    __tablename__ = "fft"
    shortname = "FFT"
    longname = "Friends and Family Test"

    service = Column(
        "service", UnicodeText,
        comment="Clinical service being rated"
    )
    rating = CamcopsColumn(
        "rating", Integer,
        permitted_value_checker=PermittedValueChecker(minimum=1, maximum=6),
        comment="Likelihood of recommendation to friends/family (1 "
                "extremely likely - 5 extremely unlikely, 6 don't know)"
    )

    def is_complete(self) -> bool:
        return self.rating is not None and self.field_contents_valid()

    def get_rating_text(self, req: CamcopsRequest) -> str:
        ratingdict = {
            None: None,
            1: self.wxstring(req, "a1"),
            2: self.wxstring(req, "a2"),
            3: self.wxstring(req, "a3"),
            4: self.wxstring(req, "a4"),
            5: self.wxstring(req, "a5"),
            6: self.wxstring(req, "a6"),
        }
        return get_from_dict(ratingdict, self.rating)

    def get_task_html(self, req: CamcopsRequest) -> str:
        if self.rating is not None:
            r = "{}. {}".format(self.rating, self.get_rating_text(req))
        else:
            r = None
        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
                {service}
                {rating}
            </table>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            service=tr_qa(req.wappstring("satis_service_being_rated"),
                          self.service),
            rating=tr_qa(self.wxstring(req, "q"), r),
        )
        return h
