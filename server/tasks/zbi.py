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

from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING, WXSTRING
from cc_modules.cc_task import (
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# ZBI
# =============================================================================

class Zbi12(Task):
    MIN_SCORE = 0
    MAX_SCORE = 4
    QUESTION_SNIPPETS = [
        "insufficient time for self",  # 1
        "stressed with other responsibilities",
        "angry",
        "other relationships affected",
        "strained",  # 5
        "health suffered",
        "insufficient privacy",
        "social life suffered",
        "lost control",
        "uncertain",  # 10
        "should do more",
        "could care better"
    ]
    NQUESTIONS = 12
    QUESTION_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        min=MIN_SCORE, max=MAX_SCORE,
        comment_strings=QUESTION_SNIPPETS
    )
    TASK_FIELDSPECS = [
        dict(name="responder_name", cctype="TEXT",
             comment="Name of person completing task "),
        dict(name="responder_relationship", cctype="TEXT",
             comment="Relationship of responder to patient"),
    ] + QUESTION_FIELDSPECS
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]
    QUESTION_FIELDS = [x["name"] for x in QUESTION_FIELDSPECS]
    EXTRASTRING_TASKNAME = "zarit_burden_interview_12"

    @classmethod
    def get_tablename(cls):
        return "zbi12"

    @classmethod
    def get_taskshortname(cls):
        return "ZBI-12"

    @classmethod
    def get_tasklongname(cls):
        return "Zarit Burden Interview-12"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + cls.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return False

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (/ 48)"),
        ]

    def total_score(self):
        return self.sum_fields(self.QUESTION_FIELDS)

    def is_complete(self):
        return (
            self.field_contents_valid()
            and self.responder_name
            and self.responder_relationship
            and self.are_all_fields_complete(self.QUESTION_FIELDS)
        )

    def get_task_html(self):
        OPTION_DICT = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            OPTION_DICT[a] = WSTRING("zbi_a" + str(a))
        h = u"""
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score (/ 48)</td>
                        <td>{total}</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                {tr_responder}
                {tr_relationship}
            </table>
            <table class="taskdetail">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer (0–4)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
            tr_responder=tr_qa(u"Responder’s name", self.responder_name),
            tr_relationship=tr_qa(u"Responder’s relationship to patient",
                                  self.responder_relationship),
        )
        for q in xrange(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            fa = (u"{}: {}".format(a, get_from_dict(OPTION_DICT, a))
                  if a is not None else None)
            h += tr(
                WXSTRING(
                    self.EXTRASTRING_TASKNAME,
                    "q" + str(q),
                    "[ZBI: Q{}]".format(q)
                ),
                answer(fa)
            )
        h += u"""
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
