#!/usr/bin/env python3
# ifs.py

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

from ..cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
    INVALID_VALUE,
    PV,
)
from ..cc_modules.cc_html import (
    answer,
    get_correct_incorrect_none,
    td,
    tr,
    tr_qa,
)
# from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import Task


# =============================================================================
# IFS
# =============================================================================

class Ifs(Task):
    Q4_DIGIT_LENGTHS = list(range(2, 7 + 1))
    Q6_SEQUENCE_NUMS = list(range(1, 4 + 1))
    Q7_PROVERB_NUMS = list(range(1, 3 + 1))
    Q8_SENTENCE_NUMS = list(range(1, 3 + 1))
    SIMPLE_Q = (
        ["q1", "q2", "q3", "q5"] +
        ["q6_seq{}".format(n) for n in Q6_SEQUENCE_NUMS] +
        ["q7_proverb{}".format(n) for n in Q7_PROVERB_NUMS] +
        ["q8_sentence{}".format(n) for n in Q8_SENTENCE_NUMS]
    )

    tablename = "ifs"
    shortname = "IFS"
    longname = "INECO Frontal Screening"
    fieldspecs = [
        dict(name="q1", cctype="INT", pv=[0, 1, 2, 3],
             comment="Q1. Motor series (motor programming)"),
        dict(name="q2", cctype="INT", pv=[0, 1, 2, 3],
             comment="Q2. Conflicting instructions "
                     "(interference sensitivity)"),
        dict(name="q3", cctype="INT", pv=[0, 1, 2, 3],
             comment="Q3. Go/no-go (inhibitory control)"),
    ]
    for seqlen in Q4_DIGIT_LENGTHS:
        fieldspecs.extend([
            dict(
                name="q4_len{}_1".format(seqlen), cctype="BOOL", pv=PV.BIT,
                comment="Q4. Digits backward, length {}, trial 1".format(
                    seqlen)),
            dict(
                name="q4_len{}_2".format(seqlen), cctype="BOOL", pv=PV.BIT,
                comment="Q4. Digits backward, length {}, trial 2".format(
                    seqlen)),
        ])
    fieldspecs.extend([
        dict(name="q5", cctype="INT", pv=[0, 1, 2],
             comment="Q5. Verbal working memory"),
    ])
    for n in Q6_SEQUENCE_NUMS:
        fieldspecs.extend([
            dict(
                name="q6_seq{}".format(n), cctype="INT", pv=[0, 1],
                comment="Q6. Spatial working memory, sequence {}".format(n)),
        ])
    for n in Q7_PROVERB_NUMS:
        fieldspecs.extend([
            dict(name="q7_proverb{}".format(n), cctype="FLOAT",
                 min=0, max=1,
                 comment="Q7. Proverb {} (1 = correct explanation, "
                         "0.5 = example, 0 = neither)".format(n)),
        ])
    for n in Q8_SENTENCE_NUMS:
        fieldspecs.extend([
            dict(name="q8_sentence{}".format(n), cctype="INT", pv=[0, 1, 2],
                 comment="Q8. Hayling, sentence {}".format(n)),
        ])
    has_clinician = True

    def get_trackers(self):
        scoredict = self.get_score()
        return [
            {
                "value": scoredict['total'],
                "plot_label": "IFS total score (higher is better)",
                "axis_label": "Total score (out of 30)",
                "axis_min": -0.5,
                "axis_max": 30.5,
            },
            {
                "value": scoredict['wm'],
                "plot_label": "IFS working memory index (higher is better)",
                "axis_label": "Total score (out of 10)",
                "axis_min": -0.5,
                "axis_max": 10.5,
            },
        ]

    def get_summaries(self):
        scoredict = self.get_score()
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="FLOAT",
                 value=scoredict['total'],
                 comment="Total (out of 30, higher better)"),
            dict(name="wm", cctype="INT",
                 value=scoredict['wm'],
                 comment="Working memory index (out of 10; sum of Q4 + Q6"),
        ]

    def get_clinical_text(self):
        scoredict = self.get_score()
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [
            {
                "content": "Total: {t}/30; working memory index {w}/10".format(
                    t=scoredict['total'],
                    w=scoredict['wm'],
                )
            }
        ]

    def get_score(self):
        q1 = getattr(self, "q1", 0) or 0
        q2 = getattr(self, "q2", 0) or 0
        q3 = getattr(self, "q3", 0) or 0
        q4 = 0
        for seqlen in self.Q4_DIGIT_LENGTHS:
            val1 = getattr(self, "q4_len{}_1".format(seqlen))
            val2 = getattr(self, "q4_len{}_2".format(seqlen))
            if val1 or val2:
                q4 += 1
            if not val1 and not val2:
                break
        q5 = getattr(self, "q5", 0) or 0
        q6 = self.sum_fields(["q6_seq" + str(s) for s in range(1, 4 + 1)])
        q7 = self.sum_fields(["q7_proverb" + str(s) for s in range(1, 3 + 1)])
        q8 = self.sum_fields(["q8_sentence" + str(s) for s in range(1, 3 + 1)])
        total = q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8
        wm = q4 + q6  # working memory index (though not verbal)
        return dict(
            total=total,
            wm=wm
        )

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(self.SIMPLE_Q):
            return False
        for seqlen in self.Q4_DIGIT_LENGTHS:
            val1 = getattr(self, "q4_len{}_1".format(seqlen))
            val2 = getattr(self, "q4_len{}_2".format(seqlen))
            if val1 is None or val2 is None:
                return False
            if not val1 and not val2:
                return True  # all done
        return True

    def get_simple_tr_qa(self, qprefix):
        q = self.WXSTRING(qprefix + "_title")
        val = getattr(self, qprefix)
        if val is not None:
            a = self.WXSTRING(qprefix + "_a" + str(val))
        else:
            a = None
        return tr_qa(q, a)

    def get_task_html(self):
        scoredict = self.get_score()
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total (higher better)</td>
                        <td>{total} / 30</td>
                    </td>
                    <tr>
                        <td>Working memory index <sup>1</sup></td>
                        <td>{wm} / 10</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(scoredict['total']),
            wm=answer(scoredict['wm']),
        )

        # Q1
        h += self.get_simple_tr_qa("q1")
        # Q2
        h += self.get_simple_tr_qa("q2")
        # Q3
        h += self.get_simple_tr_qa("q3")
        # Q4
        h += tr(td(self.WXSTRING("q4_title")), td("", td_class="subheading"),
                literal=True)
        required = True
        for n in self.Q4_DIGIT_LENGTHS:
            val1 = getattr(self, "q4_len{}_1".format(n))
            val2 = getattr(self, "q4_len{}_2".format(n))
            q = (
                "… " +
                self.WXSTRING("q4_seq_len{}_1".format(n)) +
                " / " + self.WXSTRING("q4_seq_len{}_2".format(n))
            )
            if required:
                score = 1 if val1 or val2 else 0
                a = (
                    answer(get_correct_incorrect_none(val1)) +
                    " / " + answer(get_correct_incorrect_none(val2)) +
                    " (scores {})".format(score)
                )
            else:
                a = ""
            h += tr(q, a)
            if not val1 and not val2:
                required = False
        # Q5
        h += self.get_simple_tr_qa("q5")
        # Q6
        h += tr(td(self.WXSTRING("q6_title")), td("", td_class="subheading"),
                literal=True)
        for n in self.Q6_SEQUENCE_NUMS:
            nstr = str(n)
            val = getattr(self, "q6_seq" + nstr)
            h += tr_qa("… " + self.WXSTRING("q6_seq" + nstr), val)
        # Q7
        q7map = {
            None: None,
            1: self.WXSTRING("q7_a_1"),
            0.5: self.WXSTRING("q7_a_half"),
            0: self.WXSTRING("q7_a_0"),
        }
        h += tr(td(self.WXSTRING("q7_title")), td("", td_class="subheading"),
                literal=True)
        for n in self.Q7_PROVERB_NUMS:
            nstr = str(n)
            val = getattr(self, "q7_proverb" + nstr)
            a = q7map.get(val, INVALID_VALUE)
            h += tr_qa("… " + self.WXSTRING("q7_proverb" + nstr), a)
        # Q8
        q8map = {
            None: None,
            2: self.WXSTRING("q8_a2"),
            1: self.WXSTRING("q8_a1"),
            0: self.WXSTRING("q8_a0"),
        }
        h += tr(td(self.WXSTRING("q8_title")), td("", td_class="subheading"),
                literal=True)
        for n in self.Q8_SENTENCE_NUMS:
            nstr = str(n)
            val = getattr(self, "q8_sentence" + nstr)
            a = q8map.get(val, INVALID_VALUE)
            h += tr_qa("… " + self.WXSTRING("q8_sentence_" + nstr), a)

        h += """
            </table>
            <div class="footnotes">
                [1] Sum of scores for Q4 + Q6.
            </div>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
