#!/usr/bin/env python3
# caps.py

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

from typing import List

from ..cc_modules.cc_constants import PV
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import Task, TrackerInfo


# =============================================================================
# CAPS
# =============================================================================

QUESTION_SNIPPETS = [
    "sounds loud", "presence of another", "heard thoughts echoed",
    "see shapes/lights/colours", "burning or other bodily sensations",
    "hear noises/sounds", "thoughts spoken aloud", "unexplained smells",
    "body changing shape", "limbs not own", "voices commenting",
    "feeling a touch", "hearing words or sentences", "unexplained tastes",
    "sensations flooding", "sounds distorted",
    "hard to distinguish sensations", "odours strong",
    "shapes/people distorted", "hypersensitive to touch/temperature",
    "tastes stronger than normal", "face looks different",
    "lights/colours more intense", "feeling of being uplifted",
    "common smells seem different", "everyday things look abnormal",
    "altered perception of time", "hear voices conversing",
    "smells or odours that others are unaware of",
    "food/drink tastes unusual", "see things that others cannot",
    "hear sounds/music that others cannot"
]


class Caps(Task):
    NQUESTIONS = 32

    tablename = "caps"
    shortname = "CAPS"
    longname = "Cardiff Anomalous Perceptions Scale"
    fieldspecs = (
        repeat_fieldspec(
            "endorse", 1, NQUESTIONS, pv=PV.BIT,
            comment_fmt="Q{n} ({s}): endorsed? (0 no, 1 yes)",
            comment_strings=QUESTION_SNIPPETS) +
        repeat_fieldspec(
            "distress", 1, NQUESTIONS, min=1, max=5,
            comment_fmt="Q{n} ({s}): distress (1 low - 5 high), if endorsed",
            comment_strings=QUESTION_SNIPPETS) +
        repeat_fieldspec(
            "intrusiveness", 1, NQUESTIONS, min=1, max=5,
            comment_fmt="Q{n} ({s}): intrusiveness (1 low - 5 high), "
            "if endorsed",
            comment_strings=QUESTION_SNIPPETS) +
        repeat_fieldspec(
            "frequency", 1, NQUESTIONS, min=1, max=5,
            comment_fmt="Q{n} ({s}): frequency (1 low - 5 high), if endorsed",
            comment_strings=QUESTION_SNIPPETS)
    )

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="CAPS total score",
            axis_label="Total score (out of 32)",
            axis_min=-0.5,
            axis_max=32.5
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score (/32)"),
            dict(name="distress", cctype="INT",
                 value=self.distress_score(),
                 comment="Distress score (/160)"),
            dict(name="intrusiveness", cctype="INT",
                 value=self.intrusiveness_score(),
                 comment="Intrusiveness score (/160)"),
            dict(name="frequency", cctype="INT",
                 value=self.frequency_score(),
                 comment="Frequency score (/160)"),
        ]

    def is_question_complete(self, q: int) -> bool:
        if getattr(self, "endorse" + str(q)) is None:
            return False
        if getattr(self, "endorse" + str(q)):
            if getattr(self, "distress" + str(q)) is None:
                return False
            if getattr(self, "intrusiveness" + str(q)) is None:
                return False
            if getattr(self, "frequency" + str(q)) is None:
                return False
        return True

    def is_complete(self) -> bool:
        if not self.field_contents_valid():
            return False
        for i in range(1, Caps.NQUESTIONS + 1):
            if not self.is_question_complete(i):
                return False
        return True

    def total_score(self) -> int:
        return self.count_booleans(repeat_fieldname("endorse", 1,
                                                    Caps.NQUESTIONS))

    def distress_score(self) -> int:
        score = 0
        for q in range(1, Caps.NQUESTIONS + 1):
            if getattr(self, "endorse" + str(q)) \
                    and getattr(self, "distress" + str(q)) is not None:
                score += self.sum_fields(["distress" + str(q)])
        return score

    def intrusiveness_score(self) -> int:
        score = 0
        for q in range(1, Caps.NQUESTIONS + 1):
            if getattr(self, "endorse" + str(q)) \
                    and getattr(self, "intrusiveness" + str(q)) is not None:
                score += self.sum_fields(["intrusiveness" + str(q)])
        return score

    def frequency_score(self) -> int:
        score = 0
        for q in range(1, Caps.NQUESTIONS + 1):
            if getattr(self, "endorse" + str(q)) \
                    and getattr(self, "frequency" + str(q)) is not None:
                score += self.sum_fields(["frequency" + str(q)])
        return score

    def get_task_html(self) -> str:
        total = self.total_score()
        distress = self.distress_score()
        intrusiveness = self.intrusiveness_score()
        frequency = self.frequency_score()
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa("{} <sup>[1]</sup> (0–32)".format(WSTRING("total_score")),
                   total)
        h += tr_qa("{} (0–160)".format(WSTRING("caps_distress")),
                   distress)
        h += tr_qa("{} (0–160)".format(WSTRING("caps_intrusiveness")),
                   intrusiveness)
        h += tr_qa("{} (0–160)".format(WSTRING("caps_frequency")),
                   frequency)
        h += """
                </table>
            </div>
            <div class="explanation">
                Anchor points: DISTRESS {distress1}, {distress5}.
                INTRUSIVENESS {intrusiveness1}, {intrusiveness5}.
                FREQUENCY {frequency1}, {frequency5}.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="10%">Endorsed?</th>
                    <th width="10%">Distress (1–5)</th>
                    <th width="10%">Intrusiveness (1–5)</th>
                    <th width="10%">Frequency (1–5)</th>
                </tr>
        """.format(
            distress1=WSTRING("caps_distress_option1"),
            distress5=WSTRING("caps_distress_option5"),
            intrusiveness1=WSTRING("caps_intrusiveness_option1"),
            intrusiveness5=WSTRING("caps_intrusiveness_option5"),
            frequency1=WSTRING("caps_frequency_option1"),
            frequency5=WSTRING("caps_frequency_option5"),
        )
        for q in range(1, Caps.NQUESTIONS + 1):
            h += tr(
                WSTRING("caps_q" + str(q)),
                answer(get_yes_no_none(getattr(self, "endorse" + str(q)))),
                answer(getattr(self, "distress" + str(q))
                       if getattr(self, "endorse" + str(q)) else ""),
                answer(getattr(self, "intrusiveness" + str(q))
                       if getattr(self, "endorse" + str(q)) else ""),
                answer(getattr(self, "frequency" + str(q))
                       if getattr(self, "endorse" + str(q)) else "")
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Total score: sum of endorsements (yes = 1, no = 0).
                Dimension scores: sum of ratings (0 if not endorsed).
                (Bell et al. 2006, PubMed ID 16237200)
            </div>
            <div class="copyright">
                CAPS: Copyright © 2005, Bell, Halligan & Ellis.
                Original article:
                    Bell V, Halligan PW, Ellis HD (2006).
                    The Cardiff Anomalous Perceptions Scale (CAPS): a new
                    validated measure of anomalous perceptual experience.
                    Schizophrenia Bulletin 32: 366–377.
                Published by Oxford University Press on behalf of the Maryland
                Psychiatric Research Center. All rights reserved. The online
                version of this article has been published under an open access
                model. Users are entitled to use, reproduce, disseminate, or
                display the open access version of this article for
                non-commercial purposes provided that: the original authorship
                is properly and fully attributed; the Journal and Oxford
                University Press are attributed as the original place of
                publication with the correct citation details given; if an
                article is subsequently reproduced or disseminated not in its
                entirety but only in part or as a derivative work this must be
                clearly indicated. For commercial re-use, please contact
                journals.permissions@oxfordjournals.org.<br>
                <b>This is a derivative work (partial reproduction, viz. the
                scale text).</b>
            </div>
        """
        return h
