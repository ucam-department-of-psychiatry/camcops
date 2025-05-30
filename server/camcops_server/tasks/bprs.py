"""
camcops_server/tasks/bprs.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

"""

from typing import Any, Dict, List, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo, CTV_INCOMPLETE
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_snomed import SnomedExpression, SnomedLookup
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_text import SS
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# BPRS
# =============================================================================


class BprsMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(
        cls: Type["Bprs"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:
        add_multiple_columns(
            cls,
            "q",
            1,
            cls.NQUESTIONS,
            minimum=0,
            maximum=7,
            comment_fmt="Q{n}, {s} (1-7, higher worse, 0 for unable to rate)",
            comment_strings=[
                "somatic concern",
                "anxiety",
                "emotional withdrawal",
                "conceptual disorganisation",
                "guilt",
                "tension",
                "mannerisms/posturing",
                "grandiosity",
                "depressive mood",
                "hostility",
                "suspiciousness",
                "hallucinatory behaviour",
                "motor retardation",
                "uncooperativeness",
                "unusual thought content",
                "blunted affect",
                "excitement",
                "disorientation",
                "severity of illness",
                "global improvement",
            ],
        )
        super().__init__(name, bases, classdict)


class Bprs(
    TaskHasPatientMixin, TaskHasClinicianMixin, Task, metaclass=BprsMetaclass
):
    """
    Server implementation of the BPRS task.
    """

    __tablename__ = "bprs"
    shortname = "BPRS"
    provides_trackers = True

    NQUESTIONS = 20
    TASK_FIELDS = strseq("q", 1, NQUESTIONS)
    SCORED_FIELDS = [x for x in TASK_FIELDS if (x != "q19" and x != "q20")]
    MAX_SCORE = 126

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Brief Psychiatric Rating Scale")

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.total_score(),
                plot_label="BPRS total score",
                axis_label=f"Total score (out of {self.MAX_SCORE})",
                axis_min=-0.5,
                axis_max=self.MAX_SCORE + 0.5,
            )
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [
            CtvInfo(
                content=f"BPRS total score "
                f"{self.total_score()}/{self.MAX_SCORE}"
            )
        ]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Integer(),
                value=self.total_score(),
                comment=f"Total score (/{self.MAX_SCORE})",
            )
        ]

    def is_complete(self) -> bool:
        return (
            self.all_fields_not_none(Bprs.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(Bprs.SCORED_FIELDS, ignorevalues=[0, None])
        # "0" means "not rated"

    # noinspection PyUnresolvedReferences
    def get_task_html(self, req: CamcopsRequest) -> str:
        main_dict = {
            None: None,
            0: "0 — " + self.wxstring(req, "old_option0"),
            1: "1 — " + self.wxstring(req, "old_option1"),
            2: "2 — " + self.wxstring(req, "old_option2"),
            3: "3 — " + self.wxstring(req, "old_option3"),
            4: "4 — " + self.wxstring(req, "old_option4"),
            5: "5 — " + self.wxstring(req, "old_option5"),
            6: "6 — " + self.wxstring(req, "old_option6"),
            7: "7 — " + self.wxstring(req, "old_option7"),
        }
        q19_dict = {
            None: None,
            1: self.wxstring(req, "q19_option1"),
            2: self.wxstring(req, "q19_option2"),
            3: self.wxstring(req, "q19_option3"),
            4: self.wxstring(req, "q19_option4"),
            5: self.wxstring(req, "q19_option5"),
            6: self.wxstring(req, "q19_option6"),
            7: self.wxstring(req, "q19_option7"),
        }
        q20_dict = {
            None: None,
            0: self.wxstring(req, "q20_option0"),
            1: self.wxstring(req, "q20_option1"),
            2: self.wxstring(req, "q20_option2"),
            3: self.wxstring(req, "q20_option3"),
            4: self.wxstring(req, "q20_option4"),
            5: self.wxstring(req, "q20_option5"),
            6: self.wxstring(req, "q20_option6"),
            7: self.wxstring(req, "q20_option7"),
        }

        q_a = ""
        for i in range(1, Bprs.NQUESTIONS - 1):  # only does 1-18
            q_a += tr_qa(
                self.wxstring(req, "q" + str(i) + "_title"),
                get_from_dict(main_dict, getattr(self, "q" + str(i))),
            )
        q_a += tr_qa(
            self.wxstring(req, "q19_title"), get_from_dict(q19_dict, self.q19)
        )
        q_a += tr_qa(
            self.wxstring(req, "q20_title"), get_from_dict(q20_dict, self.q20)
        )

        total_score = tr(
            req.sstring(SS.TOTAL_SCORE)
            + f" (0–{self.MAX_SCORE}; 18–{self.MAX_SCORE} if all rated) "
            "<sup>[1]</sup>",
            answer(self.total_score()),
        )
        return f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                    {total_score}
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                Ratings pertain to the past week, or behaviour during
                interview. Each question has specific answer definitions (see
                e.g. tablet app).
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer <sup>[2]</sup></th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Only questions 1–18 are scored.
                [2] All answers are in the range 1–7, or 0 (not assessed, for
                    some).
            </div>
        """

    def get_snomed_codes(self, req: CamcopsRequest) -> List[SnomedExpression]:
        codes = [SnomedExpression(req.snomed(SnomedLookup.BPRS1962_SCALE))]
        return codes
