#!/usr/bin/env python
# camcops_server/tasks/wemwbs.py

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

from typing import List

from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import answer, tr, tr_qa
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


# =============================================================================
# WEMWBS
# =============================================================================

class Wemwbs(Task):
    tablename = "wemwbs"
    shortname = "WEMWBS"
    longname = "Warwick–Edinburgh Mental Well-Being Scale"
    provides_trackers = True

    MINQSCORE = 1
    MAXQSCORE = 5
    N_QUESTIONS = 14
    MINTOTALSCORE = N_QUESTIONS * MINQSCORE
    MAXTOTALSCORE = N_QUESTIONS * MAXQSCORE

    fieldspecs = repeat_fieldspec(
        "q", 1, N_QUESTIONS, min=1, max=5,
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

    def is_complete(self) -> bool:
        if not self.field_contents_valid():
            return False
        return self.are_all_fields_complete(repeat_fieldname(
            "q", 1, self.N_QUESTIONS))

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="WEMWBS total score (rating mental well-being)",
            axis_label="Total score ({}-{})".format(
                self.MINTOTALSCORE, self.MAXTOTALSCORE),
            axis_min=self.MINTOTALSCORE - 0.5,
            axis_max=self.MAXTOTALSCORE + 0.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="WEMWBS total score {} (range {}–{})".format(
                self.total_score(),
                self.MINTOTALSCORE,
                self.MAXTOTALSCORE)
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(
                name="total", cctype="INT", value=self.total_score(),
                comment="Total score (range {}-{})".format(
                    self.MINTOTALSCORE,
                    self.MAXTOTALSCORE
                )
            ),
        ]

    def total_score(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 1, self.N_QUESTIONS))

    def get_task_html(self) -> str:
        main_dict = {
            None: None,
            1: "1 — " + self.wxstring("wemwbs_a1"),
            2: "2 — " + self.wxstring("wemwbs_a2"),
            3: "3 — " + self.wxstring("wemwbs_a3"),
            4: "4 — " + self.wxstring("wemwbs_a4"),
            5: "5 — " + self.wxstring("wemwbs_a5")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(
            wappstring("total_score"),
            answer(self.total_score()) + " (range {}–{})".format(
                self.MINTOTALSCORE,
                self.MAXTOTALSCORE
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
        for i in range(1, self.N_QUESTIONS + 1):
            nstr = str(i)
            h += tr_qa(self.wxstring("wemwbs_q" + nstr),
                       get_from_dict(main_dict, getattr(self, "q" + nstr)))
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

    tablename = "swemwbs"
    shortname = "SWEMWBS"
    longname = "Short Warwick–Edinburgh Mental Well-Being Scale"
    extrastring_taskname = "wemwbs"  # shares
    fieldspecs = repeat_fieldspec(
        "q", 1, N_QUESTIONS, min=1, max=5,
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

    def is_complete(self) -> bool:
        if not self.field_contents_valid():
            return False
        return self.are_all_fields_complete(repeat_fieldname(
            "q", 1, self.N_QUESTIONS))

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="SWEMWBS total score (rating mental well-being)",
            axis_label="Total score ({}-{})".format(
                self.MINTOTALSCORE, self.MAXTOTALSCORE),
            axis_min=self.MINTOTALSCORE - 0.5,
            axis_max=self.MAXTOTALSCORE + 0.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="SWEMWBS total score {} (range {}–{})".format(
                self.total_score(),
                self.MINTOTALSCORE,
                self.MAXTOTALSCORE)
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(
                name="total", cctype="INT", value=self.total_score(),
                comment="Total score (range {}-{})".format(
                    self.MINTOTALSCORE,
                    self.MAXTOTALSCORE
                )
            ),
        ]

    def total_score(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 1, self.N_QUESTIONS))

    def get_task_html(self) -> str:
        main_dict = {
            None: None,
            1: "1 — " + self.wxstring("wemwbs_a1"),
            2: "2 — " + self.wxstring("wemwbs_a2"),
            3: "3 — " + self.wxstring("wemwbs_a3"),
            4: "4 — " + self.wxstring("wemwbs_a4"),
            5: "5 — " + self.wxstring("wemwbs_a5")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(
            wappstring("total_score"),
            answer(self.total_score()) + " (range {}–{})".format(
                self.MINTOTALSCORE,
                self.MAXTOTALSCORE
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
        for i in range(1, self.N_QUESTIONS + 1):
            nstr = str(i)
            h += tr_qa(self.wxstring("swemwbs_q" + nstr),
                       get_from_dict(main_dict, getattr(self, "q" + nstr)))
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
