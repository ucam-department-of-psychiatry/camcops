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

from __future__ import division
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    get_yes_no,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CTV_DICTLIST_INCOMPLETE,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)

# =============================================================================
# Constants
# =============================================================================

MISSING_VALUE = -99
PERMITTED_VALUES = range(1, 4 + 1) + [MISSING_VALUE]
COPYRIGHT_DIV = u"""
    <div class="copyright">
        DEMQOL/DEMQOL-Proxy: Copyright © Institute of Psychiatry, King’s
        College London. Reproduced with permission.
    </div>
"""


# =============================================================================
# Common scoring function
# =============================================================================

def calc_total_score(obj, n_scored_questions, reverse_score_qs,
                     minimum_n_for_total_score):
    """Returns (total, extrapolated?)."""
    n = 0
    total = 0
    for q in xrange(1, n_scored_questions + 1):
        x = getattr(obj, "q" + str(n))
        if x is None or x == MISSING_VALUE:
            continue
        if q in reverse_score_qs:
            x = 5 - x
        n += 1
        total += x
    if n < minimum_n_for_total_score:
        return (None, False)
    if n < n_scored_questions:
        return (n_scored_questions * total / n, True)
    return (total, True)


# =============================================================================
# DEMQOL
# =============================================================================

class Demqol(Task):
    NQUESTIONS = 29
    N_SCORED_QUESTIONS = 28
    MINIMUM_N_FOR_TOTAL_SCORE = 14
    REVERSE_SCORE = [1, 3, 5, 6, 10, 29]  # questions scored backwards
    MIN_SCORE = N_SCORED_QUESTIONS
    MAX_SCORE = MIN_SCORE * 4
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, N_SCORED_QUESTIONS, pv=PERMITTED_VALUES,
        comment_fmt="Q{n}. {s} (1 a lot - 4 not at all; -99 no response)",
        comment_strings=[
            # 1-13
            "cheerful", "worried/anxious", "enjoying life", "frustrated",
            "confident", "full of energy", "sad", "lonely", "distressed",
            "lively", "irritable", "fed up", "couldn't do things",
            # 14-19
            "worried: forget recent", "worried: forget people",
            "worried: forget day", "worried: muddled",
            "worried: difficulty making decisions",
            "worried: poor concentration",
            # 20-28
            "worried: not enough company", "worried: get on with people close",
            "worried: affection", "worried: people not listening",
            "worried: making self understood", "worried: getting help",
            "worried: toilet", "worried: feel in self",
            "worried: health overall",
        ]
    ) + [
        dict(name="q29", cctype="INT", pv=PERMITTED_VALUES,
             comment="Q29. Overall quality of life (1 very good - 4 poor; "
                     "-99 no response)."),

    ]
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "demqol"

    @classmethod
    def get_taskshortname(cls):
        return "DEMQOL"

    @classmethod
    def get_tasklongname(cls):
        return "Dementia Quality of Life measure, self-report version"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + cls.TASK_FIELDSPECS

    def is_complete(self):
        return self.field_contents_valid() and self.are_all_fields_complete(
            repeat_fieldname("q", 1, self.NQUESTIONS))

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "DEMQOL total score",
                "axis_label": (
                    "Total score (range {}-{}, higher better)".format(
                        self.MIN_SCORE, self.MAX_SCORE)),
                "axis_min": self.MIN_SCORE - 0.5,
                "axis_max": self.MAX_SCORE + 0.5,
            },
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": u"total score {} (range {}-{}, higher better)".format(
                       self.total_score(), self.MIN_SCORE, self.MAX_SCORE)
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(
                name="total", cctype="INT",
                value=self.total_score(),
                comment=(
                    "Total score ({}-{})".format(
                        self.MIN_SCORE, self.MAX_SCORE))
                ),
        ]

    def totalscore_extrapolated(self):
        return calc_total_score(
            obj=self,
            n_scored_questions=self.N_SCORED_QUESTIONS,
            reverse_score_qs=self.REVERSE_SCORE,
            minimum_n_for_total_score=self.MINIMUM_N_FOR_TOTAL_SCORE
        )

    def total_score(self):
        (total, extrapolated) = self.totalscore_extrapolated()
        return total

    def get_task_html(self):
        (total, extrapolated) = self.totalscore_extrapolated()
        MAIN_DICT = {
            None: None,
            1: u"1 — " + WSTRING("demqol_a1"),
            2: u"2 — " + WSTRING("demqol_a2"),
            3: u"3 — " + WSTRING("demqol_a3"),
            4: u"4 — " + WSTRING("demqol_a4"),
            MISSING_VALUE: u"—99 — " + WSTRING("demqol_no_response")
        }
        LASTQ_DICT = {
            None: None,
            1: u"1 — " + WSTRING("demqol_q29_a1"),
            2: u"2 — " + WSTRING("demqol_q29_a2"),
            3: u"3 — " + WSTRING("demqol_q29_a3"),
            4: u"4 — " + WSTRING("demqol_q29_a4"),
            MISSING_VALUE: u"—99 — " + WSTRING("demqol_no_response")
        }
        h = u"""
            <div class="summary">
                <table class="summary">
                    {is_complete_tr}
                    <tr>
                        <td>Total score ({min}–{max}), higher better</td>
                        <td>{t}</td>
                    </tr>
                    <tr>
                        <td>Total score extrapolated from incomplete
                        responses?</td>
                        <td>{e}</td>
                    </tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            is_complete_tr=self.get_is_complete_tr(),
            min=self.MIN_SCORE,
            max=self.MAX_SCORE,
            t=answer(total),
            e=answer(get_yes_no(extrapolated)),
        )
        for n in xrange(1, self.N_SCORED_QUESTIONS + 1):
            nstr = str(n)
            h += tr_qa(WSTRING("demqol_q" + nstr),
                       get_from_dict(MAIN_DICT, getattr(self, "q" + nstr)))
        nstr = str(self.NQUESTIONS)
        h += tr_qa(WSTRING("demqol_q" + nstr),
                   get_from_dict(LASTQ_DICT, getattr(self, "q" + nstr)))
        h += u"""
            </table>
        """ + COPYRIGHT_DIV
        return h


# =============================================================================
# DEMQOL-Proxy
# =============================================================================

class DemqolProxy(Task):
    NQUESTIONS = 32
    N_SCORED_QUESTIONS = 31
    MINIMUM_N_FOR_TOTAL_SCORE = 16
    REVERSE_SCORE = [1, 4, 6, 8, 11, 32]  # questions scored backwards
    MIN_SCORE = N_SCORED_QUESTIONS
    MAX_SCORE = MIN_SCORE * 4
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, N_SCORED_QUESTIONS, pv=PERMITTED_VALUES,
        comment_fmt="Q{n}. {s} (1 a lot - 4 not at all; -99 no response)",
        comment_strings=[
            # 1-11
            "cheerful", "worried/anxious", "frustrated", "full of energy",
            "sad", "content", "distressed", "lively", "irritable", "fed up",
            "things to look forward to",
            # 12-20
            "worried: memory in general", "worried: forget distant",
            "worried: forget recent", "worried: forget people",
            "worried: forget place", "worried: forget day", "worried: muddled",
            "worried: difficulty making decisions",
            "worried: making self understood",
            # 21-31
            "worried: keeping clean", "worried: keeping self looking nice",
            "worried: shopping", "worried: using money to pay",
            "worried: looking after finances", "worried: taking longer",
            "worried: getting in touch with people",
            "worried: not enough company",
            "worried: not being able to help others",
            "worried: not playing a useful part", "worried: physical health",
        ]
    ) + [
        dict(name="q32", cctype="INT", pv=PERMITTED_VALUES,
             comment="Q32. Overall quality of life (1 very good - 4 poor; "
                     "-99 no response)."),

    ]
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "demqolproxy"

    @classmethod
    def get_taskshortname(cls):
        return "DEMQOL-Proxy"

    @classmethod
    def get_tasklongname(cls):
        return "Dementia Quality of Life measure, proxy version"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + cls.TASK_FIELDSPECS

    def is_complete(self):
        return self.field_contents_valid() and self.are_all_fields_complete(
            repeat_fieldname("q", 1, self.NQUESTIONS))

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "DEMQOL-Proxy total score",
                "axis_label": (
                    "Total score (range {}-{}, higher better)".format(
                        self.MIN_SCORE, self.MAX_SCORE)
                ),
                "axis_min": self.MIN_SCORE - 0.5,
                "axis_max": self.MAX_SCORE + 0.5,
            },
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": u"total score {} (range {}-{}, higher better)".format(
                       self.total_score(), self.MIN_SCORE, self.MAX_SCORE)
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(
                name="total", cctype="INT",
                value=self.total_score(),
                comment="Total score ({}-{})".format(
                    self.MIN_SCORE, self.MAX_SCORE)),
        ]

    def totalscore_extrapolated(self):
        return calc_total_score(
            obj=self,
            n_scored_questions=self.N_SCORED_QUESTIONS,
            reverse_score_qs=self.REVERSE_SCORE,
            minimum_n_for_total_score=self.MINIMUM_N_FOR_TOTAL_SCORE
        )

    def total_score(self):
        (total, extrapolated) = self.totalscore_extrapolated()
        return total

    def get_task_html(self):
        (total, extrapolated) = self.totalscore_extrapolated()
        MAIN_DICT = {
            None: None,
            1: u"1 — " + WSTRING("demqol_a1"),
            2: u"2 — " + WSTRING("demqol_a2"),
            3: u"3 — " + WSTRING("demqol_a3"),
            4: u"4 — " + WSTRING("demqol_a4"),
            MISSING_VALUE: u"—99 — " + WSTRING("demqol_no_response")
        }
        LASTQ_DICT = {
            None: None,
            1: u"1 — " + WSTRING("demqol_q29_a1"),
            2: u"2 — " + WSTRING("demqol_q29_a2"),
            3: u"3 — " + WSTRING("demqol_q29_a3"),
            4: u"4 — " + WSTRING("demqol_q29_a4"),
            MISSING_VALUE: u"—99 — " + WSTRING("demqol_no_response")
        }
        h = u"""
            <div class="summary">
                <table class="summary">
                    {is_complete_tr}
                    <tr>
                        <td>Total score ({min}–{max}), higher better</td>
                        <td>{t}</td>
                    </tr>
                    <tr>
                        <td>Total score extrapolated from incomplete
                        responses?</td>
                        <td>{e}</td>
                    </tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            is_complete_tr=self.get_is_complete_tr(),
            min=self.MIN_SCORE,
            max=self.MAX_SCORE,
            t=answer(total),
            e=answer(get_yes_no(extrapolated)),
        )
        for n in xrange(1, self.N_SCORED_QUESTIONS + 1):
            nstr = str(n)
            h += tr_qa(WSTRING("demqolproxy_q" + nstr),
                       get_from_dict(MAIN_DICT, getattr(self, "q" + nstr)))
        nstr = str(self.NQUESTIONS)
        h += tr_qa(WSTRING("demqolproxy_q" + nstr),
                   get_from_dict(LASTQ_DICT, getattr(self, "q" + nstr)))
        h += u"""
            </table>
        """ + COPYRIGHT_DIV
        return h
