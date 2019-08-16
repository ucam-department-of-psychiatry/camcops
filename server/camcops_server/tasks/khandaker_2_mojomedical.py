#!/usr/bin/env python

"""
camcops_server/tasks/khandaker_2_mojomedical.py

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

"""

from typing import Any, Dict, Tuple, Type


from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Date, Float, Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    BoolColumn,
    CamcopsColumn,
    ZERO_TO_TWO_CHECKER,
)
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)


class Khandaker2MojoMedicalMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Khandaker2MojoMedical'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:

        setattr(
            cls, cls.FN_PARTICIPANT_NUMBER,
            CamcopsColumn(
                cls.FN_PARTICIPANT_NUMBER, UnicodeText,
                comment="Participant study number"
            )
        )

        setattr(
            cls, cls.FN_DIAGNOSIS,
            CamcopsColumn(
                cls.FN_DIAGNOSIS, Integer,
                permitted_value_checker=ZERO_TO_TWO_CHECKER,
                comment=("Diagnosis (0 Rheumatoid Arthritis, "
                         "1 Ankylosing Spondylitis, 2 Sjögren’s Syndrome)")
            )
        )

        setattr(
            cls, cls.FN_DIAGNOSIS_DATE,
            CamcopsColumn(
                cls.FN_DIAGNOSIS_DATE, Date,
                comment=("Date of first diagnosis (may be approx from "
                         "'duration of illness (years))'")
            )
        )

        setattr(
            cls, cls.FN_HAS_FIBROMYALGIA,
            BoolColumn(
                cls.FN_HAS_FIBROMYALGIA,
                comment="Do you have a diagnosis of fibromyalgia?"
            )
        )

        setattr(
            cls, cls.FN_IS_PREGNANT,
            BoolColumn(
                cls.FN_IS_PREGNANT,
                comment=("Are you, or is there any possibility that you might "
                         "be pregnant?")
            )
        )

        setattr(
            cls, cls.FN_HAS_INFECTION_PAST_MONTH,
            BoolColumn(
                cls.FN_HAS_INFECTION_PAST_MONTH,
                comment=("Do you currently have an infection, or had "
                         "treatment for an infection (e.g antibiotics) "
                         "in the past month?")
            )
        )

        setattr(
            cls, cls.FN_HAD_INFECTION_TWO_MONTHS_PRECEDING,
            BoolColumn(
                cls.FN_HAD_INFECTION_TWO_MONTHS_PRECEDING,
                comment=("Have you had an infection, or had treatment for "
                         "an infection (e.g antibiotics) in the 2 months "
                         "preceding last month?"),
                constraint_name="ck_kh2mm_had_infection"
            )
        )

        setattr(
            cls, cls.FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE,
            BoolColumn(
                cls.FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE,
                comment=("Do you have a current diagnosis of alcohol or "
                         "substance dependence?"),
                constraint_name="ck_kh2mm_has_alcohol"
            )
        )

        setattr(
            cls, cls.FN_SMOKING_STATUS,
            CamcopsColumn(
                cls.FN_SMOKING_STATUS, Integer,
                permitted_value_checker=ZERO_TO_TWO_CHECKER,
                comment=("What is your smoking status? (0 Never smoked, "
                         "1 Ex-smoker, 2 Current smoker)")
            )
        )

        setattr(
            cls, cls.FN_ALCOHOL_UNITS_PER_WEEK,
            CamcopsColumn(
                cls.FN_ALCOHOL_UNITS_PER_WEEK, Float,
                comment=("How much alcohol do you drink per week? (medium "
                         "glass of wine = 2 units, pint of beer at 4.5% = "
                         "2.5 units, 25ml of spirits at 40% = 1 unit)")
            )
        )

        setattr(
            cls, cls.FN_DEPRESSION,
            BoolColumn(
                cls.FN_DEPRESSION,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_BIPOLAR_DISORDER,
            BoolColumn(
                cls.FN_BIPOLAR_DISORDER,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_SCHIZOPHRENIA,
            BoolColumn(
                cls.FN_SCHIZOPHRENIA,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_AUTISM,
            BoolColumn(
                cls.FN_AUTISM,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_PTSD,
            BoolColumn(
                cls.FN_PTSD,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_ANXIETY,
            BoolColumn(
                cls.FN_ANXIETY,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_PERSONALITY_DISORDER,
            BoolColumn(
                cls.FN_PERSONALITY_DISORDER,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_INTELLECTUAL_DISABILITY,
            BoolColumn(
                cls.FN_INTELLECTUAL_DISABILITY,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_OTHER_MENTAL_ILLNESS,
            BoolColumn(
                cls.FN_OTHER_MENTAL_ILLNESS,
                comment=("Have you had any of the following conditions "
                         "diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_OTHER_MENTAL_ILLNESS_DETAILS,
            CamcopsColumn(
                cls.FN_OTHER_MENTAL_ILLNESS_DETAILS, UnicodeText,
                comment="If other, please list here"
            )
        )

        setattr(
            cls, cls.FN_HOSPITALISED_IN_LAST_YEAR,
            BoolColumn(
                cls.FN_HOSPITALISED_IN_LAST_YEAR,
                comment=("Have you had a physical or mental illness "
                         "requiring hospitalisation in the previous 12 "
                         "months?")
            )
        )

        setattr(
            cls, cls.FN_HOSPITALISATION_DETAILS,
            CamcopsColumn(
                cls.FN_HOSPITALISATION_DETAILS, UnicodeText,
                comment=("If yes, please list here (name of illness, number "
                         "of hospitilisations and duration):")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_DEPRESSION,
            BoolColumn(
                cls.FN_FAMILY_DEPRESSION,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_BIPOLAR_DISORDER,
            BoolColumn(
                cls.FN_FAMILY_BIPOLAR_DISORDER,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_SCHIZOPHRENIA,
            BoolColumn(
                cls.FN_FAMILY_SCHIZOPHRENIA,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_AUTISM,
            BoolColumn(
                cls.FN_FAMILY_AUTISM,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_PTSD,
            BoolColumn(
                cls.FN_FAMILY_PTSD,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_ANXIETY,
            BoolColumn(
                cls.FN_FAMILY_ANXIETY,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_PERSONALITY_DISORDER,
            BoolColumn(
                cls.FN_FAMILY_PERSONALITY_DISORDER,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_INTELLECTUAL_DISABILITY,
            BoolColumn(
                cls.FN_FAMILY_INTELLECTUAL_DISABILITY,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?"),
                constraint_name="ck_kh2mm_fam_int_dis"
            )
        )

        setattr(
            cls, cls.FN_FAMILY_OTHER_MENTAL_ILLNESS,
            BoolColumn(
                cls.FN_FAMILY_OTHER_MENTAL_ILLNESS,
                comment=("Has anyone in your immediate family "
                         "(parents, siblings or children) had any of the "
                         "following conditions diagnosed by a doctor?")
            )
        )

        setattr(
            cls, cls.FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS,
            CamcopsColumn(
                cls.FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS, UnicodeText,
                comment="If other, please list here"
            )
        )

        super().__init__(name, bases, classdict)


class Khandaker2MojoMedical(
        TaskHasPatientMixin, Task,
        metaclass=Khandaker2MojoMedicalMetaclass):
    """
    Server implementation of the Khandaker_2_MOJOMedical task
    """
    __tablename__ = "khandaker_2_mojomedical"
    shortname = "Khandaker_2_MOJOMedical"
    provides_trackers = False

    # Section 1: General Information
    FN_PARTICIPANT_NUMBER = "participant_number"
    FN_DIAGNOSIS = "diagnosis"
    FN_DIAGNOSIS_DATE = "diagnosis_date"
    FN_HAS_FIBROMYALGIA = "has_fibromyalgia"
    FN_IS_PREGNANT = "is_pregnant"
    FN_HAS_INFECTION_PAST_MONTH = "has_infection_past_month"
    FN_HAD_INFECTION_TWO_MONTHS_PRECEDING = "had_infection_two_months_preceding"  # noqa
    FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE = "has_alcohol_substance_dependence"
    FN_SMOKING_STATUS = "smoking_status"
    FN_ALCOHOL_UNITS_PER_WEEK = "alcohol_units_per_week"

    # Section 2: Medical History
    FN_DEPRESSION = "depression"
    FN_BIPOLAR_DISORDER = "bipolar_disorder"
    FN_SCHIZOPHRENIA = "schizophrenia"
    FN_AUTISM = "autism"
    FN_PTSD = "ptsd"
    FN_ANXIETY = "anxiety"
    FN_PERSONALITY_DISORDER = "personality_disorder"
    FN_INTELLECTUAL_DISABILITY = "intellectual_disability"
    FN_OTHER_MENTAL_ILLNESS = "other_mental_illness"
    FN_OTHER_MENTAL_ILLNESS_DETAILS = "other_mental_illness_details"
    FN_HOSPITALISED_IN_LAST_YEAR = "hospitalised_in_last_year"
    FN_HOSPITALISATION_DETAILS = "hospitalisation_details"

    # Section 3: Family history
    FN_FAMILY_DEPRESSION = "family_depression"
    FN_FAMILY_BIPOLAR_DISORDER = "family_bipolar_disorder"
    FN_FAMILY_SCHIZOPHRENIA = "family_schizophrenia"
    FN_FAMILY_AUTISM = "family_autism"
    FN_FAMILY_PTSD = "family_ptsd"
    FN_FAMILY_ANXIETY = "family_anxiety"
    FN_FAMILY_PERSONALITY_DISORDER = "family_personality_disorder"
    FN_FAMILY_INTELLECTUAL_DISABILITY = "family_intellectual_disability"
    FN_FAMILY_OTHER_MENTAL_ILLNESS = "family_other_mental_illness"
    FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS = "family_other_mental_illness_details"  # noqa

    MANDATORY_FIELD_NAMES = [
        FN_PARTICIPANT_NUMBER,
        FN_DIAGNOSIS,
        FN_DIAGNOSIS_DATE,
        FN_HAS_FIBROMYALGIA,
        FN_IS_PREGNANT,
        FN_HAS_INFECTION_PAST_MONTH,
        FN_HAD_INFECTION_TWO_MONTHS_PRECEDING,
        FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE,
        FN_SMOKING_STATUS,
        FN_ALCOHOL_UNITS_PER_WEEK,

        FN_DEPRESSION,
        FN_BIPOLAR_DISORDER,
        FN_SCHIZOPHRENIA,
        FN_AUTISM,
        FN_PTSD,
        FN_ANXIETY,
        FN_PERSONALITY_DISORDER,
        FN_INTELLECTUAL_DISABILITY,
        FN_OTHER_MENTAL_ILLNESS,
        FN_HOSPITALISED_IN_LAST_YEAR,

        FN_FAMILY_DEPRESSION,
        FN_FAMILY_BIPOLAR_DISORDER,
        FN_FAMILY_SCHIZOPHRENIA,
        FN_FAMILY_AUTISM,
        FN_FAMILY_PTSD,
        FN_FAMILY_ANXIETY,
        FN_FAMILY_PERSONALITY_DISORDER,
        FN_FAMILY_INTELLECTUAL_DISABILITY,
        FN_FAMILY_OTHER_MENTAL_ILLNESS,
    ]

    # If the answer is yes to any of these, we need to have the details
    DETAILS_FIELDS = {
        FN_OTHER_MENTAL_ILLNESS: FN_OTHER_MENTAL_ILLNESS_DETAILS,
        FN_HOSPITALISED_IN_LAST_YEAR: FN_HOSPITALISATION_DETAILS,
        FN_FAMILY_OTHER_MENTAL_ILLNESS: FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS,
    }

    MULTI_CHOICE_FIELD_NAMES = [
        FN_DIAGNOSIS,
        FN_SMOKING_STATUS,
    ]

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Khandaker GM — 2 MOJO Study — Medical Questionnaire")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.MANDATORY_FIELD_NAMES):
            return False

        if not self.field_contents_valid():
            return False

        for field_name, details_field_name in self.DETAILS_FIELDS.items():
            if getattr(self, field_name):
                if getattr(self, details_field_name) is None:
                    return False

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = ""

        for field_name in self.MANDATORY_FIELD_NAMES:
            question_text = self.wxstring(req, f"q_{field_name}")
            answer = getattr(self, field_name)

            answer_text = answer

            if answer is not None and (
                    field_name in self.MULTI_CHOICE_FIELD_NAMES):
                answer_text = self.wxstring(req, f"{field_name}_{answer}")

            rows += tr_qa(question_text, answer_text)

            if answer and field_name in self.DETAILS_FIELDS:
                details_field_name = self.DETAILS_FIELDS[field_name]
                details_question_text = self.wxstring(
                    req, f"q_{details_field_name}")
                details_answer = getattr(self, details_field_name)

                rows += tr_qa(details_question_text, details_answer)

        html = f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {rows}
            </table>
        """

        return html
