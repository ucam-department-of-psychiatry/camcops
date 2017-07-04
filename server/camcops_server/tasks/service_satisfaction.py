#!/usr/bin/env python
# service_satisfaction.py

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

from typing import Optional

from ..cc_modules.cc_html import tr_qa
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# Abstract base class
# =============================================================================

class AbstractSatisfaction(object):
    fieldspecs = [
        dict(name="service", cctype="TEXT",
             comment="Clinical service being rated"),
        dict(name="rating", cctype="INT", min=0, max=4,
             comment="Rating (0 very poor - 4 excellent)"),
        dict(name="good", cctype="TEXT",
             comment="What has been good?"),
        dict(name="bad", cctype="TEXT",
             comment="What could be improved?"),
    ]

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self) -> bool:
        return self.rating is not None and self.field_contents_valid()

    def get_rating_text(self) -> Optional[str]:
        ratingdict = {
            None: None,
            0: wappstring("satis_rating_a0"),
            1: wappstring("satis_rating_a1"),
            2: wappstring("satis_rating_a2"),
            3: wappstring("satis_rating_a3"),
            4: wappstring("satis_rating_a4"),
        }
        return get_from_dict(ratingdict, self.rating)

    def get_common_task_html(self,
                             rating_q: str,
                             good_q: str,
                             bad_q: str) -> str:
        if self.rating is not None:
            r = "{}. {}".format(self.rating, self.get_rating_text())
        else:
            r = None
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr() + """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        h += tr_qa(wappstring("satis_service_being_rated"), self.service)
        h += tr_qa("{} {}?".format(rating_q, self.service), r)
        h += tr_qa(good_q, self.good)
        h += tr_qa(bad_q, self.bad)
        h += """
            </table>
        """
        return h


# =============================================================================
# PatientSatisfaction
# =============================================================================

class PatientSatisfaction(AbstractSatisfaction, Task):
    tablename = "pt_satis"
    shortname = "PatientSatisfaction"
    longname = "Patient Satisfaction Scale"

    def get_task_html(self) -> str:
        return self.get_common_task_html(
            wappstring("satis_pt_rating_q"),
            wappstring("satis_good_q"),
            wappstring("satis_bad_q")
        )


# =============================================================================
# ReferrerSatisfactionGen
# =============================================================================

class ReferrerSatisfactionGen(AbstractSatisfaction, Task):
    tablename = "ref_satis_gen"
    shortname = "ReferrerSatisfactionSurvey"
    longname = "Referrer Satisfaction Scale, survey"
    is_anonymous = True

    def get_task_html(self) -> str:
        return self.get_common_task_html(
            wappstring("satis_ref_gen_rating_q"),
            wappstring("satis_good_q"),
            wappstring("satis_bad_q")
        )


# =============================================================================
# ReferrerSatisfactionSpec
# =============================================================================

class ReferrerSatisfactionSpec(AbstractSatisfaction, Task):
    tablename = "ref_satis_spec"
    shortname = "ReferrerSatisfactionSpecific"
    longname = "Referrer Satisfaction Scale, patient-specific"

    def get_task_html(self) -> str:
        return self.get_common_task_html(
            wappstring("satis_ref_spec_rating_q"),
            wappstring("satis_good_q"),
            wappstring("satis_bad_q")
        )
