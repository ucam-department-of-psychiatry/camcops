#!/usr/bin/env python3
# frs.py

"""
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
"""

from typing import Dict, List, Optional

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_html import tr_qa
from ..cc_modules.cc_lang import BetweenDict
# from ..cc_modules.cc_math import safe_logit
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task


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

TABULAR_LOGIT_BETWEENDICT = BetweenDict({
    # tests a <= x < b
    (100, float("inf")): 5.39,  # from Python 3.5, can use math.inf
    (97, 100): 4.12,
    (93, 97): 3.35,
    (90, 93): 2.86,
    (87, 90): 2.49,
    (83, 87): 2.19,
    (80, 83): 1.92,
    (77, 80): 1.68,
    (73, 77): 1.47,
    (70, 73): 1.26,
    (67, 70): 1.07,
    (63, 67): 0.88,
    (60, 63): 0.7,
    (57, 60): 0.52,
    (53, 57): 0.34,
    (50, 53): 0.16,
    (47, 50): -0.02,
    (43, 47): -0.2,
    (40, 43): -0.4,
    (37, 40): -0.59,
    (33, 37): -0.8,
    (30, 33): -1.03,
    (27, 30): -1.27,
    (23, 27): -1.54,
    (20, 23): -1.84,
    (17, 20): -2.18,
    (13, 17): -2.58,
    (10, 13): -3.09,
    (6, 10): -3.8,
    (3, 6): -4.99,
    (0, 3): -6.66,
})


def get_severity(logit: float) -> str:
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


def get_tabular_logit(score: float) -> float:
    """
    Implements the scoring table accompanying Mioshi et al. (2010).
    Converts a score (in the table, a percentage; here, a number in the
    range 0-1) to a logit score of some description, whose true basis (in
    a Rasch analysis) is a bit obscure.
    """
    pct_score = 100 * score
    return TABULAR_LOGIT_BETWEENDICT[pct_score]


# for x in range(100, 0 - 1, -1):
#     score = x / 100
#     logit = get_tabular_logit(score)
#     severity = get_severity(logit)
#     print(",".join(str(q) for q in [x, logit, severity]))


def make_frs_fieldspec(n: int):
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

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        scoredict = self.get_score()
        return [CtvInfo(
            content=(
                "Total {total}/n, n = {n}, score = {score}, "
                "logit score = {logit}, severity = {severity}".format(
                    total=scoredict['total'],
                    n=scoredict['n'],
                    score=ws.number_to_dp(scoredict['score'], DP),
                    logit=ws.number_to_dp(scoredict['logit'], DP),
                    severity=scoredict['severity'],
                )
            )
        )]

    def get_score(self) -> Dict:
        total = 0
        n = 0
        for q in range(1, NQUESTIONS + 1):
            value = getattr(self, "q" + str(q))
            if value is not None and value != NA:
                n += 1
                total += SCORE.get(value, 0)
        if n > 0:
            score = total / n
            # logit = safe_logit(score)
            logit = get_tabular_logit(score)
            severity = get_severity(logit)
        else:
            score = None
            logit = None
            severity = ""
        return dict(total=total, n=n, score=score, logit=logit,
                    severity=severity)

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.is_respondent_complete() and
            self.are_all_fields_complete(self.TASK_FIELDS)
        )

    def get_answer(self, q: int) -> Optional[str]:
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

    def get_task_html(self) -> str:
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
                        <td>logit score <sup>2</sup></td>
                        <td>{logit}</td>
                    </td>
                    <tr>
                        <td>Severity <sup>3</sup></td>
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
                [2] This is not the simple logit, log(score/[1 – score]).
                Instead, it is determined by a lookup table, as per
                <a href="http://www.ftdrg.org/wp-content/uploads/FRS-Score-conversion.pdf">http://www.ftdrg.org/wp-content/uploads/FRS-Score-conversion.pdf</a>.
                The logit score that is looked up is very close to the logit
                of the raw score (on a 0–1 scale); however, it differs in that
                firstly it is banded rather than continuous, and secondly it
                is subtly different near the lower scores and at the extremes.
                The original is based on a Rasch analysis but the raw method of
                converting the score to the tabulated logit is not given.
                [3] Where <i>x</i> is the logit score, severity is determined
                as follows (after Mioshi et al. 2010, Neurology 74: 1591, PMID
                20479357, with sharp cutoffs).
                <i>Very mild:</i> <i>x</i> ≥ 4.12.
                <i>Mild:</i> 1.92 ≤ <i>x</i> &lt; 4.12.
                <i>Moderate:</i> –0.40 ≤ <i>x</i> &lt; 1.92.
                <i>Severe:</i> –2.58 ≤ <i>x</i> &lt; –0.40.
                <i>Very severe:</i> –4.99 ≤ <i>x</i> &lt; –2.58.
                <i>Profound:</i> <i>x</i> &lt; –4.99.
            </div>
        """  # noqa
        return h
