#!/usr/bin/env python
# camcops_server/tasks/ifs.py

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

from typing import Dict, List

from ..cc_modules.cc_constants import (
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
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo


# =============================================================================
# IFS
# =============================================================================

class Ifs(Task):
    tablename = "ifs"
    shortname = "IFS"
    longname = "INECO Frontal Screening"
    has_clinician = True
    provides_trackers = True

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

    def get_trackers(self) -> List[TrackerInfo]:
        scoredict = self.get_score()
        return [
            TrackerInfo(
                value=scoredict['total'],
                plot_label="IFS total score (higher is better)",
                axis_label="Total score (out of 30)",
                axis_min=-0.5,
                axis_max=30.5
            ),
            TrackerInfo(
                value=scoredict['wm'],
                plot_label="IFS working memory index (higher is better)",
                axis_label="Total score (out of 10)",
                axis_min=-0.5,
                axis_max=10.5
            ),
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

    def get_clinical_text(self) -> List[CtvInfo]:
        scoredict = self.get_score()
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="Total: {t}/30; working memory index {w}/10".format(
                t=scoredict['total'],
                w=scoredict['wm'],
            )
        )]

    def get_score(self) -> Dict:
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

    def is_complete(self) -> bool:
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

    def get_simple_tr_qa(self, qprefix: str) -> str:
        q = self.wxstring(qprefix + "_title")
        val = getattr(self, qprefix)
        if val is not None:
            a = self.wxstring(qprefix + "_a" + str(val))
        else:
            a = None
        return tr_qa(q, a)

    def get_task_html(self) -> str:
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
        h += tr(td(self.wxstring("q4_title")), td("", td_class="subheading"),
                literal=True)
        required = True
        for n in self.Q4_DIGIT_LENGTHS:
            val1 = getattr(self, "q4_len{}_1".format(n))
            val2 = getattr(self, "q4_len{}_2".format(n))
            q = (
                "… " +
                self.wxstring("q4_seq_len{}_1".format(n)) +
                " / " + self.wxstring("q4_seq_len{}_2".format(n))
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
        h += tr(td(self.wxstring("q6_title")), td("", td_class="subheading"),
                literal=True)
        for n in self.Q6_SEQUENCE_NUMS:
            nstr = str(n)
            val = getattr(self, "q6_seq" + nstr)
            h += tr_qa("… " + self.wxstring("q6_seq" + nstr), val)
        # Q7
        q7map = {
            None: None,
            1: self.wxstring("q7_a_1"),
            0.5: self.wxstring("q7_a_half"),
            0: self.wxstring("q7_a_0"),
        }
        h += tr(td(self.wxstring("q7_title")), td("", td_class="subheading"),
                literal=True)
        for n in self.Q7_PROVERB_NUMS:
            nstr = str(n)
            val = getattr(self, "q7_proverb" + nstr)
            a = q7map.get(val, INVALID_VALUE)
            h += tr_qa("… " + self.wxstring("q7_proverb" + nstr), a)
        # Q8
        q8map = {
            None: None,
            2: self.wxstring("q8_a2"),
            1: self.wxstring("q8_a1"),
            0: self.wxstring("q8_a0"),
        }
        h += tr(td(self.wxstring("q8_title")), td("", td_class="subheading"),
                literal=True)
        for n in self.Q8_SENTENCE_NUMS:
            nstr = str(n)
            val = getattr(self, "q8_sentence" + nstr)
            a = q8map.get(val, INVALID_VALUE)
            h += tr_qa("… " + self.wxstring("q8_sentence_" + nstr), a)

        h += """
            </table>
            <div class="footnotes">
                [1] Sum of scores for Q4 + Q6.
            </div>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
