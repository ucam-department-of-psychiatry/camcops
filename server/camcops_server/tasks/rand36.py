#!/usr/bin/env python
# rand36.py

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

from typing import Any, List, Optional

from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import answer, identity, tr, tr_span_col
from ..cc_modules.cc_lang import mean
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo


# =============================================================================
# RAND-36
# =============================================================================

class Rand36(Task):
    NQUESTIONS = 36

    tablename = "rand36"
    shortname = "RAND-36"
    longname = "RAND 36-Item Short Form Health Survey 1.0"
    fieldspecs = [
        dict(name="q1", cctype="INT", min=1, max=5,
             comment="Q1 (general health) (1 excellent - 5 poor)"),
        dict(name="q2", cctype="INT", min=1, max=5,
             comment="Q2 (health cf. 1y ago) (1 much better - 5 much worse)"),
    ] + repeat_fieldspec(
        "q", 3, 12, min=1, max=3,
        comment_fmt="Q{n} ({s}) (1 limited a lot - 3 not limited at all)",
        comment_strings=[
            "Vigorous activities",
            "Moderate activities",
            "Lifting or carrying groceries",
            "Climbing several flights of stairs",
            "Climbing one flight of stairs",
            "Bending, kneeling, or stooping",
            "Walking more than a mile",
            "Walking several blocks",
            "Walking one block",
            "Bathing or dressing yourself",
        ]
    ) + repeat_fieldspec(
        "q", 13, 16, min=1, max=2,
        comment_fmt="Q{n} (physical health: {s}) (1 yes, 2 no)",
        comment_strings=[
            "Cut down work/other activities",
            "Accomplished less than would like",
            "Were limited in the kind of work or other activities",
            "Had difficulty performing the work or other activities",
        ]
    ) + repeat_fieldspec(
        "q", 17, 19, min=1, max=2,
        comment_fmt="Q{n} (emotional problems: {s}) (1 yes, 2 no)",
        comment_strings=[
            "Cut down work/other activities",
            "Accomplished less than would like",
            "Didn't do work or other activities as carefully as usual",
            "Had difficulty performing the work or other activities",
        ]
    ) + [
        dict(name="q20", cctype="INT", min=1, max=5,
             comment="Q20 (past 4 weeks, to what extent physical health/"
             "emotional problems interfered with social activity) "
             "(1 not at all - 5 extremely)"),
        dict(name="q21", cctype="INT", min=1, max=6,
             comment="Q21 (past 4 weeks, how much pain (1 none - 6 very "
             "severe)"),
        dict(name="q22", cctype="INT", min=1, max=5,
             comment="Q22 (past 4 weeks, pain interfered with normal activity "
             "(1 not at all - 5 extremely)"),
    ] + repeat_fieldspec(
        "q", 23, 31, min=1, max=6,
        comment_fmt="Q{n} (past 4 weeks: {s}) (1 all of the time - 6 none of "
        "the time)",
        comment_strings=[
            "Did you feel full of pep?",
            "Have you been a very nervous person?",
            "Have you felt so down in the dumps that nothing could cheer you "
            "up?",
            "Have you felt calm and peaceful?",
            "Did you have a lot of energy?",
            "Have you felt downhearted and blue?",
            "Did you feel worn out?",
            "Have you been a happy person?",
            "Did you feel tired?",
        ]
    ) + [
        dict(name="q32", cctype="INT", min=1, max=5,
             comment="Q32 (past 4 weeks, how much of the time has physical "
             "health/emotional problems interfered with social activities "
             "(1 all of the time - 5 none of the time)"),
        # ... note Q32 extremely similar to Q20.
    ] + repeat_fieldspec(
        "q", 33, 36, min=1, max=5,
        comment_fmt="Q{n} (how true/false: {s}) (1 definitely true - "
        "5 definitely false)",
        comment_strings=[
            "I seem to get sick a little easier than other people",
            "I am as healthy as anybody I know",
            "I expect my health to get worse",
            "My health is excellent",
        ]
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(
                repeat_fieldname("q", 1, self.NQUESTIONS)) and
            self.field_contents_valid()
        )

    @classmethod
    def tracker_element(cls, value: float, plot_label: str) -> TrackerInfo:
        return TrackerInfo(
            value=value,
            plot_label="RAND-36: " + plot_label,
            axis_label="Scale score (out of 100)",
            axis_min=-0.5,
            axis_max=100.5
        )

    def get_trackers(self) -> List[TrackerInfo]:
        return [
            self.tracker_element(self.score_overall(),
                                 self.wxstring("score_overall")),
            self.tracker_element(self.score_physical_functioning(),
                                 self.wxstring("score_physical_functioning")),
            self.tracker_element(
                self.score_role_limitations_physical(),
                self.wxstring("score_role_limitations_physical")),
            self.tracker_element(
                self.score_role_limitations_emotional(),
                self.wxstring("score_role_limitations_emotional")),
            self.tracker_element(self.score_energy(),
                                 self.wxstring("score_energy")),
            self.tracker_element(self.score_emotional_wellbeing(),
                                 self.wxstring("score_emotional_wellbeing")),
            self.tracker_element(self.score_social_functioning(),
                                 self.wxstring("score_social_functioning")),
            self.tracker_element(self.score_pain(),
                                 self.wxstring("score_pain")),
            self.tracker_element(self.score_general_health(),
                                 self.wxstring("score_general_health")),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content=(
                "RAND-36 (scores out of 100, 100 best): overall {}, "
                "physical functioning {}, physical role "
                "limitations {}, emotional role limitations {}, "
                "energy {}, emotional wellbeing {}, social "
                "functioning {}, pain {}, general health {}.".format(
                    self.score_overall(),
                    self.score_physical_functioning(),
                    self.score_role_limitations_physical(),
                    self.score_role_limitations_emotional(),
                    self.score_energy(),
                    self.score_emotional_wellbeing(),
                    self.score_social_functioning(),
                    self.score_pain(),
                    self.score_general_health(),
                )
            )
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="overall", cctype="FLOAT",
                 value=self.score_overall(),
                 comment="Overall mean score (0-100, higher better)"),
            dict(name="physical_functioning", cctype="FLOAT",
                 value=self.score_physical_functioning(),
                 comment="Physical functioning score (0-100, higher better)"),
            dict(name="role_limitations_physical", cctype="FLOAT",
                 value=self.score_role_limitations_physical(),
                 comment="Role limitations due to physical health score "
                 "(0-100, higher better)"),
            dict(name="role_limitations_emotional", cctype="FLOAT",
                 value=self.score_role_limitations_emotional(),
                 comment="Role limitations due to emotional problems score "
                 "(0-100, higher better)"),
            dict(name="energy", cctype="FLOAT",
                 value=self.score_energy(),
                 comment="Energy/fatigue score (0-100, higher better)"),
            dict(name="emotional_wellbeing", cctype="FLOAT",
                 value=self.score_emotional_wellbeing(),
                 comment="Emotional well-being score (0-100, higher better)"),
            dict(name="social_functioning", cctype="FLOAT",
                 value=self.score_social_functioning(),
                 comment="Social functioning score (0-100, higher better)"),
            dict(name="pain", cctype="FLOAT",
                 value=self.score_pain(),
                 comment="Pain score (0-100, higher better)"),
            dict(name="general_health", cctype="FLOAT",
                 value=self.score_general_health(),
                 comment="General health score (0-100, higher better)"),
        ]

    # Scoring
    def recode(self, q: int) -> Optional[float]:
        x = getattr(self, "q" + str(q))  # response
        if x is None or x < 1:
            return None
        # http://m.rand.org/content/dam/rand/www/external/health/
        #        surveys_tools/mos/mos_core_36item_scoring.pdf
        if q == 1 or q == 2 or q == 20 or q == 22 or q == 34 or q == 36:
            # 1 becomes 100, 2 => 75, 3 => 50, 4 =>25, 5 => 0
            if x > 5:
                return None
            return 100 - 25 * (x - 1)
        elif 3 <= q <= 12:
            # 1 => 0, 2 => 50, 3 => 100
            if x > 3:
                return None
            return 50 * (x - 1)
        elif 13 <= q <= 19:
            # 1 => 0, 2 => 100
            if x > 2:
                return None
            return 100 * (x - 1)
        elif q == 21 or q == 23 or q == 26 or q == 27 or q == 30:
            # 1 => 100, 2 => 80, 3 => 60, 4 => 40, 5 => 20, 6 => 0
            if x > 6:
                return None
            return 100 - 20 * (x - 1)
        elif q == 24 or q == 25 or q == 28 or q == 29 or q == 31:
            # 1 => 0, 2 => 20, 3 => 40, 4 => 60, 5 => 80, 6 => 100
            if x > 6:
                return None
            return 20 * (x - 1)
        elif q == 32 or q == 33 or q == 35:
            # 1 => 0, 2 => 25, 3 => 50, 4 => 75, 5 => 100
            if x > 5:
                return None
            return 25 * (x - 1)
        return None

    def score_physical_functioning(self) -> Optional[float]:
        return mean([self.recode(3), self.recode(4), self.recode(5),
                     self.recode(6), self.recode(7), self.recode(8),
                     self.recode(9), self.recode(10), self.recode(11),
                     self.recode(12)])

    def score_role_limitations_physical(self) -> Optional[float]:
        return mean([self.recode(13), self.recode(14), self.recode(15),
                     self.recode(16)])

    def score_role_limitations_emotional(self) -> Optional[float]:
        return mean([self.recode(17), self.recode(18), self.recode(19)])

    def score_energy(self) -> Optional[float]:
        return mean([self.recode(23), self.recode(27), self.recode(29),
                     self.recode(31)])

    def score_emotional_wellbeing(self) -> Optional[float]:
        return mean([self.recode(24), self.recode(25), self.recode(26),
                     self.recode(28), self.recode(30)])

    def score_social_functioning(self) -> Optional[float]:
        return mean([self.recode(20), self.recode(32)])

    def score_pain(self) -> Optional[float]:
        return mean([self.recode(21), self.recode(22)])

    def score_general_health(self) -> Optional[float]:
        return mean([self.recode(1), self.recode(33), self.recode(34),
                     self.recode(35), self.recode(36)])

    @staticmethod
    def format_float_for_display(val: Optional[float]) -> Optional[str]:
        if val is None:
            return None
        return "{:.1f}".format(val)

    def score_overall(self) -> Optional[float]:
        values = []
        for q in range(1, self.NQUESTIONS + 1):
            values.append(self.recode(q))
        return mean(values)

    @staticmethod
    def section_row_html(text: str) -> str:
        return tr_span_col(text, cols=3, tr_class="subheading")

    def answer_text(self, q: int, v: Any) -> Optional[str]:
        if v is None:
            return None
        # wxstring has its own validity checking, so we can do:
        if q == 1 or q == 2 or (20 <= q <= 22) or q == 32:
            return self.wxstring("q" + str(q) + "_option" + str(v))
        elif 3 <= q <= 12:
            return self.wxstring("activities_option" + str(v))
        elif 13 <= q <= 19:
            return self.wxstring("yesno_option" + str(v))
        elif 23 <= q <= 31:
            return self.wxstring("last4weeks_option" + str(v))
        elif 33 <= q <= 36:
            return self.wxstring("q33to36_option" + str(v))
        else:
            return None

    def answer_row_html(self, q: int) -> str:
        qtext = self.wxstring("q" + str(q))
        v = getattr(self, "q" + str(q))
        atext = self.answer_text(q, v)
        s = self.recode(q)
        return tr(
            qtext,
            answer(v) + ": " + answer(atext),
            answer(s, formatter_answer=identity)
        )

    @staticmethod
    def scoreline(text: str, footnote_num: int, score: Optional[float]) -> str:
        return tr(
            text + " <sup>[{}]</sup>".format(footnote_num),
            answer(score) + " / 100"
        )

    def get_task_html(self) -> str:
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += self.scoreline(
            self.wxstring("score_overall"), 1,
            self.format_float_for_display(self.score_overall()))
        h += self.scoreline(
            self.wxstring("score_physical_functioning"), 2,
            self.format_float_for_display(self.score_physical_functioning()))
        h += self.scoreline(
            self.wxstring("score_role_limitations_physical"), 3,
            self.format_float_for_display(
                self.score_role_limitations_physical()))
        h += self.scoreline(
            self.wxstring("score_role_limitations_emotional"), 4,
            self.format_float_for_display(
                self.score_role_limitations_emotional()))
        h += self.scoreline(
            self.wxstring("score_energy"), 5,
            self.format_float_for_display(self.score_energy()))
        h += self.scoreline(
            self.wxstring("score_emotional_wellbeing"), 6,
            self.format_float_for_display(self.score_emotional_wellbeing()))
        h += self.scoreline(
            self.wxstring("score_social_functioning"), 7,
            self.format_float_for_display(self.score_social_functioning()))
        h += self.scoreline(
            self.wxstring("score_pain"), 8,
            self.format_float_for_display(self.score_pain()))
        h += self.scoreline(
            self.wxstring("score_general_health"), 9,
            self.format_float_for_display(self.score_general_health()))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="30%">Answer</th>
                    <th width="10%">Score</th>
                </tr>
        """
        for q in range(1, 2 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html(self.wxstring("activities_q"))
        for q in range(3, 12 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html(
            self.wxstring("work_activities_physical_q"))
        for q in range(13, 16 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html(
            self.wxstring("work_activities_emotional_q"))
        for q in range(17, 19 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html("<br>")
        h += self.answer_row_html(20)
        h += self.section_row_html("<br>")
        for q in range(21, 22 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html(self.wxstring("last4weeks_q_a") + " " +
                                   self.wxstring("last4weeks_q_b"))
        for q in range(23, 31 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html("<br>")
        for q in [32]:
            h += self.answer_row_html(q)
        h += self.section_row_html(self.wxstring("q33to36stem"))
        for q in range(33, 36 + 1):
            h += self.answer_row_html(q)
        h += """
            </table>
            <div class="copyright">
                The RAND 36-Item Short Form Health Survey was developed at RAND
                as part of the Medical Outcomes Study. See
            http://www.rand.org/health/surveys_tools/mos/mos_core_36item.html
            </div>
            <div class="footnotes">
                All questions are first transformed to a score in the range
                0–100. Higher scores are always better. Then:
                [1] Mean of all 36 questions.
                [2] Mean of Q3–12 inclusive.
                [3] Q13–16.
                [4] Q17–19.
                [5] Q23, 27, 29, 31.
                [6] Q24, 25, 26, 28, 30.
                [7] Q20, 32.
                [8] Q21, 22.
                [9] Q1, 33–36.
            </div>
        """
        return h
