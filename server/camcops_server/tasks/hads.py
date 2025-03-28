"""
camcops_server/tasks/hads.py

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

from abc import ABC
import logging
from typing import Any, cast, List, Type, Union

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import (
    CssClass,
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
)
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_snomed import SnomedExpression, SnomedLookup
from camcops_server.cc_modules.cc_string import AS
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
    TaskHasRespondentMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# HADS (crippled unless upgraded locally) - base classes
# =============================================================================


class HadsBase(TaskHasPatientMixin, Task, ABC):  # type: ignore[misc]
    """
    Server implementation of the HADS task.
    """

    __abstract__ = True
    provides_trackers = True

    NQUESTIONS = 14
    ANXIETY_QUESTIONS = [1, 3, 5, 7, 9, 11, 13]
    DEPRESSION_QUESTIONS = [2, 4, 6, 8, 10, 12, 14]
    TASK_FIELDS = strseq("q", 1, NQUESTIONS)
    MAX_ANX_SCORE = 21
    MAX_DEP_SCORE = 21

    @classmethod
    def extend_columns(cls: Type["HadsBase"], **kwargs: Any) -> None:
        add_multiple_columns(
            cls,
            "q",
            1,
            cls.NQUESTIONS,
            minimum=0,
            maximum=3,
            comment_fmt="Q{n}: {s} (0-3)",
            comment_strings=[
                "tense",
                "enjoy usual",
                "apprehensive",
                "laugh",
                "worry",
                "cheerful",
                "relaxed",
                "slow",
                "butterflies",
                "appearance",
                "restless",
                "anticipate",
                "panic",
                "book/TV/radio",
            ],
        )

    def is_complete(self) -> bool:
        return self.field_contents_valid() and self.all_fields_not_none(
            self.TASK_FIELDS
        )

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.anxiety_score(),
                plot_label="HADS anxiety score",
                axis_label=f"Anxiety score (out of {self.MAX_ANX_SCORE})",
                axis_min=-0.5,
                axis_max=self.MAX_ANX_SCORE + 0.5,
            ),
            TrackerInfo(
                value=self.depression_score(),
                plot_label="HADS depression score",
                axis_label=f"Depression score (out of {self.MAX_DEP_SCORE})",
                axis_min=-0.5,
                axis_max=self.MAX_DEP_SCORE + 0.5,
            ),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [
            CtvInfo(
                content=(
                    f"anxiety score "
                    f"{self.anxiety_score()}/{self.MAX_ANX_SCORE}, "
                    f"depression score "
                    f"{self.depression_score()}/{self.MAX_DEP_SCORE}"
                )
            )
        ]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="anxiety",
                coltype=Integer(),
                value=self.anxiety_score(),
                comment=f"Anxiety score (/{self.MAX_ANX_SCORE})",
            ),
            SummaryElement(
                name="depression",
                coltype=Integer(),
                value=self.depression_score(),
                comment=f"Depression score (/{self.MAX_DEP_SCORE})",
            ),
        ]

    def score(self, questions: List[int]) -> int:
        fields = self.fieldnames_from_list("q", questions)
        return cast(int, self.sum_fields(fields))

    def anxiety_score(self) -> Union[int, float]:
        return self.score(self.ANXIETY_QUESTIONS)

    def depression_score(self) -> Union[int, float]:
        return self.score(self.DEPRESSION_QUESTIONS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        min_score = 0
        max_score = 3
        crippled = not self.extrastrings_exist(req)
        a = self.anxiety_score()
        d = self.depression_score()
        h = f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                    <tr>
                        <td>{req.wappstring(AS.HADS_ANXIETY_SCORE)}</td>
                        <td>{answer(a)} / {self.MAX_ANX_SCORE}</td>
                    </tr>
                    <tr>
                        <td>{req.wappstring(AS.HADS_DEPRESSION_SCORE)}</td>
                        <td>{answer(d)} / 21</td>
                    </tr>
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                All questions are scored from 0–3
                (0 least symptomatic, 3 most symptomatic).
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        for n in range(1, self.NQUESTIONS + 1):
            if crippled:
                q = f"HADS: Q{n}"
            else:
                q = f"Q{n}. {self.wxstring(req, f'q{n}_stem')}"
            if n in self.ANXIETY_QUESTIONS:
                q += " (A)"
            if n in self.DEPRESSION_QUESTIONS:
                q += " (D)"
            v = getattr(self, "q" + str(n))
            if crippled or v is None or v < min_score or v > max_score:
                a = v
            else:
                a = f"{v}: {self.wxstring(req, f'q{n}_a{v}')}"  # type: ignore[assignment]  # noqa: E501
            h += tr_qa(q, a)
        h += (
            """
            </table>
        """
            + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        )
        return h


# =============================================================================
# Hads
# =============================================================================


class Hads(HadsBase):
    __tablename__ = "hads"
    shortname = "HADS"

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _(
            "Hospital Anxiety and Depression Scale (data collection only)"
        )

    def get_snomed_codes(self, req: CamcopsRequest) -> List[SnomedExpression]:
        codes = [
            SnomedExpression(
                req.snomed(SnomedLookup.HADS_PROCEDURE_ASSESSMENT)
            )
        ]
        if self.is_complete():
            codes.append(
                SnomedExpression(
                    req.snomed(SnomedLookup.HADS_SCALE),
                    {
                        req.snomed(
                            SnomedLookup.HADS_ANXIETY_SCORE
                        ): self.anxiety_score(),
                        req.snomed(
                            SnomedLookup.HADS_DEPRESSION_SCORE
                        ): self.depression_score(),
                    },
                )
            )
        return codes


# =============================================================================
# HadsRespondent
# =============================================================================


class HadsRespondent(TaskHasRespondentMixin, HadsBase):  # type: ignore[misc]
    __tablename__ = "hads_respondent"
    shortname = "HADS-Respondent"
    extrastring_taskname = "hads"
    info_filename_stem = extrastring_taskname

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _(
            "Hospital Anxiety and Depression Scale (data collection "
            "only), non-patient respondent version"
        )

    # No SNOMED codes; not for the patient!
