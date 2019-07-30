#!/usr/bin/env python

"""
camcops_server/tasks/das28.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

**Disease Activity Score-28 (DAS28) task.**

"""

import math
from typing import Any, Dict, List, Optional, Type, Tuple

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import answer, table_row, th, td, tr
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    BoolColumn,
    PermittedValueChecker,

    SummaryCategoryColType,
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import TaskHasPatientMixin, \
    TaskHasClinicianMixin, Task
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerAxisTick,
    TrackerInfo,
    TrackerLabel,
)

import cardinal_pythonlib.rnc_web as ws
from sqlalchemy import Column, Float, Integer
from sqlalchemy.ext.declarative import DeclarativeMeta


class Das28Metaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Das28'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        for field_name in cls.get_count_field_names():
            setattr(cls, field_name,
                    BoolColumn(field_name, comment="0 no, 1 yes"))

        setattr(
            cls, 'vas',
            Column(
                'vas',
                Integer,
                comment="Patient assessment of health (0-100mm)",
                permitted_value_checker=PermittedValueChecker(
                    minimum=0, maximum=100)
            )
        )

        setattr(
            cls, 'crp',
            Column('crp', Integer, comment="CRP (0-300 mg/L)")
        )

        setattr(
            cls, 'esr',
            Column('esr', Integer, comment="ESR (1-300 mm/h)")
        )

        super().__init__(name, bases, classdict)


class Das28(TaskHasPatientMixin,
            TaskHasClinicianMixin,
            Task,
            metaclass=Das28Metaclass):
    __tablename__ = "das28"
    shortname = "DAS28"
    provides_trackers = True

    JOINTS = (
        ['shoulder', 'elbow', 'wrist'] +
        [f"mcp_{n}" for n in range(1, 6)] +
        [f"pip_{n}" for n in range(1, 6)] +
        ['knee']
    )

    SIDES = ['left', 'right']
    STATES = ['swollen', 'tender']

    INACTIVE_MODERATE_CUTOFF = 1.3
    MODERATE_HIGH_CUTOFF = 2.1
    HIGH_VERY_HIGH_CUTOFF = 3.5

    @classmethod
    def field_name(cls, side, joint, state) -> str:
        return f"{side}_{joint}_{state}"

    @classmethod
    def get_count_field_names(cls) -> List:
        field_names = []

        for joint in cls.JOINTS:
            for side in cls.SIDES:
                for state in cls.STATES:
                    field_names.append(cls.field_name(side, joint, state))

        return field_names

    @classmethod
    def get_all_field_names(cls) -> List:
        return cls.get_count_field_names() + ['vas', 'crp', 'esr']

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Disease Activity Score-28")

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="das28_crp", coltype=Float(),
                value=self.das28_crp(),
                comment=f"DAS28-CRP"),
            SummaryElement(
                name="activity_state_crp", coltype=SummaryCategoryColType,
                value=self.activity_state_crp(req, self.das28_crp()),
                comment=f"Activity state (CRP)"),
            SummaryElement(
                name="das28_esr", coltype=Float(),
                value=self.das28_esr(),
                comment=f"DAS28-ESR"),
            SummaryElement(
                name="activity_state_esr", coltype=SummaryCategoryColType,
                value=self.activity_state_esr(req, self.das28_esr()),
                comment=f"Activity state (ESR)"),
        ]

    def is_complete(self) -> bool:
        if self.any_fields_none(self.get_count_field_names() + ['vas']):
            return False

        if self.crp is None and self.esr is None:
            return False

        if not self.field_contents_valid():
            return False

        return True

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        # TODO: Find out cutoffs for both CRP and ESR versions

        axis_min = -0.5
        axis_max = 7.5
        axis_ticks = [TrackerAxisTick(n, str(n))
                      for n in range(0, int(axis_max) + 1)]

        horizontal_lines = [
            self.HIGH_VERY_HIGH_CUTOFF,
            self.MODERATE_HIGH_CUTOFF,
            self.INACTIVE_MODERATE_CUTOFF,
            0,
        ]

        horizontal_labels = [
            TrackerLabel(5.25, self.wxstring(req, "very_high")),
            TrackerLabel(2.8, self.wxstring(req, "high")),
            TrackerLabel(1.7, self.wxstring(req, "moderate")),
            TrackerLabel(0.65, self.wxstring(req, "inactive")),
        ]

        return [
            TrackerInfo(
                value=self.das28_crp(),
                plot_label="DAS28-CRP",
                axis_label="DAS28-CRP",
                axis_min=axis_min,
                axis_max=axis_max,
                axis_ticks=axis_ticks,
                horizontal_lines=horizontal_lines,
                horizontal_labels=horizontal_labels,
            ),
            TrackerInfo(
                value=self.das28_esr(),
                plot_label="DAS28-ESR",
                axis_label="DAS28-ESR",
                axis_min=axis_min,
                axis_max=axis_max,
                axis_ticks=axis_ticks,
                horizontal_lines=horizontal_lines,
                horizontal_labels=horizontal_labels,
            ),
        ]

    def swollen_joint_count(self):
        return self.count_booleans(
            [n for n in self.get_count_field_names() if n.endswith("swollen")]
        )

    def tender_joint_count(self):
        return self.count_booleans(
            [n for n in self.get_count_field_names() if n.endswith("tender")]
        )

    def das28_crp(self) -> Optional[float]:
        if self.crp is None:
            return None

        # TODO: VAS null

        return (
            0.56 * math.sqrt(self.tender_joint_count()) +
            0.28 * math.sqrt(self.swollen_joint_count()) +
            0.36 * math.log(self.crp + 1) +
            0.014 * self.vas +
            0.96
        )

    def das28_esr(self) -> Optional[float]:
        if self.esr is None:
            return None

        # TODO: VAS null

        return (
            0.56 * math.sqrt(self.tender_joint_count()) +
            0.28 * math.sqrt(self.swollen_joint_count()) +
            0.70 * math.log(self.esr) +
            0.014 * self.vas
        )

    def activity_state_crp(self, req: CamcopsRequest, measurement: Any) -> str:
        # TODO: Fix
        if measurement is None:
            return self.wxstring(req, "n_a")

        if measurement < self.INACTIVE_MODERATE_CUTOFF:
            return self.wxstring(req, "inactive")

        if measurement < self.MODERATE_HIGH_CUTOFF:
            return self.wxstring(req, "moderate")

        if measurement > self.HIGH_VERY_HIGH_CUTOFF:
            return self.wxstring(req, "very_high")

        return self.wxstring(req, "high")

    def activity_state_esr(self, req: CamcopsRequest, measurement: Any) -> str:
        # TODO: Implement
        pass

    def get_task_html(self, req: CamcopsRequest) -> str:
        _ = req.gettext

        rows = ""

        sides_strings = [self.wxstring(req, s) for s in self.SIDES]
        states_strings = [self.wxstring(req, s) for s in self.STATES]

        rows += table_row([""] + sides_strings,
                          colspans=[1, 2, 2])

        rows += table_row([""] + states_strings * 2)

        for joint in self.JOINTS:
            cells = [th(self.wxstring(req, joint))]
            for side in self.SIDES:
                for state in self.STATES:
                    value = ""
                    if getattr(self, self.field_name(side, joint, state)):
                        value = _("Yes")

                    cells.append(td(value))

            rows += tr(*cells, literal=True)

        das28_crp = ws.number_to_dp(self.das28_crp(), 2, default="?")
        das28_esr = ws.number_to_dp(self.das28_esr(), 2, default="?")

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {das28_crp}
                    {das28_esr}
                    {swollen_joint_count}
                    {tender_joint_count}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                {rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
            TODO
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            das28_crp=tr(
                self.wxstring(req, "das28_crp") + " <sup>[1][2]</sup>",
                "{} ({})".format(
                    answer(das28_crp),
                    self.activity_state_crp(req, self.das28_crp())
                )
            ),
            das28_esr=tr(
                self.wxstring(req, "das28_esr") + " <sup>[1][3]</sup>",
                "{} ({})".format(
                    answer(das28_esr),
                    self.activity_state_esr(req, self.das28_esr())
                )
            ),
            swollen_joint_count=tr(
                self.wxstring(req, "swollen_count"),
                self.swollen_joint_count()
            ),
            tender_joint_count=tr(
                self.wxstring(req, "tender_count"),
                self.tender_joint_count()
            ),
            rows=rows,
        )
        return html
