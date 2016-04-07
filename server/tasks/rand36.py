#!/usr/bin/env python3
# rand36.py

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
)
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    identity,
    tr,
    tr_span_col,
)
from cc_modules.cc_lang import mean
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task


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
        dict(name="q21", cctype="INT", min=1, max=5,
             comment="Q21 (past 4 weeks, how much pain (1 none - 5 very "
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

    def is_complete(self):
        return (
            self.are_all_fields_complete(
                repeat_fieldname("q", 1, self.NQUESTIONS)) and
            self.field_contents_valid()
        )

    @classmethod
    def tracker_element(cls, value, plot_label):
        return {
            "value": value,
            "plot_label": "RAND-36: " + plot_label,
            "axis_label": "Scale score (out of 100)",
            "axis_min": -0.5,
            "axis_max": 100.5,
        }

    def get_trackers(self):
        return [
            self.tracker_element(self.scoreOverall(),
                                 WSTRING("rand36_score_overall")),
            self.tracker_element(self.scorePhysicalFunctioning(),
                                 WSTRING("rand36_score_physical_functioning")),
            self.tracker_element(
                self.scoreRoleLimitationsPhysical(),
                WSTRING("rand36_score_role_limitations_physical")),
            self.tracker_element(
                self.scoreRoleLimitationsEmotional(),
                WSTRING("rand36_score_role_limitations_emotional")),
            self.tracker_element(self.scoreEnergy(),
                                 WSTRING("rand36_score_energy")),
            self.tracker_element(self.scoreEmotionalWellbeing(),
                                 WSTRING("rand36_score_emotional_wellbeing")),
            self.tracker_element(self.scoreSocialFunctioning(),
                                 WSTRING("rand36_score_social_functioning")),
            self.tracker_element(self.scorePain(),
                                 WSTRING("rand36_score_pain")),
            self.tracker_element(self.scoreGeneralHealth(),
                                 WSTRING("rand36_score_general_health")),
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content":  "RAND-36 (scores out of 100, 100 best): overall {}, "
                        "physical functioning {}, physical role "
                        "limitations {}, emotional role limitations {}, "
                        "energy {}, emotional wellbeing {}, social "
                        "functioning {}, pain {}, general health {}.".format(
                            self.scoreOverall(),
                            self.scorePhysicalFunctioning(),
                            self.scoreRoleLimitationsPhysical(),
                            self.scoreRoleLimitationsEmotional(),
                            self.scoreEnergy(),
                            self.scoreEmotionalWellbeing(),
                            self.scoreSocialFunctioning(),
                            self.scorePain(),
                            self.scoreGeneralHealth(),
                        )
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="overall", cctype="FLOAT",
                 value=self.scoreOverall(),
                 comment="Overall mean score (0-100, higher better)"),
            dict(name="physical_functioning", cctype="FLOAT",
                 value=self.scorePhysicalFunctioning(),
                 comment="Physical functioning score (0-100, higher better)"),
            dict(name="role_limitations_physical", cctype="FLOAT",
                 value=self.scoreRoleLimitationsPhysical(),
                 comment="Role limitations due to physical health score "
                 "(0-100, higher better)"),
            dict(name="role_limitations_emotional", cctype="FLOAT",
                 value=self.scoreRoleLimitationsEmotional(),
                 comment="Role limitations due to emotional problems score "
                 "(0-100, higher better)"),
            dict(name="energy", cctype="FLOAT",
                 value=self.scoreEnergy(),
                 comment="Energy/fatigue score (0-100, higher better)"),
            dict(name="emotional_wellbeing", cctype="FLOAT",
                 value=self.scoreEmotionalWellbeing(),
                 comment="Emotional well-being score (0-100, higher better)"),
            dict(name="social_functioning", cctype="FLOAT",
                 value=self.scoreSocialFunctioning(),
                 comment="Social functioning score (0-100, higher better)"),
            dict(name="pain", cctype="FLOAT",
                 value=self.scorePain(),
                 comment="Pain score (0-100, higher better)"),
            dict(name="general_health", cctype="FLOAT",
                 value=self.scoreGeneralHealth(),
                 comment="General health score (0-100, higher better)"),
        ]

    # Scoring
    def recode(self, q):
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
        elif q >= 3 and q <= 12:
            # 1 => 0, 2 => 50, 3 => 100
            if x > 3:
                return None
            return 50 * (x - 1)
        elif q >= 13 and q <= 19:
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

    def scorePhysicalFunctioning(self):
        return mean([self.recode(3), self.recode(4), self.recode(5),
                     self.recode(6), self.recode(7), self.recode(8),
                     self.recode(9), self.recode(10), self.recode(11),
                     self.recode(12)])

    def scoreRoleLimitationsPhysical(self):
        return mean([self.recode(13), self.recode(14), self.recode(15),
                     self.recode(16)])

    def scoreRoleLimitationsEmotional(self):
        return mean([self.recode(17), self.recode(18), self.recode(19)])

    def scoreEnergy(self):
        return mean([self.recode(23), self.recode(27), self.recode(29),
                     self.recode(31)])

    def scoreEmotionalWellbeing(self):
        return mean([self.recode(24), self.recode(25), self.recode(26),
                     self.recode(28), self.recode(30)])

    def scoreSocialFunctioning(self):
        return mean([self.recode(20), self.recode(32)])

    def scorePain(self):
        return mean([self.recode(21), self.recode(22)])

    def scoreGeneralHealth(self):
        return mean([self.recode(1), self.recode(33), self.recode(34),
                     self.recode(35), self.recode(36)])

    def format_float_for_display(self, val):
        if val is None:
            return None
        return "{:.1f}".format(val)

    def scoreOverall(self):
        values = []
        for q in range(1, self.NQUESTIONS + 1):
            values.append(self.recode(q))
        return mean(values)

    def section_row_html(self, text):
        return tr_span_col(text, cols=3, tr_class="subheading")

    def answer_text(self, q, v):
        if v is None:
            return None
        # WSTRING has its own validity checking, so we can do:
        if q == 1 or q == 2 or (q >= 20 and q <= 22) or q == 32:
            return WSTRING("rand36_q" + str(q) + "_option" + str(v))
        elif q >= 3 and q <= 12:
            return WSTRING("rand36_activities_option" + str(v))
        elif q >= 13 and q <= 19:
            return WSTRING("rand36_yesno_option" + str(v))
        elif q >= 23 and q <= 31:
            return WSTRING("rand36_last4weeks_option" + str(v))
        elif q >= 33 and q <= 36:
            return WSTRING("rand36_q33to36_option" + str(v))
        else:
            return None

    def answer_row_html(self, q):
        qtext = WSTRING("rand36_q" + str(q))
        v = getattr(self, "q" + str(q))
        atext = self.answer_text(q, v)
        s = self.recode(q)
        return tr(
            qtext,
            answer(v) + ": " + answer(atext),
            answer(s, formatter_answer=identity)
        )

    def scoreline(self, text, footnote_num, score):
        return tr(
            text + " <sup>[{}]</sup>".format(footnote_num),
            answer(score) + " / 100"
        )

    def get_task_html(self):
        ANSWER_DICT = {None: "?"}
        for option in range(0, 3):
            ANSWER_DICT[option] = str(option) + " – " + \
                WSTRING("phq15_a" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += self.scoreline(
            WSTRING("rand36_score_overall"), 1,
            self.format_float_for_display(self.scoreOverall()))
        h += self.scoreline(
            WSTRING("rand36_score_physical_functioning"), 2,
            self.format_float_for_display(self.scorePhysicalFunctioning()))
        h += self.scoreline(
            WSTRING("rand36_score_role_limitations_physical"), 3,
            self.format_float_for_display(self.scoreRoleLimitationsPhysical()))
        h += self.scoreline(
            WSTRING("rand36_score_role_limitations_emotional"), 4,
            self.format_float_for_display(
                self.scoreRoleLimitationsEmotional()))
        h += self.scoreline(
            WSTRING("rand36_score_energy"), 5,
            self.format_float_for_display(self.scoreEnergy()))
        h += self.scoreline(
            WSTRING("rand36_score_emotional_wellbeing"), 6,
            self.format_float_for_display(self.scoreEmotionalWellbeing()))
        h += self.scoreline(
            WSTRING("rand36_score_social_functioning"), 7,
            self.format_float_for_display(self.scoreSocialFunctioning()))
        h += self.scoreline(
            WSTRING("rand36_score_pain"), 8,
            self.format_float_for_display(self.scorePain()))
        h += self.scoreline(
            WSTRING("rand36_score_general_health"), 9,
            self.format_float_for_display(self.scoreGeneralHealth()))
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
        h += self.section_row_html(WSTRING("rand36_activities_q"))
        for q in range(3, 12 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html(
            WSTRING("rand36_work_activities_physical_q"))
        for q in range(13, 16 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html(
            WSTRING("rand36_work_activities_emotional_q"))
        for q in range(17, 19 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html("")
        h += self.answer_row_html(20)
        h += self.section_row_html("")
        for q in range(21, 22 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html(WSTRING("rand36_last4weeks_q_a") + " " +
                                   WSTRING("rand36_last4weeks_q_b"))
        for q in range(23, 31 + 1):
            h += self.answer_row_html(q)
        h += self.section_row_html("")
        for q in [32]:
            h += self.answer_row_html(q)
        h += self.section_row_html(WSTRING("rand36_q33to36stem"))
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
