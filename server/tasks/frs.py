#!/usr/bin/env python3
# frs.py

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

import pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
)
from cc_modules.cc_html import (
    tr_qa,
)
from cc_modules.cc_math import safe_logit
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task


# =============================================================================
# FRS
# =============================================================================

"""

SCORING
Confirmed by Eneida Mioshi 2015-01-20; "sometimes" and "always" score the same.

LOGIT

Quick R definitions:
    logit <- function(x) log(x / (1 - x))
    invlogit <- function(x) exp(x) / (exp(x) + 1)

See comparison file published_calculated_FRS_scoring.ods
and correspondence with Eneida 2015-01-20.

"""

NEVER = 0
SOMETIMES = 1
ALWAYS = 2
NA = -99
NA_QUESTIONS = [9, 10, 11, 13, 14, 15, 17, 18, 19, 20, 21, 27]
SPECIAL_NA_TEXT_QUESTIONS = [27]
NO_SOMETIMES_QUESTIONS = [30]
SCORE = {
    NEVER: 1,
    SOMETIMES: 0,
    ALWAYS: 0
}
NQUESTIONS = 30
QUESTION_SNIPPETS = [
    "behaviour / lacks interest",  # 1
    "behaviour / lacks affection",
    "behaviour / uncooperative",
    "behaviour / confused/muddled in unusual surroundings",
    "behaviour / restless",  # 5
    "behaviour / impulsive",
    "behaviour / forgets day",
    "outings / transportation",
    "outings / shopping",
    "household / lacks interest/motivation",  # 10
    "household / difficulty completing chores",
    "household / telephoning",
    "finances / lacks interest",
    "finances / problems organizing finances",
    "finances / problems organizing correspondence",  # 15
    "finances / difficulty with cash",
    "medication / problems taking medication at correct time",
    "medication / problems taking medication as prescribed",
    "mealprep / lacks interest/motivation",
    "mealprep / difficulty organizing meal prep",  # 20
    "mealprep / problems preparing meal on own",
    "mealprep / lacks initiative to eat",
    "mealprep / difficulty choosing utensils/seasoning",
    "mealprep / problems eating",
    "mealprep / wants to eat same foods repeatedly",  # 25
    "mealprep / prefers sweet foods more",
    "selfcare / problems choosing appropriate clothing",
    "selfcare / incontinent",
    "selfcare / cannot be left at home safely",
    "selfcare / bedbound",  # 30
]
DP = 3


def make_frs_fieldspec(n):
    pv = [NEVER, ALWAYS]
    pc = ["{} = never".format(NEVER), "{} = always".format(ALWAYS)]
    if n not in NO_SOMETIMES_QUESTIONS:
        pv.append(SOMETIMES)
        pc.append("{} = sometimes".format(SOMETIMES))
    if n in NA_QUESTIONS:
        pv.append(NA)
        pc.append("{} = N/A".format(NA))
    comment = "Q{}, {} ({})".format(n, QUESTION_SNIPPETS[n - 1],
                                    ", ".join(pc))
    return dict(
        name="q" + str(n),
        cctype="INT",
        comment=comment,
        pv=pv
    )


class Frs(Task):
    TASK_FIELDS = ["q" + str(n) for n in range(1, NQUESTIONS + 1)]

    tablename = "frs"
    shortname = "FRS"
    longname = "Frontotemporal Dementia Rating Scale"
    fieldspecs = [make_frs_fieldspec(n) for n in range(1, NQUESTIONS + 1)]
    fieldspecs.append(dict(name="comments", cctype="TEXT",
                           comment="Clinician's comments"))
    extrastring_taskname = "frs"
    has_clinician = True
    has_respondent = True

    def get_summaries(self):
        scoredict = self.get_score()
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=scoredict['total'],
                 comment="Total (0-n, higher better)"),
            dict(name="n", cctype="INT",
                 value=scoredict['n'],
                 comment="Number of applicable questions"),
            dict(name="score", cctype="FLOAT",
                 value=scoredict['score'],
                 comment="tcore / n"),
            dict(name="logit", cctype="FLOAT",
                 value=scoredict['logit'],
                 comment="log(score / (1 - score))"),
            dict(name="severity", cctype="TEXT",
                 value=scoredict['severity'],
                 comment="Severity"),
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        scoredict = self.get_score()
        return [{
            "content": "Total {total}/n, n = {n}, score = {score}, "
            "logit score = {logit}, severity = {severity}".format(
                total=scoredict['total'],
                n=scoredict['n'],
                score=scoredict['score'],
                logit=scoredict['logit'],
                severity=scoredict['severity'],
            )
        }]

    @staticmethod
    def get_severity(logit):
        # p1593 of Mioshi et al. (2010)
        # Copes with Infinity comparisons
        if logit >= 4.12:
            return "very mild"
        if logit >= 1.92:
            return "mild"
        if logit >= -0.40:
            return "moderate"
        if logit >= -2.58:
            return "severe"
        if logit >= -4.99:
            return "very severe"
        return "profound"

    def get_score(self):
        total = 0
        n = 0
        for q in range(1, NQUESTIONS + 1):
            value = getattr(self, "q" + str(q))
            if value is not None and value != NA:
                n += 1
                total += SCORE.get(value, 0)
        if n > 0:
            score = total / n
            logit = safe_logit(score)
            severity = self.get_severity(logit)
        else:
            score = None
            logit = None
            severity = ""
        return dict(total=total, n=n, score=score, logit=logit,
                    severity=severity)

    def is_complete(self):
        return (
            self.field_contents_valid()
            and self.is_respondent_complete()
            and self.are_all_fields_complete(self.TASK_FIELDS)
        )

    def get_answer(self, q):
        qstr = str(q)
        value = getattr(self, "q" + qstr)
        if value is None:
            return None
        prefix = "q" + qstr + "_a_"
        if value == ALWAYS:
            return self.WXSTRING(prefix + "always")
        if value == SOMETIMES:
            return self.WXSTRING(prefix + "sometimes")
        if value == NEVER:
            return self.WXSTRING(prefix + "never")
        if value == NA:
            if q in SPECIAL_NA_TEXT_QUESTIONS:
                return self.WXSTRING(prefix + "na")
            return WSTRING("NA")
        return None

    def get_task_html(self):
        scoredict = self.get_score()
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total (0–n, higher better) <sup>1</sup></td>
                        <td>{total}</td>
                    </td>
                    <tr>
                        <td>n (applicable questions)</td>
                        <td>{n}</td>
                    </td>
                    <tr>
                        <td>Score (total / n; 0–1)</td>
                        <td>{score}</td>
                    </td>
                    <tr>
                        <td>logit score (= log(score/[1 – score]))</td>
                        <td>{logit}</td>
                    </td>
                    <tr>
                        <td>Severity <sup>2</sup></td>
                        <td>{severity}</td>
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
            total=scoredict['total'],
            n=scoredict['n'],
            score=ws.number_to_dp(scoredict['score'], DP),
            logit=ws.number_to_dp(scoredict['logit'], DP),
            severity=scoredict['severity'],
        )
        for q in range(1, NQUESTIONS + 1):
            qtext = self.WXSTRING("q" + str(q) + "_q")
            atext = self.get_answer(q)
            h += tr_qa(qtext, atext)
        h += """
            </table>
            <div class="footnotes">
                [1] ‘Never’ scores 1 and ‘sometimes’/‘always’ both score 0,
                i.e. there is no scoring difference between ‘sometimes’ and
                ‘always’.
                [2] Where <i>x</i> is the logit score, severity is determined
                as follows (after Mioshi et al. 2010, Neurology 74: 1591, PMID
                20479357, with sharp cutoffs).
                <i>Very mild:</i> <i>x</i> ≥ 4.12.
                <i>Mild:</i> 1.92 ≤ <i>x</i> &lt; 4.12.
                <i>Moderate:</i> –0.40 ≤ <i>x</i> &lt; 1.92.
                <i>Severe:</i> –2.58 ≤ <i>x</i> &lt; –0.40.
                <i>Very severe:</i> –4.99 ≤ <i>x</i> &lt; –2.58.
                <i>Profound:</i> <i>x</i> &lt; –4.99.
            </div>
        """
        return h
