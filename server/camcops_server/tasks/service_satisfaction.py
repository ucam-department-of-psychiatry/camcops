#!/usr/bin/env python
# camcops_server/tasks/service_satisfaction.py

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

from typing import Optional

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    ZERO_TO_FOUR_CHECKER,
)
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)


# =============================================================================
# Abstract base class
# =============================================================================

class AbstractSatisfaction(object):
    # noinspection PyMethodParameters
    @declared_attr
    def service(cls) -> Column:
        return Column(
            "service", UnicodeText,
            comment="Clinical service being rated"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def rating(cls) -> Column:
        return CamcopsColumn(
            "rating", Integer,
            permitted_value_checker=ZERO_TO_FOUR_CHECKER,
            comment="Rating (0 very poor - 4 excellent)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def good(cls) -> Column:
        return Column(
            "good", UnicodeText,
            comment="What has been good?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def bad(cls) -> Column:
        return Column(
            "bad", UnicodeText,
            comment="What could be improved?"
        )

    TASK_FIELDS = ["service", "rating", "good", "bad"]

    def is_complete(self) -> bool:
        # noinspection PyUnresolvedReferences
        return self.rating is not None and self.field_contents_valid()
        # ... self.field_contents_valid() is from Task, and we are a mixin

    def get_rating_text(self, req: CamcopsRequest) -> Optional[str]:
        ratingdict = {
            None: None,
            0: req.wappstring("satis_rating_a0"),
            1: req.wappstring("satis_rating_a1"),
            2: req.wappstring("satis_rating_a2"),
            3: req.wappstring("satis_rating_a3"),
            4: req.wappstring("satis_rating_a4"),
        }
        return get_from_dict(ratingdict, self.rating)

    def get_common_task_html(self,
                             req: CamcopsRequest,
                             rating_q: str,
                             good_q: str,
                             bad_q: str) -> str:
        if self.rating is not None:
            r = "{}. {}".format(self.rating, self.get_rating_text(req))
        else:
            r = None
        # noinspection PyUnresolvedReferences
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
                {good}
                {bad}
            </table>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            # ... self.get_is_complete_tr() is from Task, and we are a mixin
            service=tr_qa(
                req.wappstring("satis_service_being_rated"), self.service),
            rating=tr_qa("{} {}?".format(rating_q, self.service), r),
            good=tr_qa(good_q, self.good),
            bad=tr_qa(bad_q, self.bad),
        )
        return h

    def get_task_html(self, req: CamcopsRequest) -> str:
        raise NotImplementedError()


# =============================================================================
# PatientSatisfaction
# =============================================================================

class PatientSatisfaction(TaskHasPatientMixin, AbstractSatisfaction, Task):
    __tablename__ = "pt_satis"
    shortname = "PatientSatisfaction"
    longname = "Patient Satisfaction Scale"

    def get_task_html(self, req: CamcopsRequest) -> str:
        return self.get_common_task_html(
            req,
            req.wappstring("satis_pt_rating_q"),
            req.wappstring("satis_good_q"),
            req.wappstring("satis_bad_q")
        )


# =============================================================================
# ReferrerSatisfactionGen
# =============================================================================

class ReferrerSatisfactionGen(AbstractSatisfaction, Task):
    __tablename__ = "ref_satis_gen"
    shortname = "ReferrerSatisfactionSurvey"
    longname = "Referrer Satisfaction Scale, survey"

    def get_task_html(self, req: CamcopsRequest) -> str:
        return self.get_common_task_html(
            req,
            req.wappstring("satis_ref_gen_rating_q"),
            req.wappstring("satis_good_q"),
            req.wappstring("satis_bad_q")
        )


# =============================================================================
# ReferrerSatisfactionSpec
# =============================================================================

class ReferrerSatisfactionSpec(TaskHasPatientMixin, AbstractSatisfaction,
                               Task):
    __tablename__ = "ref_satis_spec"
    shortname = "ReferrerSatisfactionSpecific"
    longname = "Referrer Satisfaction Scale, patient-specific"

    def get_task_html(self, req: CamcopsRequest) -> str:
        return self.get_common_task_html(
            req,
            req.wappstring("satis_ref_spec_rating_q"),
            req.wappstring("satis_good_q"),
            req.wappstring("satis_bad_q")
        )
