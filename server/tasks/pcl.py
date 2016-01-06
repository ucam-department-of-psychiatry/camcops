#!/usr/bin/env python3
# pcl.py

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

from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    get_yes_no,
    subheading_spanning_two_columns,
    tr,
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
# PCL
# =============================================================================

# -----------------------------------------------------------------------------
# PCL: common class
# -----------------------------------------------------------------------------

class PclCommon(object):
    NQUESTIONS = 17
    CORE_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=1, max=5,
        comment_fmt="Q{n} ({s}) (1 not at all - 5 extremely)",
        comment_strings=[
            "disturbing memories/thoughts/images",
            "disturbing dreams",
            "reliving",
            "upset at reminders",
            "physical reactions to reminders",
            "avoid thinking/talking/feelings relating to experience",
            "avoid activities/situations because they remind",
            "trouble remembering important parts of stressful event",
            "loss of interest in previously enjoyed activities",
            "feeling distant/cut off from people",
            "feeling emotionally numb",
            "feeling future will be cut short",
            "hard to sleep",
            "irritable",
            "difficulty concentrating",
            "super alert/on guard",
            "jumpy/easily startled",
        ]
    )
    TASK_FIELDSPECS = []
    TASK_FIELDS = []
    TASK_TYPE = "?"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + cls.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def is_complete(self):
        return (
            self.are_all_fields_complete(self.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def total_score(self):
        return self.sum_fields(repeat_fieldname("q", 1, PclCommon.NQUESTIONS))

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "PCL total score",
                "axis_label": "Total score (17-85)",
                "axis_min": 16.5,
                "axis_max": 85.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "PCL total score {}".format(self.total_score())}]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (17-85)"),
            dict(name="num_symptomatic", cctype="INT",
                 value=self.num_symptomatic(),
                 comment="Total number of symptoms considered symptomatic "
                 "(meaning scoring 3 or more)"),
            dict(name="num_symptomatic_B", cctype="INT",
                 value=self.num_symptomatic_B(),
                 comment="Number of group B symptoms considered symptomatic "
                 "(meaning scoring 3 or more)"),
            dict(name="num_symptomatic_C", cctype="INT",
                 value=self.num_symptomatic_C(),
                 comment="Number of group C symptoms considered symptomatic "
                 "(meaning scoring 3 or more)"),
            dict(name="num_symptomatic_D", cctype="INT",
                 value=self.num_symptomatic_D(),
                 comment="Number of group D symptoms considered symptomatic "
                 "(meaning scoring 3 or more)"),
            dict(name="ptsd", cctype="BOOL", value=self.ptsd(),
                 comment="Meets DSM-IV criteria for PTSD"),
        ]

    def get_num_symptomatic(self, first, last):
        n = 0
        for i in range(first, last + 1):
            if getattr(self, "q" + str(i)) >= 3:
                n += 1
        return n

    def num_symptomatic(self):
        return self.get_num_symptomatic(1, PclCommon.NQUESTIONS)

    def num_symptomatic_B(self):
        return self.get_num_symptomatic(1, 5)

    def num_symptomatic_C(self):
        return self.get_num_symptomatic(6, 12)

    def num_symptomatic_D(self):
        return self.get_num_symptomatic(13, 17)

    def ptsd(self):
        num_symptomatic_B = self.num_symptomatic_B()
        num_symptomatic_C = self.num_symptomatic_C()
        num_symptomatic_D = self.num_symptomatic_D()
        return num_symptomatic_B >= 1 and num_symptomatic_C >= 3 and \
            num_symptomatic_D >= 2

    def get_task_html(self):
        tasktype = self.TASK_TYPE
        score = self.total_score()
        num_symptomatic = self.num_symptomatic()
        num_symptomatic_B = self.num_symptomatic_B()
        num_symptomatic_C = self.num_symptomatic_C()
        num_symptomatic_D = self.num_symptomatic_D()
        ptsd = self.ptsd()
        ANSWER_DICT = {None: None}
        for option in range(1, 6):
            ANSWER_DICT[option] = str(option) + " – " + \
                WSTRING("pcl_option" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr_qa("{} (17–85)".format(WSTRING("total_score")),
                   score)
        h += tr("Number symptomatic <sup>[1]</sup>: B, C, D (total)",
                answer(num_symptomatic_B)
                + ", "
                + answer(num_symptomatic_C)
                + ", "
                + answer(num_symptomatic_D)
                + " ("
                + answer(num_symptomatic)
                + ")")
        h += tr_qa(WSTRING("pcl_dsm_criteria_met") + " <sup>[2]</sup>",
                   get_yes_no(ptsd))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        if tasktype == "S":
            h += tr_qa(WSTRING("pcl_s_event_s"), self.event)
            h += tr_qa(WSTRING("pcl_s_eventdate_s"), self.eventdate)
        for q in range(1, PclCommon.NQUESTIONS + 1):
            if q == 1 or q == 6 or q == 13:
                section = "B" if q == 1 else ("C" if q == 6 else "D")
                h += subheading_spanning_two_columns(
                    "DSM section {}".format(section)
                )
            h += tr_qa(
                WSTRING("pcl_q" + str(q) + "_s"),
                get_from_dict(ANSWER_DICT, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Questions with scores ≥3 are considered symptomatic.
                [2] ≥1 ‘B’ symptoms and ≥3 ‘C’ symptoms and
                    ≥2 ‘D’ symptoms.
            </div>
        """
        return h


# -----------------------------------------------------------------------------
# PCL-C
# -----------------------------------------------------------------------------

class PclC(PclCommon, Task):
    TASK_FIELDSPECS = PclCommon.CORE_FIELDSPECS
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]
    TASK_TYPE = "C"

    @classmethod
    def get_tablename(cls):
        return "pclc"

    @classmethod
    def get_taskshortname(cls):
        return "PCL-C"

    @classmethod
    def get_tasklongname(cls):
        return "PTSD Checklist, Civilian version"


# -----------------------------------------------------------------------------
# PCL-M
# -----------------------------------------------------------------------------

class PclM(PclCommon, Task):
    TASK_FIELDSPECS = PclCommon.CORE_FIELDSPECS
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]
    TASK_TYPE = "M"

    @classmethod
    def get_tablename(cls):
        return "pclm"

    @classmethod
    def get_taskshortname(cls):
        return "PCL-M"

    @classmethod
    def get_tasklongname(cls):
        return "PTSD Checklist, Military version"


# -----------------------------------------------------------------------------
# PCL-S
# -----------------------------------------------------------------------------

class PclS(PclCommon, Task):
    TASK_FIELDSPECS = PclCommon.CORE_FIELDSPECS + [
        dict(name="event", cctype="TEXT",
             comment="Traumatic event"),
        dict(name="eventdate", cctype="TEXT",
             comment="Date of traumatic event (free text)"),
    ]
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]
    TASK_TYPE = "S"

    @classmethod
    def get_tablename(cls):
        return "pcls"

    @classmethod
    def get_taskshortname(cls):
        return "PCL-S"

    @classmethod
    def get_tasklongname(cls):
        return "PTSD Checklist, Stressor-specific version"
