#!/usr/bin/env python

"""
camcops_server/tasks/apeqpt.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

- By Joe Kearney, Rudolf Cardinal.

"""

from typing import Dict, List, TYPE_CHECKING

from fhirclient.models.questionnaire import (
    QuestionnaireItem,
    QuestionnaireItemAnswerOption,
)
from fhirclient.models.questionnaireresponse import (
    QuestionnaireResponseItem,
    QuestionnaireResponseItemAnswer,
)
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    PendulumDateTimeAsIsoTextColType,
    ZERO_TO_ONE_CHECKER,
    ZERO_TO_TWO_CHECKER,
    ZERO_TO_FOUR_CHECKER
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
)

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient


# =============================================================================
# APEQPT
# =============================================================================

class Apeqpt(Task):
    """
    Server implementation of the APEQPT task.
    """
    __tablename__ = "apeqpt"
    shortname = "APEQPT"
    provides_trackers = True

    q_datetime = CamcopsColumn(
        "q_datetime", PendulumDateTimeAsIsoTextColType,
        comment="Date/time the assessment tool was completed")

    N_CHOICE_QUESTIONS = 3
    q1_choice = CamcopsColumn(
        "q1_choice", Integer,
        comment="Enough information was provided (0 no, 1 yes)",
        permitted_value_checker=ZERO_TO_ONE_CHECKER)
    q2_choice = CamcopsColumn(
        "q2_choice", Integer,
        comment="Treatment preference (0 no, 1 yes)",
        permitted_value_checker=ZERO_TO_ONE_CHECKER)
    q3_choice = CamcopsColumn(
        "q3_choice", Integer,
        comment="Preference offered (0 no, 1 yes, 2 N/A)",
        permitted_value_checker=ZERO_TO_TWO_CHECKER)

    q1_satisfaction = CamcopsColumn(
        "q1_satisfaction", Integer,
        comment=(
            "Patient satisfaction (0 not at all satisfied - "
            "4 completely satisfied)"
        ),
        permitted_value_checker=ZERO_TO_FOUR_CHECKER)
    q2_satisfaction = CamcopsColumn(
        "q2_satisfaction", UnicodeText,
        comment="Service experience")

    MAIN_QUESTIONS = [
        "q_datetime",
        "q1_choice",
        "q2_choice",
        "q3_choice",
        "q1_satisfaction",
    ]

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Assessment Patient Experience Questionnaire "
                 "for Psychological Therapies")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.MAIN_QUESTIONS):
            return False
        if not self.field_contents_valid():
            return False
        return True

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def get_task_html(self, req: CamcopsRequest) -> str:
        c_dict = {
            0: "0 — " + self.wxstring(req, "a0_choice"),
            1: "1 — " + self.wxstring(req, "a1_choice"),
            2: "2 — " + self.wxstring(req, "a2_choice"),
        }
        s_dict = {
            0: "0 — " + self.wxstring(req, "a0_satisfaction"),
            1: "1 — " + self.wxstring(req, "a1_satisfaction"),
            2: "2 — " + self.wxstring(req, "a2_satisfaction"),
            3: "3 — " + self.wxstring(req, "a3_satisfaction"),
            4: "4 — " + self.wxstring(req, "a4_satisfaction"),
        }
        q_a = ""
        for i in range(1, self.N_CHOICE_QUESTIONS + 1):
            nstr = str(i)
            q_a += tr_qa(
                self.wxstring(req, "q" + nstr + "_choice"),
                get_from_dict(c_dict, getattr(self, "q" + nstr + "_choice")))

        q_a += tr_qa(self.wxstring(req, "q1_satisfaction"),
                     get_from_dict(s_dict, self.q1_satisfaction))
        q_a += tr_qa(self.wxstring(req, "q2_satisfaction"),
                     self.q2_satisfaction, default="")

        return f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                Patient satisfaction rating for service provided. The service
                is rated on choice offered and general satisfaction.
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a}
            </table>
        """

    def get_fhir_questionnaire_items(
            self,
            req: "CamcopsRequest",
            recipient: "ExportRecipient") -> List[Dict]:
        items = [
            QuestionnaireItem(jsondict={
                "linkId": "q_datetime",
                "text": self.wxstring(req, "q_date"),
                "type": "dateTime",
            }).as_json()
        ]

        yes_no_options = []

        for index in range(2):
            yes_no_options.append(QuestionnaireItemAnswerOption(jsondict={
                "valueCoding": {
                    "code": str(index),
                    "display": self.wxstring(req, f"a{index}_choice"),
                }
            }).as_json())

        items.append(QuestionnaireItem(jsondict={
            "linkId": "q1_choice",
            "text": self.wxstring(req, "q1_choice"),
            "type": "choice",
            "answerOption": yes_no_options,
        }).as_json())

        items.append(QuestionnaireItem(jsondict={
            "linkId": "q2_choice",
            "text": self.wxstring(req, "q2_choice"),
            "type": "choice",
            "answerOption": yes_no_options,
        }).as_json())

        yes_no_na_options = yes_no_options + [
            QuestionnaireItemAnswerOption(
                jsondict={
                    "valueCoding": {
                        "code": "2",
                        "display": self.wxstring(req, "a2_choice"),
                    }
                }
            ).as_json()
        ]

        items.append(QuestionnaireItem(jsondict={
            "linkId": "q3_choice",
            "text": self.wxstring(req, "q3_choice"),
            "type": "choice",
            "answerOption": yes_no_na_options,
        }).as_json())

        satisfaction_options = []

        for index in range(5):
            satisfaction_options.append(QuestionnaireItemAnswerOption(jsondict={
                "valueCoding": {
                    "code": str(index),
                    "display": self.wxstring(req, f"a{index}_satisfaction"),
                }
            }).as_json())

        items.append(QuestionnaireItem(jsondict={
            "linkId": "q1_satisfaction",
            "text": self.wxstring(req, "q1_satisfaction"),
            "type": "choice",
            "answerOption": satisfaction_options,
        }).as_json())

        items.append(QuestionnaireItem(jsondict={
            "linkId": "q2_satisfaction",
            "text": self.wxstring(req, "q2_satisfaction"),
            "type": "string",
        }).as_json())

        return items

    def get_fhir_questionnaire_response_items(
            self,
            req: "CamcopsRequest",
            recipient: "ExportRecipient") -> List[Dict]:

        items = []

        answer = QuestionnaireResponseItemAnswer(jsondict={
            "valueDateTime": self.q_datetime.isoformat()
        })
        items.append(QuestionnaireResponseItem(jsondict={
            "linkId": "q_datetime",
            "text": self.wxstring(req, "q_date"),
            "answer": [answer.as_json()],
        }).as_json())

        answer = QuestionnaireResponseItemAnswer(jsondict={
            "valueInteger": self.q1_choice
        })
        items.append(QuestionnaireResponseItem(jsondict={
            "linkId": "q1_choice",
            "text": self.wxstring(req, "q1_choice"),
            "answer": [answer.as_json()],
        }).as_json())

        answer = QuestionnaireResponseItemAnswer(jsondict={
            "valueInteger": self.q2_choice
        })
        items.append(QuestionnaireResponseItem(jsondict={
            "linkId": "q2_choice",
            "text": self.wxstring(req, "q2_choice"),
            "answer": [answer.as_json()],
        }).as_json())

        answer = QuestionnaireResponseItemAnswer(jsondict={
            "valueInteger": self.q3_choice
        })
        items.append(QuestionnaireResponseItem(jsondict={
            "linkId": "q3_choice",
            "text": self.wxstring(req, "q3_choice"),
            "answer": [answer.as_json()],
        }).as_json())

        answer = QuestionnaireResponseItemAnswer(jsondict={
            "valueInteger": self.q1_satisfaction
        })
        items.append(QuestionnaireResponseItem(jsondict={
            "linkId": "q1_satisfaction",
            "text": self.wxstring(req, "q1_satisfaction"),
            "answer": [answer.as_json()],
        }).as_json())

        answer = QuestionnaireResponseItemAnswer(jsondict={
            "valueString": self.q2_satisfaction
        })
        items.append(QuestionnaireResponseItem(jsondict={
            "linkId": "q2_satisfaction",
            "text": self.wxstring(req, "q2_satisfaction"),
            "answer": [answer.as_json()],
        }).as_json())

        return items
