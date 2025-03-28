"""
camcops_server/tasks/mds_updrs.py

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

from typing import List, Optional

from sqlalchemy.orm import Mapped

from camcops_server.cc_modules.cc_cache import cache_region_static, fkg
from camcops_server.cc_modules.cc_constants import (
    CssClass,
    DATA_COLLECTION_ONLY_DIV,
)
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_snomed import SnomedExpression, SnomedLookup
from camcops_server.cc_modules.cc_sqla_coltypes import (
    BIT_CHECKER,
    gen_camcops_columns,
    get_camcops_column_attr_names,
    mapped_camcops_column,
    ZERO_TO_TWO_CHECKER,
    ZERO_TO_FOUR_CHECKER,
    ZERO_TO_FIVE_CHECKER,
)
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
    TaskHasClinicianMixin,
)


# =============================================================================
# MDS-UPDRS (crippled)
# =============================================================================


class MdsUpdrs(TaskHasClinicianMixin, TaskHasPatientMixin, Task):  # type: ignore[misc]  # noqa: E501
    """
    Server implementation of the MDS-UPDRS task.

    Has clinician as of v2.0.0.
    """

    __tablename__ = "mds_updrs"
    shortname = "MDS-UPDRS"

    main_cmt = " (0 normal, 1 slight, 2 mild, 3 moderate, 4 severe)"
    main_pv = ZERO_TO_FOUR_CHECKER
    informant_cmt = " (0 patient, 1 caregiver, 2 both)"
    informant_pv = ZERO_TO_TWO_CHECKER
    yn_cmt = " (0 no, 1 yes)"
    on_off_cmt = " (0 off, 1 on)"
    hy_pv = ZERO_TO_FIVE_CHECKER

    # Part I
    q1a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=informant_pv,
        comment="Part I: informant for Q1.1-1.6" + informant_cmt,
    )
    q1_1: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.1 " + main_cmt,
    )
    q1_2: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.2 " + main_cmt,
    )
    q1_3: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.3 " + main_cmt,
    )
    q1_4: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.4 " + main_cmt,
    )
    q1_5: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.5 " + main_cmt,
    )
    q1_6: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.6 " + main_cmt,
    )
    q1_6a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=informant_pv,
        comment="Part I, Q1.6a: informant for Q1.7-1.13" + informant_cmt,
    )
    q1_7: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.7 " + main_cmt,
    )
    q1_8: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.8 " + main_cmt,
    )
    q1_9: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.9 " + main_cmt,
    )
    q1_10: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.10 " + main_cmt,
    )
    q1_11: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.11 " + main_cmt,
    )
    q1_12: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.12 " + main_cmt,
    )
    q1_13: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part I, Q1.13 " + main_cmt,
    )

    # Part II
    q2_1: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.1 " + main_cmt,
    )
    q2_2: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.2 " + main_cmt,
    )
    q2_3: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.3 " + main_cmt,
    )
    q2_4: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.4 " + main_cmt,
    )
    q2_5: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.5 " + main_cmt,
    )
    q2_6: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.6 " + main_cmt,
    )
    q2_7: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.7 " + main_cmt,
    )
    q2_8: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.8 " + main_cmt,
    )
    q2_9: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.9 " + main_cmt,
    )
    q2_10: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.10 " + main_cmt,
    )
    q2_11: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.11 " + main_cmt,
    )
    q2_12: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.12 " + main_cmt,
    )
    q2_13: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part II, Q2.13 " + main_cmt,
    )

    # Part III
    q3a: Mapped[Optional[bool]] = mapped_camcops_column(
        permitted_value_checker=BIT_CHECKER,
        comment="Part III, Q3a (medication) " + yn_cmt,
    )
    q3b: Mapped[Optional[bool]] = mapped_camcops_column(
        permitted_value_checker=BIT_CHECKER,
        comment="Part III, Q3b (clinical state) " + on_off_cmt,
    )
    q3c: Mapped[Optional[bool]] = mapped_camcops_column(
        permitted_value_checker=BIT_CHECKER,
        comment="Part III, Q3c (levodopa) " + yn_cmt,
    )
    q3c1: Mapped[Optional[float]] = mapped_camcops_column(
        comment="Part III, Q3c.1 (minutes since last dose)"
    )
    q3_1: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.1 " + main_cmt,
    )
    q3_2: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.2 " + main_cmt,
    )
    q3_3a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.3a " + main_cmt,
    )
    q3_3b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.3b " + main_cmt,
    )
    q3_3c: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.3c " + main_cmt,
    )
    q3_3d: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.3d " + main_cmt,
    )
    q3_3e: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.3e " + main_cmt,
    )
    q3_4a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.4a " + main_cmt,
    )
    q3_4b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.4b " + main_cmt,
    )
    q3_5a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.5a " + main_cmt,
    )
    q3_5b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.5b " + main_cmt,
    )
    q3_6a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.6a " + main_cmt,
    )
    q3_6b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.6b " + main_cmt,
    )
    q3_7a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.7a " + main_cmt,
    )
    q3_7b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.7b " + main_cmt,
    )
    q3_8a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.8a " + main_cmt,
    )
    q3_8b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.8b " + main_cmt,
    )
    q3_9: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.9 " + main_cmt,
    )
    q3_10: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.10 " + main_cmt,
    )
    q3_11: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.11 " + main_cmt,
    )
    q3_12: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.12 " + main_cmt,
    )
    q3_13: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.13 " + main_cmt,
    )
    q3_14: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.14 " + main_cmt,
    )
    q3_15a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.15a " + main_cmt,
    )
    q3_15b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.15b " + main_cmt,
    )
    q3_16a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.16a " + main_cmt,
    )
    q3_16b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.16b " + main_cmt,
    )
    q3_17a: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.17a " + main_cmt,
    )
    q3_17b: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.17b " + main_cmt,
    )
    q3_17c: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.17c " + main_cmt,
    )
    q3_17d: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.17d " + main_cmt,
    )
    q3_17e: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.17e " + main_cmt,
    )
    q3_18: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part III, Q3.18 " + main_cmt,
    )
    q3_dyskinesia_present: Mapped[Optional[bool]] = mapped_camcops_column(
        permitted_value_checker=BIT_CHECKER,
        comment="Part III, q3_dyskinesia_present " + yn_cmt,
    )
    q3_dyskinesia_interfered: Mapped[Optional[bool]] = mapped_camcops_column(
        permitted_value_checker=BIT_CHECKER,
        comment="Part III, q3_dyskinesia_interfered " + yn_cmt,
    )
    q3_hy_stage: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=hy_pv,
        comment="Part III, q3_hy_stage (0-5)",
    )

    # Part IV
    q4_1: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part IV, Q4.1 " + main_cmt,
    )
    q4_2: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part IV, Q4.2 " + main_cmt,
    )
    q4_3: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part IV, Q4.3 " + main_cmt,
    )
    q4_4: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part IV, Q4.4 " + main_cmt,
    )
    q4_5: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part IV, Q4.5 " + main_cmt,
    )
    q4_6: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=main_pv,
        comment="Part IV, Q4.6 " + main_cmt,
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _(
            "Movement Disorder Society-Sponsored Revision of the Unified "
            "Parkinson’s Disease Rating Scale (data collection only)"
        )

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def task_fields_except_3c1(cls) -> List[str]:
        task_fields = get_camcops_column_attr_names(cls)
        return [x for x in task_fields if x != "q3c1"]

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid()
            and self.all_fields_not_none(self.task_fields_except_3c1())
            and (self.q3c1 is not None or not self.q3c)
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        q_a = ""
        for attrname, column in gen_camcops_columns(self):
            if attrname.startswith("clinician_"):  # not the most elegant!
                continue
            question = column.comment
            value = getattr(self, attrname)
            q_a += tr_qa(question, value)
        return f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
                {q_a}
            </table>
            {DATA_COLLECTION_ONLY_DIV}
        """

    def get_snomed_codes(self, req: CamcopsRequest) -> List[SnomedExpression]:
        if not self.is_complete():
            return []
        return [SnomedExpression(req.snomed(SnomedLookup.UPDRS_SCALE))]
