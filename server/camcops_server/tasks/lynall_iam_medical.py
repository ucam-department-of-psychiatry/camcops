"""
camcops_server/tasks/lynall_iam_medical.py

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

from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import (
    get_yes_no,
    get_yes_no_none,
    tr_qa,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    mapped_bool_column,
    mapped_camcops_column,
    PermittedValueChecker,
)
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_text import SS


# =============================================================================
# Lynall1MedicalHistory
# =============================================================================


class LynallIamMedicalHistory(TaskHasPatientMixin, Task):  # type: ignore[misc]
    """
    Server implementation of the Lynall1IamMedicalHistory task.
    """

    __tablename__ = "lynall_1_iam_medical"  # historically fixed
    shortname = "Lynall_IAM_Medical"
    extrastring_taskname = "lynall_iam_medical"
    info_filename_stem = extrastring_taskname

    Q2_N_OPTIONS = 6
    Q3_N_OPTIONS = 11
    Q4_N_OPTIONS = 5
    Q4_OPTION_PSYCH_BEFORE_PHYSICAL = 1
    Q4_OPTION_PSYCH_AFTER_PHYSICAL = 2
    Q8_N_OPTIONS = 2
    Q7B_MIN = 1
    Q7B_MAX = 10

    q1_age_first_inflammatory_sx: Mapped[Optional[int]] = mapped_column(
        comment="Age (y) at onset of first symptoms of inflammatory disease",
    )
    q2_when_psych_sx_started: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=PermittedValueChecker(
            minimum=1, maximum=Q2_N_OPTIONS
        ),
        comment="Timing of onset of psych symptoms (1 = NA, 2 = before "
        "physical symptoms [Sx], 3 = same time as physical Sx but "
        "before diagnosis [Dx], 4 = around time of Dx, 5 = weeks or "
        "months after Dx, 6 = years after Dx)",
    )
    q3_worst_symptom_last_month: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=PermittedValueChecker(
            minimum=1, maximum=Q3_N_OPTIONS
        ),
        comment="Worst symptom in last month (1 = fatigue, 2 = low mood, 3 = "
        "irritable, 4 = anxiety, 5 = brain fog/confused, 6 = pain, "
        "7 = bowel Sx, 8 = mobility, 9 = skin, 10 = other, 11 = no Sx "
        "in past month)",
    )
    q4a_symptom_timing: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=PermittedValueChecker(
            minimum=1, maximum=Q4_N_OPTIONS
        ),
        comment="Timing of brain/psych Sx relative to physical Sx (1 = brain "
        "before physical, 2 = brain after physical, 3 = same time, "
        "4 = no relationship, 5 = none of the above)",
    )
    q4b_days_psych_before_phys: Mapped[Optional[int]] = mapped_column(
        comment="If Q4a == 1, number of days that brain Sx typically begin "
        "before physical Sx",
    )
    q4c_days_psych_after_phys: Mapped[Optional[int]] = mapped_column(
        comment="If Q4a == 2, number of days that brain Sx typically begin "
        "after physical Sx",
    )
    q5_antibiotics: Mapped[Optional[bool]] = mapped_bool_column(
        "q5_antibiotics",
        comment="Medication for infection (e.g. antibiotics) in past 3 months?"
        " (0 = no, 1 = yes)",
    )
    q6a_inpatient_last_y: Mapped[Optional[bool]] = mapped_bool_column(
        "q6a_inpatient_last_y",
        comment="Inpatient in the last year? (0 = no, 1 = yes)",
    )
    q6b_inpatient_weeks: Mapped[Optional[int]] = mapped_column(
        comment="If Q6a is true, approximate number of weeks spent as an "
        "inpatient in the past year",
    )
    q7a_sx_last_2y: Mapped[Optional[bool]] = mapped_bool_column(
        "q7a_sx_last_2y",
        comment="Symptoms within the last 2 years? (0 = no, 1 = yes)",
    )
    q7b_variability: Mapped[Optional[int]] = mapped_column(
        comment="If Q7a is true, degree of variability of symptoms (1-10 "
        "where 1 = highly variable [from none to severe], 10 = "
        "there all the time)",
    )
    q8_smoking: Mapped[Optional[int]] = mapped_column(
        comment="Current smoking status (0 = no, 1 = yes but not every day, "
        "2 = every day)",
    )
    q9_pregnant: Mapped[Optional[bool]] = mapped_bool_column(
        "q9_pregnant", comment="Currently pregnant (0 = no or N/A, 1 = yes)"
    )
    q10a_effective_rx_physical: Mapped[Optional[str]] = mapped_column(
        UnicodeText,
        comment="Most effective treatments for physical Sx",
    )
    q10b_effective_rx_psych: Mapped[Optional[str]] = mapped_column(
        UnicodeText,
        comment="Most effective treatments for brain/psychiatric Sx",
    )
    q11a_ph_depression: Mapped[Optional[bool]] = mapped_bool_column(
        "q11a_ph_depression", comment="Personal history of depression?"
    )
    q11b_ph_bipolar: Mapped[Optional[bool]] = mapped_bool_column(
        "q11b_ph_bipolar", comment="Personal history of bipolar disorder?"
    )
    q11c_ph_schizophrenia: Mapped[Optional[bool]] = mapped_bool_column(
        "q11c_ph_schizophrenia", comment="Personal history of schizophrenia?"
    )
    q11d_ph_autistic_spectrum: Mapped[Optional[bool]] = mapped_bool_column(
        "q11d_ph_autistic_spectrum",
        comment="Personal history of autism/Asperger's?",
    )
    q11e_ph_ptsd: Mapped[Optional[bool]] = mapped_bool_column(
        "q11e_ph_ptsd", comment="Personal history of PTSD?"
    )
    q11f_ph_other_anxiety: Mapped[Optional[bool]] = mapped_bool_column(
        "q11f_ph_other_anxiety",
        comment="Personal history of other anxiety disorders?",
    )
    q11g_ph_personality_disorder: Mapped[Optional[bool]] = mapped_bool_column(
        "q11g_ph_personality_disorder",
        comment="Personal history of personality disorder?",
    )
    q11h_ph_other_psych: Mapped[Optional[bool]] = mapped_bool_column(
        "q11h_ph_other_psych",
        comment="Personal history of other psychiatric disorder(s)?",
    )
    q11h_ph_other_detail: Mapped[Optional[str]] = mapped_column(
        UnicodeText,
        comment="If q11h_ph_other_psych is true, this is the free-text "
        "details field",
    )
    q12a_fh_depression: Mapped[Optional[bool]] = mapped_bool_column(
        "q12a_fh_depression", comment="Family history of depression?"
    )
    q12b_fh_bipolar: Mapped[Optional[bool]] = mapped_bool_column(
        "q12b_fh_bipolar", comment="Family history of bipolar disorder?"
    )
    q12c_fh_schizophrenia: Mapped[Optional[bool]] = mapped_bool_column(
        "q12c_fh_schizophrenia", comment="Family history of schizophrenia?"
    )
    q12d_fh_autistic_spectrum: Mapped[Optional[bool]] = mapped_bool_column(
        "q12d_fh_autistic_spectrum",
        comment="Family history of autism/Asperger's?",
    )
    q12e_fh_ptsd: Mapped[Optional[bool]] = mapped_bool_column(
        "q12e_fh_ptsd", comment="Family history of PTSD?"
    )
    q12f_fh_other_anxiety: Mapped[Optional[bool]] = mapped_bool_column(
        "q12f_fh_other_anxiety",
        comment="Family history of other anxiety disorders?",
    )
    q12g_fh_personality_disorder: Mapped[Optional[bool]] = mapped_bool_column(
        "q12g_fh_personality_disorder",
        comment="Family history of personality disorder?",
    )
    q12h_fh_other_psych: Mapped[Optional[bool]] = mapped_bool_column(
        "q12h_fh_other_psych",
        comment="Family history of other psychiatric disorder(s)?",
    )
    q12h_fh_other_detail: Mapped[Optional[str]] = mapped_column(
        UnicodeText,
        comment="If q12h_fh_other_psych is true, this is the free-text "
        "details field",
    )
    q13a_behcet: Mapped[Optional[bool]] = mapped_bool_column(
        "q13a_behcet", comment="Behçet’s syndrome? (0 = no, 1 = yes)"
    )
    q13b_oral_ulcers: Mapped[Optional[bool]] = mapped_bool_column(
        "q13b_oral_ulcers",
        comment="(If Behçet’s) Oral ulcers? (0 = no, 1 = yes)",
    )
    q13c_oral_age_first: Mapped[Optional[int]] = mapped_column(
        comment="(If Behçet’s + oral) Age (y) at first oral ulcers",
    )
    q13d_oral_scarring: Mapped[Optional[bool]] = mapped_bool_column(
        "q13d_oral_scarring",
        comment="(If Behçet’s + oral) Oral scarring? (0 = no, 1 = yes)",
    )
    q13e_genital_ulcers: Mapped[Optional[bool]] = mapped_bool_column(
        "q13e_genital_ulcers",
        comment="(If Behçet’s) Genital ulcers? (0 = no, 1 = yes)",
    )
    q13f_genital_age_first: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="(If Behçet’s + genital) Age (y) at first genital ulcers",
    )
    q13g_genital_scarring: Mapped[Optional[bool]] = mapped_bool_column(
        "q13g_genital_scarring",
        comment="(If Behçet’s + genital) Genital scarring? (0 = no, 1 = yes)",
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Lynall M-E — 1 — IAM — Medical history")

    def is_complete(self) -> bool:
        if self.any_fields_none(
            [
                "q1_age_first_inflammatory_sx",
                "q2_when_psych_sx_started",
                "q3_worst_symptom_last_month",
                "q4a_symptom_timing",
                "q5_antibiotics",
                "q6a_inpatient_last_y",
                "q7a_sx_last_2y",
                "q8_smoking",
                "q9_pregnant",
                "q10a_effective_rx_physical",
                "q10b_effective_rx_psych",
                "q13a_behcet",
            ]
        ):
            return False
        if self.any_fields_null_or_empty_str(
            ["q10a_effective_rx_physical", "q10b_effective_rx_psych"]
        ):
            return False
        q4a = self.q4a_symptom_timing
        if (
            q4a == self.Q4_OPTION_PSYCH_BEFORE_PHYSICAL
            and self.q4b_days_psych_before_phys is None
        ):
            return False
        if (
            q4a == self.Q4_OPTION_PSYCH_AFTER_PHYSICAL
            and self.q4c_days_psych_after_phys is None
        ):
            return False
        if self.q6a_inpatient_last_y and self.q6b_inpatient_weeks is None:
            return False
        if self.q7a_sx_last_2y and self.q7b_variability is None:
            return False
        if self.q11h_ph_other_psych and not self.q11h_ph_other_detail:
            return False
        if self.q12h_fh_other_psych and not self.q12h_fh_other_detail:
            return False
        if self.q13a_behcet:
            if self.any_fields_none(
                ["q13b_oral_ulcers", "q13e_genital_ulcers"]
            ):
                return False
            if self.q13b_oral_ulcers:
                if self.any_fields_none(
                    ["q13c_oral_age_first", "q13d_oral_scarring"]
                ):
                    return False
            if self.q13e_genital_ulcers:
                if self.any_fields_none(
                    ["q13f_genital_age_first", "q13g_genital_scarring"]
                ):
                    return False
        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        def plainrow(
            qname: str,
            xstring_name: str,
            value: Any,
            if_applicable: bool = False,
            qsuffix: str = "",
        ) -> str:
            ia_str = (
                f"<i>[{req.wsstring(SS.IF_APPLICABLE)}]</i> "
                if if_applicable
                else ""
            )
            q = f"{ia_str}{qname}. {self.wxstring(req, xstring_name)}{qsuffix}"
            return tr_qa(q, value)

        def lookuprow(
            qname: str,
            xstring_name: str,
            key: Optional[int],
            lookup: Dict[int, str],
            if_applicable: bool = False,
            qsuffix: str = "",
        ) -> str:
            description = lookup.get(key, None)
            value = None if description is None else f"{key}: {description}"
            return plainrow(
                qname,
                xstring_name,
                value,
                if_applicable=if_applicable,
                qsuffix=qsuffix,
            )

        def boolrow(
            qname: str,
            xstring_name: str,
            value: Optional[bool],
            lookup: Dict[int, str],
            if_applicable: bool = False,
            qsuffix: str = "",
        ) -> str:
            v = int(value) if value is not None else None
            return lookuprow(
                qname,
                xstring_name,
                v,
                lookup,
                if_applicable=if_applicable,
                qsuffix=qsuffix,
            )

        def ynrow(
            qname: str, xstring_name: str, value: Optional[Union[int, bool]]
        ) -> str:
            return plainrow(qname, xstring_name, get_yes_no(req, value))

        def ynnrow(
            qname: str,
            xstring_name: str,
            value: Optional[Union[int, bool]],
            if_applicable: bool = False,
        ) -> str:
            return plainrow(
                qname,
                xstring_name,
                get_yes_no_none(req, value),
                if_applicable=if_applicable,
            )

        q2_options = self.make_options_from_xstrings(
            req, "q2_option", 1, self.Q2_N_OPTIONS
        )
        q3_options = self.make_options_from_xstrings(
            req, "q3_option", 1, self.Q3_N_OPTIONS
        )
        q4a_options = self.make_options_from_xstrings(
            req, "q4a_option", 1, self.Q4_N_OPTIONS
        )
        q7a_options = self.make_options_from_xstrings(req, "q7a_option", 0, 1)
        _q7b_anchors = []  # type: List[str]
        for _o in (1, 10):
            _wxstring = self.wxstring(req, f"q7b_anchor_{_o}")
            _q7b_anchors.append(f"{_o}: {_wxstring}")
        q7b_explanation = f" <i>(Anchors: {' // '.join(_q7b_anchors)})</i>"
        q8_options = self.make_options_from_xstrings(
            req, "q8_option", 1, self.Q8_N_OPTIONS
        )
        q9_options = self.make_options_from_xstrings(req, "q9_option", 0, 1)

        rows_1_to_9 = "".join(
            [
                plainrow(
                    "1", "q1_question", self.q1_age_first_inflammatory_sx
                ),
                lookuprow(
                    "2",
                    "q2_question",
                    self.q2_when_psych_sx_started,
                    q2_options,
                ),
                lookuprow(
                    "3",
                    "q3_question",
                    self.q3_worst_symptom_last_month,
                    q3_options,
                ),
                lookuprow(
                    "4a", "q4a_question", self.q4a_symptom_timing, q4a_options
                ),
                plainrow(
                    "4b", "q4b_question", self.q4b_days_psych_before_phys, True
                ),
                plainrow(
                    "4c", "q4c_question", self.q4c_days_psych_after_phys, True
                ),
                ynnrow("5", "q5_question", self.q5_antibiotics),
                ynnrow("6a", "q6a_question", self.q6a_inpatient_last_y),
                plainrow("6b", "q6b_question", self.q6b_inpatient_weeks, True),
                boolrow(
                    "7a", "q7a_question", self.q7a_sx_last_2y, q7a_options
                ),
                plainrow(
                    "7b",
                    "q7b_question",
                    self.q7b_variability,
                    True,
                    qsuffix=q7b_explanation,
                ),
                lookuprow("8", "q8_question", self.q8_smoking, q8_options),
                boolrow("9", "q9_question", self.q9_pregnant, q9_options),
            ]
        )

        rows_10a_and_10b = "".join(
            [
                plainrow(
                    "10a", "q10a_question", self.q10a_effective_rx_physical
                ),
                plainrow("10b", "q10b_question", self.q10b_effective_rx_psych),
            ]
        )

        rows_11a_to_11h = "".join(
            [
                ynrow("11a", "depression", self.q11a_ph_depression),
                ynrow("11b", "bipolar", self.q11b_ph_bipolar),
                ynrow("11c", "schizophrenia", self.q11c_ph_schizophrenia),
                ynrow(
                    "11d", "autistic_spectrum", self.q11d_ph_autistic_spectrum
                ),
                ynrow("11e", "ptsd", self.q11e_ph_ptsd),
                ynrow("11f", "other_anxiety", self.q11f_ph_other_anxiety),
                ynrow(
                    "11g",
                    "personality_disorder",
                    self.q11g_ph_personality_disorder,
                ),
                ynrow("11h", "other_psych", self.q11h_ph_other_psych),
                plainrow(
                    "11h", "other_psych", self.q11h_ph_other_detail, True
                ),
            ]
        )

        rows_12a_to_12h = "".join(
            [
                ynrow("12a", "depression", self.q12a_fh_depression),
                ynrow("12b", "bipolar", self.q12b_fh_bipolar),
                ynrow("12c", "schizophrenia", self.q12c_fh_schizophrenia),
                ynrow(
                    "12d", "autistic_spectrum", self.q12d_fh_autistic_spectrum
                ),
                ynrow("12e", "ptsd", self.q12e_fh_ptsd),
                ynrow("12f", "other_anxiety", self.q12f_fh_other_anxiety),
                ynrow(
                    "12g",
                    "personality_disorder",
                    self.q12g_fh_personality_disorder,
                ),
                ynrow("12h", "other_psych", self.q12h_fh_other_psych),
                plainrow(
                    "12h", "other_psych", self.q12h_fh_other_detail, True
                ),
            ]
        )

        rows_13a_to_13g = "".join(
            [
                ynnrow("13a", "q13a_question", self.q13a_behcet),
                ynnrow("13b", "q13b_question", self.q13b_oral_ulcers, True),
                plainrow(
                    "13c", "q13c_question", self.q13c_oral_age_first, True
                ),
                ynnrow("13d", "q13d_question", self.q13d_oral_scarring, True),
                ynnrow("13e", "q13e_question", self.q13e_genital_ulcers, True),
                plainrow(
                    "13f", "q13f_question", self.q13f_genital_age_first, True
                ),
                ynnrow(
                    "13g", "q13g_question", self.q13g_genital_scarring, True
                ),
            ]
        )

        return f"""
          <div class="{CssClass.SUMMARY}">
            <table class="{CssClass.SUMMARY}">
              {self.get_is_complete_tr(req)}
            </table>
          </div>
          <table class="{CssClass.TASKDETAIL}">
            <tr>
              <th width="60%">{req.sstring(SS.QUESTION)}</th>
              <th width="40%">{req.sstring(SS.ANSWER)}</th>
            </tr>
            {rows_1_to_9}
            <tr class="subheading">
              <td><i>{self.wxstring(req, "q10_stem")}</i></td>
              <td></td>
            </tr>
            {rows_10a_and_10b}
            <tr class="subheading">
              <td><i>{self.wxstring(req, "q11_title")}</i></td>
              <td></td>
            </tr>
            {rows_11a_to_11h}
            <tr class="subheading">
              <td><i>{self.wxstring(req, "q12_title")}</i></td>
              <td></td>
            </tr>
            {rows_12a_to_12h}
            <tr class="subheading">
              <td><i>{self.wxstring(req, "q13_title")}</i></td>
              <td></td>
            </tr>
            {rows_13a_to_13g}
          </table>
        """
