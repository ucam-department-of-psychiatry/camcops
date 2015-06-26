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

from cc_modules.cc_html import tr_qa
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# FFT
# =============================================================================

class Fft(Task):
    TASK_FIELDSPECS = [
        dict(name="service", cctype="TEXT",
             comment="Clinical service being rated"),
        dict(name="rating", cctype="INT", min=1, max=6,
             comment="Likelihood of recommendation to friends/family (1 "
                     "extremely likely - 5 extremely unlikely, 6 don't know)"),
    ]
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "fft"

    @classmethod
    def get_taskshortname(cls):
        return "FFT"

    @classmethod
    def get_tasklongname(cls):
        return "Friends and Family Test"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + cls.TASK_FIELDSPECS

    def is_complete(self):
        return self.rating is not None and self.field_contents_valid()

    def get_rating_text(self):
        ratingdict = {
            None: None,
            1: WSTRING("fft_a1"),
            2: WSTRING("fft_a2"),
            3: WSTRING("fft_a3"),
            4: WSTRING("fft_a4"),
            5: WSTRING("fft_a5"),
            6: WSTRING("fft_a6"),
        }
        return get_from_dict(ratingdict, self.rating)

    def get_task_html(self):
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
        h += tr_qa(WSTRING("fft_q"), r)
        h += u"""
            </table>
        """
        return h
