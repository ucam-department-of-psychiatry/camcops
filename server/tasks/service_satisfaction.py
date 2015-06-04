#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from cc_html import tr_qa
from cc_string import WSTRING
from cc_task import (
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# Abstract base class
# =============================================================================

class AbstractSatisfaction(object):
    TASK_FIELDSPECS = [
        dict(name="service", cctype="TEXT",
             comment="Clinical service being rated"),
        dict(name="rating", cctype="INT", min=0, max=4,
             comment="Rating (0 very poor - 4 excellent)"),
        dict(name="good", cctype="TEXT",
             comment="What has been good?"),
        dict(name="bad", cctype="TEXT",
             comment="What could be improved?"),
    ]
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + cls.TASK_FIELDSPECS

    def is_complete(self):
        return self.rating is not None and self.field_contents_valid()

    def get_rating_text(self):
        ratingdict = {
            None: None,
            0: WSTRING("service_satis_rating_a0"),
            1: WSTRING("service_satis_rating_a1"),
            2: WSTRING("service_satis_rating_a2"),
            3: WSTRING("service_satis_rating_a3"),
            4: WSTRING("service_satis_rating_a4"),
        }
        return get_from_dict(ratingdict, self.rating)

    def get_common_task_html(self, rating_q, good_q, bad_q):
        if self.rating is not None:
            r = u"{}. {}".format(self.rating, self.get_rating_text())
        else:
            r = None
        h = u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr() + u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        h += tr_qa(WSTRING("service_being_rated"), self.service)
        h += tr_qa(u"{} {}?".format(rating_q, self.service), r)
        h += tr_qa(good_q, self.good)
        h += tr_qa(bad_q, self.bad)
        h += u"""
            </table>
        """
        return h


# =============================================================================
# PatientSatisfaction
# =============================================================================

class PatientSatisfaction(AbstractSatisfaction, Task):

    @classmethod
    def get_tablename(cls):
        return "pt_satis"

    @classmethod
    def get_taskshortname(cls):
        return "PatientSatisfaction"

    @classmethod
    def get_tasklongname(cls):
        return "Patient Satisfaction Scale"

    def get_task_html(self):
        return self.get_common_task_html(
            WSTRING("pt_satis_rating_q"),
            WSTRING("pt_satis_good_q"),
            WSTRING("pt_satis_bad_q")
        )


# =============================================================================
# ReferrerSatisfactionGen
# =============================================================================

class ReferrerSatisfactionGen(AbstractSatisfaction, Task):

    @classmethod
    def get_tablename(cls):
        return "ref_satis_gen"

    @classmethod
    def get_taskshortname(cls):
        return "ReferrerSatisfactionSurvey"

    @classmethod
    def get_tasklongname(cls):
        return "Referrer Satisfaction Scale, survey"

    def get_task_html(self):
        return self.get_common_task_html(
            WSTRING("ref_satis_rating_gen_q"),
            WSTRING("ref_satis_good_q"),
            WSTRING("ref_satis_bad_q")
        )


# =============================================================================
# ReferrerSatisfactionSpec
# =============================================================================

class ReferrerSatisfactionSpec(AbstractSatisfaction, Task):

    @classmethod
    def get_tablename(cls):
        return "ref_satis_spec"

    @classmethod
    def get_taskshortname(cls):
        return "ReferrerSatisfactionSpecific"

    @classmethod
    def get_tasklongname(cls):
        return "Referrer Satisfaction Scale, patient-specific"

    def get_task_html(self):
        return self.get_common_task_html(
            WSTRING("ref_satis_rating_spec_q"),
            WSTRING("ref_satis_good_q"),
            WSTRING("ref_satis_bad_q")
        )
