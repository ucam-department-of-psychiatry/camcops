#!/usr/bin/env python3
# wemwbs.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
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

from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
    STANDARD_TASK_FIELDSPECS,
)
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# WEMWBS
# =============================================================================

class Wemwbs(Task):
    MINQSCORE = 1
    MAXQSCORE = 5
    N_QUESTIONS = 14
    MINTOTALSCORE = N_QUESTIONS * MINQSCORE
    MAXTOTALSCORE = N_QUESTIONS * MAXQSCORE

    @classmethod
    def get_tablename(cls):
        return "wemwbs"

    @classmethod
    def get_taskshortname(cls):
        return "WEMWBS"

    @classmethod
    def get_tasklongname(cls):
        return "Warwick–Edinburgh Mental Well-Being Scale"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + repeat_fieldspec(
            "q", 1, Wemwbs.N_QUESTIONS, min=1, max=5,
            comment_fmt="Q{n} ({s}) (1 none of the time - 5 all of the time)",
            comment_strings=[
                "optimistic",
                "useful",
                "relaxed",
                "interested in other people",
                "energy",
                "dealing with problems well",
                "thinking clearly",
                "feeling good about myself",
                "feeling close to others",
                "confident",
                "able to make up my own mind",
                "feeling loved",
                "interested in new things",
                "cheerful",
            ]
        )

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        return self.are_all_fields_complete(repeat_fieldname(
            "q", 1, Wemwbs.N_QUESTIONS))

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "WEMWBS total score (rating mental well-being)",
                "axis_label": "Total score ({}-{})".format(
                    Wemwbs.MINTOTALSCORE,
                    Wemwbs.MAXTOTALSCORE
                ),
                "axis_min": Wemwbs.MINTOTALSCORE - 0.5,
                "axis_max": Wemwbs.MAXTOTALSCORE + 0.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "WEMWBS total score {} (range {}–{})".format(
                self.total_score(),
                Wemwbs.MINTOTALSCORE,
                Wemwbs.MAXTOTALSCORE)
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(
                name="total", cctype="INT", value=self.total_score(),
                comment="Total score (range {}-{})".format(
                    Wemwbs.MINTOTALSCORE,
                    Wemwbs.MAXTOTALSCORE
                )
            ),
        ]

    def total_score(self):
        return self.sum_fields(repeat_fieldname("q", 1, Wemwbs.N_QUESTIONS))

    def get_task_html(self):
        MAIN_DICT = {
            None: None,
            1: "1 — " + WSTRING("wemwbs_a1"),
            2: "2 — " + WSTRING("wemwbs_a2"),
            3: "3 — " + WSTRING("wemwbs_a3"),
            4: "4 — " + WSTRING("wemwbs_a4"),
            5: "5 — " + WSTRING("wemwbs_a5")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(
            WSTRING("total_score"),
            answer(self.total_score()) + " (range {}–{})".format(
                Wemwbs.MINTOTALSCORE,
                Wemwbs.MAXTOTALSCORE
            )
        )
        h += """
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last 2 weeks.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """
        for i in range(1, Wemwbs.N_QUESTIONS + 1):
            nstr = str(i)
            h += tr_qa(WSTRING("wemwbs_q" + nstr),
                       get_from_dict(MAIN_DICT, getattr(self, "q" + nstr)))
        h += """
            </table>
            <div class="copyright">
                WEMWBS: from Tennant et al. (2007), <i>Health and Quality of
                Life Outcomes</i> 5:63, http://www.hqlo.com/content/5/1/63;
                © 2007 Tennant et al.; distributed under the terms of the
                Creative Commons Attribution License.
            </div>
        """
        return h


# =============================================================================
# SWEMWBS
# =============================================================================

class Swemwbs(Task):
    MINQSCORE = 1
    MAXQSCORE = 5
    N_QUESTIONS = 7
    MINTOTALSCORE = N_QUESTIONS * MINQSCORE
    MAXTOTALSCORE = N_QUESTIONS * MAXQSCORE

    @classmethod
    def get_tablename(cls):
        return "swemwbs"

    @classmethod
    def get_taskshortname(cls):
        return "SWEMWBS"

    @classmethod
    def get_tasklongname(cls):
        return "Short Warwick–Edinburgh Mental Well-Being Scale"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + repeat_fieldspec(
            "q", 1, Swemwbs.N_QUESTIONS, min=1, max=5,
            comment_fmt="Q{n} ({s}) (1 none of the time - 5 all of the time)",
            comment_strings=[
                "optimistic",
                "useful",
                "relaxed",
                "interested in other people",
                "energy",
                "dealing with problems well",
                "thinking clearly",
                "feeling good about myself",
                "feeling close to others",
                "confident",
                "able to make up my own mind",
                "feeling loved",
                "interested in new things",
                "cheerful",
            ]
        )

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        return self.are_all_fields_complete(repeat_fieldname(
            "q", 1, Swemwbs.N_QUESTIONS))

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "SWEMWBS total score (rating mental well-being)",
                "axis_label": "Total score ({}-{})".format(
                    Swemwbs.MINTOTALSCORE,
                    Swemwbs.MAXTOTALSCORE
                ),
                "axis_min": Swemwbs.MINTOTALSCORE - 0.5,
                "axis_max": Swemwbs.MAXTOTALSCORE + 0.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "SWEMWBS total score {} (range {}–{})".format(
                self.total_score(),
                Swemwbs.MINTOTALSCORE,
                Swemwbs.MAXTOTALSCORE)
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(
                name="total", cctype="INT", value=self.total_score(),
                comment="Total score (range {}-{})".format(
                    Swemwbs.MINTOTALSCORE,
                    Swemwbs.MAXTOTALSCORE
                )
            ),
        ]

    def total_score(self):
        return self.sum_fields(repeat_fieldname("q", 1, Swemwbs.N_QUESTIONS))

    def get_task_html(self):
        MAIN_DICT = {
            None: None,
            1: "1 — " + WSTRING("wemwbs_a1"),
            2: "2 — " + WSTRING("wemwbs_a2"),
            3: "3 — " + WSTRING("wemwbs_a3"),
            4: "4 — " + WSTRING("wemwbs_a4"),
            5: "5 — " + WSTRING("wemwbs_a5")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(
            WSTRING("total_score"),
            answer(self.total_score()) + " (range {}–{})".format(
                Swemwbs.MINTOTALSCORE,
                Swemwbs.MAXTOTALSCORE
            )
        )
        h += """
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last 2 weeks.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """
        for i in range(1, Swemwbs.N_QUESTIONS + 1):
            nstr = str(i)
            h += tr_qa(WSTRING("swemwbs_q" + nstr),
                       get_from_dict(MAIN_DICT, getattr(self, "q" + nstr)))
        h += """
            </table>
            <div class="copyright">
                SWEMWBS: from Stewart-Brown et al. (2009), <i>Health and
                Quality of Life Outcomes</i> 7:15,
                http://www.hqlo.com/content/7/1/15;
                © 2009 Stewart-Brown et al.; distributed under the terms of the
                Creative Commons Attribution License.
            </div>
        """
        return h
