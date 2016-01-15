#!/usr/bin/env python3
# cope.py

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
    PV,
    STANDARD_TASK_FIELDSPECS,
)
from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import tr_qa
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# COPE_Brief
# =============================================================================

class CopeBrief(Task):
    NQUESTIONS = 28
    RELATIONSHIP_OTHER_CODE = 0
    RELATIONSHIPS_FIRST = 0
    RELATIONSHIPS_FIRST_NON_OTHER = 1
    RELATIONSHIPS_LAST = 9
    TASK_FIELDSPECS = [
        dict(name="completed_by_patient", cctype="INT", pv=PV.BIT,
             comment="Task completed by patient? (0 no, 1 yes)"),
        dict(name="completed_by", cctype="TEXT",
             comment="Name of person task completed by (if not by patient)"),
        dict(name="relationship_to_patient", cctype="INT", min=0, max=9,
             comment="Relationship of responder to patient (0 other, 1 wife, "
                     "2 husband, 3 daughter, 4 son, 5 sister, 6 brother, "
                     "7 mother, 8 father, 9 friend)"),
        dict(name="relationship_to_patient_other", cctype="TEXT",
             comment="Relationship of responder to patient (if OTHER chosen)"),
    ] + repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=3,
        comment_fmt="Q{n}, {s} (0 not at all - 3 a lot)",
        comment_strings=[
            "work/activities to take mind off",  # 1
            "concentrating efforts on doing something about it",
            "saying it's unreal",
            "alcohol/drugs to feel better",
            "emotional support from others",  # 5
            "given up trying to deal with it",
            "taking action to make situation better",
            "refusing to believe it's happened",
            "saying things to let unpleasant feelings escape",
            "getting help/advice from others",  # 10
            "alcohol/drugs to get through it",
            "trying to see it in a more positive light",
            "criticizing myself",
            "trying to come up with a strategy",
            "getting comfort/understanding from someone",  # 15
            "giving up the attempt to cope",
            "looking for something good in what's happening",
            "making jokes about it",
            "doing something to think about it less",
            "accepting reality of the fact it's happened",  # 20
            "expressing negative feelings",
            "seeking comfort in religion/spirituality",
            "trying to get help/advice from others about what to do",
            "learning to live with it",
            "thinking hard about what steps to take",  # 25
            "blaming myself",
            "praying/meditating",
            "making fun of the situation"  # 28
        ])
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "cope_brief"

    @classmethod
    def get_taskshortname(cls):
        return "COPE-Brief"

    @classmethod
    def get_tasklongname(cls):
        return "Brief COPE Inventory"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + cls.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return False

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="self_distraction", cctype="INT",
                 value=self.self_distraction(),
                 comment="Self-distraction (2-8)"),
            dict(name="active_coping", cctype="INT",
                 value=self.active_coping(),
                 comment="Active coping (2-8)"),
            dict(name="denial", cctype="INT",
                 value=self.denial(),
                 comment="Denial (2-8)"),
            dict(name="substance_use", cctype="INT",
                 value=self.substance_use(),
                 comment="Substance use (2-8)"),
            dict(name="emotional_support", cctype="INT",
                 value=self.emotional_support(),
                 comment="Use of emotional support (2-8)"),
            dict(name="instrumental_support", cctype="INT",
                 value=self.instrumental_support(),
                 comment="Use of instrumental support (2-8)"),
            dict(name="behavioural_disengagement", cctype="INT",
                 value=self.behavioural_disengagement(),
                 comment="Behavioural disengagement (2-8)"),
            dict(name="venting", cctype="INT",
                 value=self.venting(),
                 comment="Venting (2-8)"),
            dict(name="positive_reframing", cctype="INT",
                 value=self.positive_reframing(),
                 comment="Positive reframing (2-8)"),
            dict(name="planning", cctype="INT",
                 value=self.planning(),
                 comment="Planning (2-8)"),
            dict(name="humour", cctype="INT",
                 value=self.humour(),
                 comment="Humour (2-8)"),
            dict(name="acceptance", cctype="INT",
                 value=self.acceptance(),
                 comment="Acceptance (2-8)"),
            dict(name="religion", cctype="INT",
                 value=self.religion(),
                 comment="Religion (2-8)"),
            dict(name="self_blame", cctype="INT",
                 value=self.self_blame(),
                 comment="Self-blame (2-8)"),
        ]

    def is_complete_responder(self):
        if self.completed_by_patient is None:
            return False
        if self.completed_by_patient:
            return True
        if not self.completed_by or self.relationship_to_patient is None:
            return False
        if (self.relationship_to_patient == self.RELATIONSHIP_OTHER_CODE and
                not self.relationship_to_patient_other):
            return False
        return True

    def is_complete(self):
        return (
            self.is_complete_responder() and
            self.are_all_fields_complete(
                ["q{}".format(n) for n in range(1, self.NQUESTIONS + 1)]) and
            self.field_contents_valid()
        )

    def self_distraction(self):
        return self.sum_fields(["q1", "q19"])

    def active_coping(self):
        return self.sum_fields(["q2", "q7"])

    def denial(self):
        return self.sum_fields(["q3", "q8"])

    def substance_use(self):
        return self.sum_fields(["q4", "q11"])

    def emotional_support(self):
        return self.sum_fields(["q5", "q15"])

    def instrumental_support(self):
        return self.sum_fields(["q10", "q23"])

    def behavioural_disengagement(self):
        return self.sum_fields(["q6", "q16"])

    def venting(self):
        return self.sum_fields(["q9", "q21"])

    def positive_reframing(self):
        return self.sum_fields(["q12", "q17"])

    def planning(self):
        return self.sum_fields(["q14", "q25"])

    def humour(self):
        return self.sum_fields(["q18", "q28"])

    def acceptance(self):
        return self.sum_fields(["q20", "q24"])

    def religion(self):
        return self.sum_fields(["q22", "q27"])

    def self_blame(self):
        return self.sum_fields(["q13", "q26"])

    def get_task_html(self):
        ANSWER_DICT = {None: None}
        for option in range(0, 3 + 1):
            ANSWER_DICT[option] = (
                str(option) + " — " + WSTRING("copebrief_a" + str(option))
            )
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa("Self-distraction (Q1, Q19)", self.self_distraction())
        h += tr_qa("Active coping (Q2, Q7)", self.active_coping())
        h += tr_qa("Denial (Q3, Q8)", self.denial())
        h += tr_qa("Substance use (Q4, Q11)", self.substance_use())
        h += tr_qa("Use of emotional support (Q5, Q15)",
                   self.emotional_support())
        h += tr_qa("Use of instrumental support (Q10, Q23)",
                   self.instrumental_support())
        h += tr_qa("Behavioural disengagement (Q6, Q16)",
                   self.behavioural_disengagement())
        h += tr_qa("Venting (Q9, Q21)", self.venting())
        h += tr_qa("Positive reframing (Q12, Q17)", self.positive_reframing())
        h += tr_qa("Planning (Q14, Q25)", self.planning())
        h += tr_qa("Humour (Q18, Q28)", self.humour())
        h += tr_qa("Acceptance (Q20, Q24)", self.acceptance())
        h += tr_qa("Religion (Q22, Q27)", self.religion())
        h += tr_qa("Self-blame (Q13, Q26)", self.self_blame())
        h += """
                </table>
            </div>
            <div class="explanation">
                Individual items are scored 0–3 (as in Carver 1997 PMID
                16250744), not 1–4 (as in
                http://www.psy.miami.edu/faculty/ccarver/sclBrCOPE.html).
                Summaries, which are all
                based on two items, are therefore scored 0–6.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        for q in range(1, self.NQUESTIONS + 1):
            h += tr_qa(
                "Q{}. {}".format(q, WSTRING("copebrief_q" + str(q))),
                get_from_dict(ANSWER_DICT, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
        """
        return h
