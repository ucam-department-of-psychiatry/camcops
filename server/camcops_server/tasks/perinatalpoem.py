#!/usr/bin/env python

"""
camcops_server/tasks/perinatalpoem.py

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

from typing import Dict, Generator, List, Optional, Tuple, Type

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.datetimefunc import format_datetime
from pyramid.renderers import render_to_response
from pyramid.response import Response
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import and_, column, func, select
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import (
    CssClass,
    DateFormat,
)
from camcops_server.cc_modules.cc_forms import (
    EndPendulumSelector,
    ReportParamSchema,
    StartPendulumSelector,
)
from camcops_server.cc_modules.cc_html import (
    get_yes_no_none,
    subheading_spanning_two_columns,
    tr_qa,
)
from camcops_server.cc_modules.cc_pyramid import (
    ViewParam,
)
from camcops_server.cc_modules.cc_report import Report
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
)
from camcops_server.cc_modules.cc_text import SS
from camcops_server.cc_modules.cc_tsv import TsvPage
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase


# =============================================================================
# Perinatal-POEM
# =============================================================================

class PerinatalPoem(Task):
    """
    Server implementation of the Perinatal-POEM task.
    """
    __tablename__ = "perinatal_poem"
    shortname = "Perinatal-POEM"
    provides_trackers = False

    # Field names
    FN_QA_RESPONDENT = "qa"
    FN_QB_SERVICE_TYPE = "qb"
    FN_Q1A_MH_FIRST_CONTACT = "q1a"
    FN_Q1B_MH_DISCHARGE = "q1b"
    FN_Q2A_STAFF_DID_NOT_COMMUNICATE = "q2a"
    FN_Q2B_STAFF_GAVE_RIGHT_SUPPORT = "q2b"
    FN_Q2C_HELP_NOT_QUICK_ENOUGH = "q2c"
    FN_Q2D_STAFF_LISTENED = "q2d"
    FN_Q2E_STAFF_DID_NOT_INVOLVE_ME = "q2e"
    FN_Q2F_SERVICE_PROVIDED_INFO = "q2f"
    FN_Q2G_STAFF_NOT_SENSITIVE_TO_ME = "q2g"
    FN_Q2H_STAFF_HELPED_ME_UNDERSTAND = "q2h"
    FN_Q2I_STAFF_NOT_SENSITIVE_TO_BABY = "q2i"
    FN_Q2J_STAFF_HELPED_MY_CONFIDENCE = "q2j"
    FN_Q2K_SERVICE_INVOLVED_OTHERS_HELPFULLY = "q2k"
    FN_Q2L_I_WOULD_RECOMMEND_SERVICE = "q2l"
    FN_Q3A_UNIT_CLEAN = "q3a"
    FN_Q3B_UNIT_NOT_GOOD_PLACE_TO_RECOVER = "q3b"
    FN_Q3C_UNIT_DID_NOT_PROVIDE_ACTIVITIES = "q3c"
    FN_Q3D_UNIT_GOOD_PLACE_FOR_BABY = "q3d"
    FN_Q3E_UNIT_SUPPORTED_FAMILY_FRIENDS_CONTACT = "q3e"
    FN_Q3F_FOOD_NOT_ACCEPTABLE = "q3f"
    FN_GENERAL_COMMENTS = "general_comments"
    FN_FUTURE_PARTICIPATION = "future_participation"
    FN_CONTACT_DETAILS = "contact_details"

    # Response values
    VAL_QA_PATIENT = 1
    VAL_QA_PARTNER_OTHER = 2

    VAL_QB_INPATIENT = 1  # inpatient = MBU = mother and baby unit
    VAL_QB_COMMUNITY = 2

    VAL_Q1_VERY_WELL = 1
    VAL_Q1_WELL = 2
    VAL_Q1_UNWELL = 3
    VAL_Q1_VERY_UNWELL = 4
    VAL_Q1_EXTREMELY_UNWELL = 5
    _MH_KEY = (
        f"({VAL_Q1_VERY_WELL} very well, {VAL_Q1_WELL} well, "
        f"{VAL_Q1_UNWELL} unwell, {VAL_Q1_VERY_UNWELL} very unwell, "
        f"{VAL_Q1_EXTREMELY_UNWELL} extremely unwell)"
    )

    VAL_STRONGLY_AGREE = 1
    VAL_AGREE = 2
    VAL_DISAGREE = 3
    VAL_STRONGLY_DISAGREE = 4
    _AGREE_KEY = (
        f"({VAL_STRONGLY_AGREE} strongly agree, {VAL_AGREE} agree, "
        f"{VAL_DISAGREE} disagree, {VAL_STRONGLY_DISAGREE} strongly disagree)"
    )

    _INPATIENT_ONLY = "[Inpatient services only]"

    YES_INT = 1
    NO_INT = 0

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------
    qa = Column(
        FN_QA_RESPONDENT, Integer,
        comment=(
            f"Question A: Is the respondent the patient ({VAL_QA_PATIENT}) "
            f"or other ({VAL_QA_PARTNER_OTHER})?"
        )
    )
    qb = Column(
        FN_QB_SERVICE_TYPE, Integer,
        comment=(
            f"Question B: Was the service type inpatient [mother-and-baby "
            f"unit, MBU] ({VAL_QB_INPATIENT}) or "
            f"community ({VAL_QB_COMMUNITY})?"
        )
    )

    q1a = Column(
        FN_Q1A_MH_FIRST_CONTACT, Integer,
        comment=f"Q1A: mental health at first contact {_MH_KEY}"
    )
    q1b = Column(
        FN_Q1B_MH_DISCHARGE, Integer,
        comment=f"Q1B: mental health at discharge {_MH_KEY}"
    )

    q2a = Column(
        FN_Q2A_STAFF_DID_NOT_COMMUNICATE, Integer,
        comment=f"Q2a: staff didn't communicate with others {_AGREE_KEY}"
    )
    q2b = Column(
        FN_Q2B_STAFF_GAVE_RIGHT_SUPPORT, Integer,
        comment=f"Q2b: Staff gave right amount of support {_AGREE_KEY}"
    )
    q2c = Column(
        FN_Q2C_HELP_NOT_QUICK_ENOUGH, Integer,
        comment=f"Q2c: Help not quick enough after referral {_AGREE_KEY}"
    )
    q2d = Column(
        FN_Q2D_STAFF_LISTENED, Integer,
        comment=f"Q2d: Staff listened/understood {_AGREE_KEY}"
    )

    q2e = Column(
        FN_Q2E_STAFF_DID_NOT_INVOLVE_ME, Integer,
        comment=f"Q2e: Staff didn't involve pt enough {_AGREE_KEY}"
    )
    q2f = Column(
        FN_Q2F_SERVICE_PROVIDED_INFO, Integer,
        comment=f"Q2f: Service provided information {_AGREE_KEY}"
    )
    q2g = Column(
        FN_Q2G_STAFF_NOT_SENSITIVE_TO_ME, Integer,
        comment=f"Q2g: Staff not very sensitive to pt {_AGREE_KEY}"
    )
    q2h = Column(
        FN_Q2H_STAFF_HELPED_ME_UNDERSTAND, Integer,
        comment=f"Q2h: Staff helped understanding of illness {_AGREE_KEY}"
    )

    q2i = Column(
        FN_Q2I_STAFF_NOT_SENSITIVE_TO_BABY, Integer,
        comment=f"Q2i: Staff not very sensitive to baby {_AGREE_KEY}"
    )
    q2j = Column(
        FN_Q2J_STAFF_HELPED_MY_CONFIDENCE, Integer,
        comment=f"Q2j: Staff helped confidence re baby {_AGREE_KEY}"
    )
    q2k = Column(
        FN_Q2K_SERVICE_INVOLVED_OTHERS_HELPFULLY, Integer,
        comment=f"Q2k: Service involved others helpfully {_AGREE_KEY}"
    )
    q2l = Column(
        FN_Q2L_I_WOULD_RECOMMEND_SERVICE, Integer,
        comment=f"Q2l: Would recommend service {_AGREE_KEY}"
    )

    q3a = Column(
        FN_Q3A_UNIT_CLEAN, Integer,
        comment=f"Q3a: MBU clean {_AGREE_KEY} {_INPATIENT_ONLY}"
    )
    q3b = Column(
        FN_Q3B_UNIT_NOT_GOOD_PLACE_TO_RECOVER, Integer,
        comment=f"Q3b: MBU not a good place to recover "
                f"{_AGREE_KEY} {_INPATIENT_ONLY}"
    )
    q3c = Column(
        FN_Q3C_UNIT_DID_NOT_PROVIDE_ACTIVITIES, Integer,
        comment=f"Q3c: MBU did not provide helpful activities "
                f"{_AGREE_KEY} {_INPATIENT_ONLY}"
    )
    q3d = Column(
        FN_Q3D_UNIT_GOOD_PLACE_FOR_BABY, Integer,
        comment=f"Q3d: MBU a good place for baby to be with pt "
                f"{_AGREE_KEY} {_INPATIENT_ONLY}"
    )
    q3e = Column(
        FN_Q3E_UNIT_SUPPORTED_FAMILY_FRIENDS_CONTACT, Integer,
        comment=f"Q3e: MBU supported contact with family/friends "
                f"{_AGREE_KEY} {_INPATIENT_ONLY}"
    )
    q3f = Column(
        FN_Q3F_FOOD_NOT_ACCEPTABLE, Integer,
        comment=f"Q3f: Food not acceptable {_AGREE_KEY} {_INPATIENT_ONLY}"
    )

    general_comments = Column(
        FN_GENERAL_COMMENTS, UnicodeText,
        comment="General comments"
    )
    future_participation = Column(
        FN_FUTURE_PARTICIPATION, Integer,
        comment=f"Willing to participate in future studies "
                f"({YES_INT} yes, {NO_INT} no)"
    )
    contact_details = Column(
        FN_CONTACT_DETAILS, UnicodeText,
        comment="Contact details"
    )

    # -------------------------------------------------------------------------
    # Fieldname collections
    # -------------------------------------------------------------------------
    REQUIRED_ALWAYS = [
        FN_QA_RESPONDENT,
        FN_QB_SERVICE_TYPE,
        FN_Q1A_MH_FIRST_CONTACT,
        FN_Q1B_MH_DISCHARGE,
        FN_Q2A_STAFF_DID_NOT_COMMUNICATE,
        FN_Q2B_STAFF_GAVE_RIGHT_SUPPORT,
        FN_Q2C_HELP_NOT_QUICK_ENOUGH,
        FN_Q2D_STAFF_LISTENED,
        FN_Q2E_STAFF_DID_NOT_INVOLVE_ME,
        FN_Q2F_SERVICE_PROVIDED_INFO,
        FN_Q2G_STAFF_NOT_SENSITIVE_TO_ME,
        FN_Q2H_STAFF_HELPED_ME_UNDERSTAND,
        FN_Q2I_STAFF_NOT_SENSITIVE_TO_BABY,
        FN_Q2J_STAFF_HELPED_MY_CONFIDENCE,
        FN_Q2K_SERVICE_INVOLVED_OTHERS_HELPFULLY,
        FN_Q2L_I_WOULD_RECOMMEND_SERVICE,
        # not FN_GENERAL_COMMENTS,
        FN_FUTURE_PARTICIPATION,
        # not FN_CONTACT_DETAILS,
    ]
    REQUIRED_INPATIENT = [
        FN_Q3A_UNIT_CLEAN,
        FN_Q3B_UNIT_NOT_GOOD_PLACE_TO_RECOVER,
        FN_Q3C_UNIT_DID_NOT_PROVIDE_ACTIVITIES,
        FN_Q3D_UNIT_GOOD_PLACE_FOR_BABY,
        FN_Q3E_UNIT_SUPPORTED_FAMILY_FRIENDS_CONTACT,
        FN_Q3F_FOOD_NOT_ACCEPTABLE,
    ]
    Q1_FIELDS = [
        FN_Q1A_MH_FIRST_CONTACT,
        FN_Q1B_MH_DISCHARGE,
    ]
    Q2_FIELDS = [
        FN_Q2A_STAFF_DID_NOT_COMMUNICATE,
        FN_Q2B_STAFF_GAVE_RIGHT_SUPPORT,
        FN_Q2C_HELP_NOT_QUICK_ENOUGH,
        FN_Q2D_STAFF_LISTENED,
        FN_Q2E_STAFF_DID_NOT_INVOLVE_ME,
        FN_Q2F_SERVICE_PROVIDED_INFO,
        FN_Q2G_STAFF_NOT_SENSITIVE_TO_ME,
        FN_Q2H_STAFF_HELPED_ME_UNDERSTAND,
        FN_Q2I_STAFF_NOT_SENSITIVE_TO_BABY,
        FN_Q2J_STAFF_HELPED_MY_CONFIDENCE,
        FN_Q2K_SERVICE_INVOLVED_OTHERS_HELPFULLY,
        FN_Q2L_I_WOULD_RECOMMEND_SERVICE,
    ]
    Q3_FIELDS = REQUIRED_INPATIENT

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Perinatal Patient-rated Outcome and Experience Measure")

    def was_inpatient(self) -> bool:
        return self.qb == self.VAL_QB_INPATIENT

    def respondent_not_patient(self) -> bool:
        return self.qa == self.VAL_QA_PARTNER_OTHER

    def offering_participation(self) -> bool:
        return self.future_participation == self.YES_INT

    def is_complete(self) -> bool:
        if self.any_fields_none(self.REQUIRED_ALWAYS):
            return False
        if (self.was_inpatient() and
                self.any_fields_none(self.REQUIRED_INPATIENT)):
            return False
        if not self.field_contents_valid():
            return False
        return True

    def get_qa_options(self, req: CamcopsRequest) -> List[str]:
        options = [self.wxstring(req, f"qa_a{o}") for o in range(
            self.VAL_QA_PATIENT,
            self.VAL_QA_PARTNER_OTHER + 1)]

        return options

    def get_qb_options(self, req: CamcopsRequest) -> List[str]:
        options = [self.wxstring(req, f"qb_a{o}") for o in range(
            self.VAL_QB_INPATIENT,
            self.VAL_QB_COMMUNITY + 1)]

        return options

    def get_q1_options(self, req: CamcopsRequest) -> List[str]:
        options = [self.wxstring(req, f"q1_a{o}") for o in range(
            self.VAL_Q1_VERY_WELL,
            self.VAL_Q1_EXTREMELY_UNWELL + 1)]

        return options

    def get_agree_options(self, req: CamcopsRequest) -> List[str]:
        options = [self.wxstring(req, f"agreement_a{o}") for o in range(
            self.VAL_STRONGLY_AGREE,
            self.VAL_STRONGLY_DISAGREE + 1)]

        return options

    def get_yn_options(self, req: CamcopsRequest) -> List[str]:
        return [req.sstring(SS.NO), req.sstring(SS.YES)]

    def get_task_html(self, req: CamcopsRequest) -> str:
        def loadvalues(_dict: Dict[int, str], _first: int, _last: int,
                       _xstringprefix: str) -> None:
            for val in range(_first, _last + 1):
                _dict[val] = (
                    f"{val} — {self.wxstring(req, f'{_xstringprefix}{val}')}"
                )

        respondent_dict = {}  # type: Dict[int, str]
        loadvalues(respondent_dict, self.VAL_QA_PATIENT,
                   self.VAL_QA_PARTNER_OTHER, "qa_a")
        service_dict = {}  # type: Dict[int, str]
        loadvalues(service_dict, self.VAL_QB_INPATIENT,
                   self.VAL_QB_COMMUNITY, "qb_a")
        mh_dict = {}  # type: Dict[int, str]
        loadvalues(mh_dict, self.VAL_Q1_VERY_WELL,
                   self.VAL_Q1_EXTREMELY_UNWELL, "q1_a")
        agree_dict = {}  # type: Dict[int, str]
        loadvalues(agree_dict, self.VAL_STRONGLY_AGREE,
                   self.VAL_STRONGLY_DISAGREE, "agreement_a")

        q_a_list = []  # type: List[str]

        def addqa(_fieldname: str, _valuedict: Dict[int, str]) -> None:
            xstringname = _fieldname + "_q"
            q_a_list.append(
                tr_qa(self.xstring(req, xstringname),  # not wxstring
                      get_from_dict(_valuedict, getattr(self, _fieldname)))
            )

        def subheading(_xstringname: str) -> None:
            q_a_list.append(subheading_spanning_two_columns(
                self.wxstring(req, _xstringname)))

        # Preamble
        addqa(self.FN_QA_RESPONDENT, respondent_dict)
        addqa(self.FN_QB_SERVICE_TYPE, service_dict)
        # The bulk
        subheading("q1_stem")
        for fieldname in self.Q1_FIELDS:
            addqa(fieldname, mh_dict)
        subheading("q2_stem")
        for fieldname in self.Q2_FIELDS:
            addqa(fieldname, agree_dict)
        if self.was_inpatient():
            subheading("q3_stem")
            for fieldname in self.Q3_FIELDS:
                addqa(fieldname, agree_dict)
        # General
        q_a_list.append(subheading_spanning_two_columns(
            req.sstring(SS.GENERAL)))
        q_a_list.append(tr_qa(
            self.wxstring(req, "general_comments_q"),
            self.general_comments
        ))
        q_a_list.append(tr_qa(
            self.wxstring(req, "participation_q"),
            get_yes_no_none(req, self.future_participation)
        ))
        if self.offering_participation():
            q_a_list.append(tr_qa(
                self.wxstring(req, "contact_details_q"),
                self.contact_details
            ))

        q_a = "\n".join(q_a_list)
        return f"""
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
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
            </div>
        """

    # No SNOMED codes for Perinatal-POEM.


# =============================================================================
# Reports
# =============================================================================

class PerinatalPoemReportSchema(ReportParamSchema):
    start_datetime = StartPendulumSelector()
    end_datetime = EndPendulumSelector()


class PerinatalPoemReport(Report):
    """
    Provides a summary of each question, x% of people said each response etc.
    Then a summary of the comments.
    """
    COL_Q = 0
    COL_TOTAL = 1
    COL_RESPONSE_OFFSET = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.task = PerinatalPoem()

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "perinatal_poem"

    @classmethod
    def title(cls, req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Perinatal-POEM — Question summaries")

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    @staticmethod
    def get_paramform_schema_class() -> Type[ReportParamSchema]:
        return PerinatalPoemReportSchema

    @classmethod
    def get_specific_http_query_keys(cls) -> List[str]:
        return [
            ViewParam.START_DATETIME,
            ViewParam.END_DATETIME,
        ]

    def get_response(self, req: "CamcopsRequest") -> Response:
        self.start_datetime = format_datetime(
            req.get_datetime_param(ViewParam.START_DATETIME),
            DateFormat.ERA
        )
        self.end_datetime = format_datetime(
            req.get_datetime_param(ViewParam.END_DATETIME),
            DateFormat.ERA
        )

        return super().get_response(req)

    def render_html(self, req: "CamcopsRequest") -> Response:
        cell_format = "{0:.1f}%"

        return render_to_response(
            "perinatal_poem_report.mako",
            dict(
                title=self.title(req),
                report_id=self.report_id,
                start_datetime=self.start_datetime,
                end_datetime=self.end_datetime,
                qa_q=self.task.xstring(req, "qa_q"),
                qa_column_headings=self._get_qa_column_headings(req),
                qa_rows=self._get_qa_rows(req, cell_format=cell_format),
                qb_q=self.task.xstring(req, "qb_q"),
                qb_column_headings=self._get_qb_column_headings(req),
                qb_rows=self._get_qb_rows(req, cell_format=cell_format),
                q1_stem=self.task.xstring(req, "q1_stem"),
                q1_column_headings=self._get_q1_column_headings(req),
                q1_rows=self._get_q1_rows(req, cell_format=cell_format),
                q2_stem=self.task.xstring(req, "q2_stem"),
                q2_column_headings=self._get_q2_column_headings(req),
                q2_rows=self._get_q2_rows(req, cell_format=cell_format),
                q3_stem=self.task.xstring(req, "q3_stem"),
                q3_column_headings=self._get_q3_column_headings(req),
                q3_rows=self._get_q3_rows(req, cell_format=cell_format),
                participation_q=self.task.xstring(req, "participation_q"),
                fp_column_headings=self._get_fp_column_headings(req),
                fp_rows=self._get_fp_rows(req),
                comment_rows=self._get_comment_rows(req)
            ),
            request=req
        )

    def get_tsv_pages(self, req: "CamcopsRequest") -> List[TsvPage]:
        _ = req.gettext

        qa_page = self.get_tsv_page(
            name=self.task.xstring(req, "qa_q"),
            column_names=self._get_qa_column_headings(req),
            rows=self._get_qa_rows(req)
        )

        qb_page = self.get_tsv_page(
            name=self.task.xstring(req, "qb_q"),
            column_names=self._get_qb_column_headings(req),
            rows=self._get_qb_rows(req)
        )

        q1_page = self.get_tsv_page(
            name=self.task.xstring(req, "q1_stem"),
            column_names=self._get_q1_column_headings(req),
            rows=self._get_q1_rows(req)
        )

        q2_page = self.get_tsv_page(
            name=self.task.xstring(req, "q2_stem"),
            column_names=self._get_q2_column_headings(req),
            rows=self._get_q2_rows(req)
        )

        q3_page = self.get_tsv_page(
            name=self.task.xstring(req, "q3_stem"),
            column_names=self._get_q3_column_headings(req),
            rows=self._get_q3_rows(req)
        )

        participation_page = self.get_tsv_page(
            name=self.task.xstring(req, "participation_q"),
            column_names=self._get_fp_column_headings(req),
            rows=self._get_fp_rows(req)
        )

        comments_page = self.get_tsv_page(
            name=_("Comments"),
            column_names=[_("Comment")],
            rows=self._get_comment_rows(req)
        )

        return [qa_page, qb_page, q1_page, q2_page, q3_page,
                participation_page, comments_page]

    def _get_qa_column_headings(self, req: "CamcopsRequest") -> List[str]:
        _ = req.gettext
        names = [_("Question"),
                 _("Total responses")] + self.task.get_qa_options(req)

        return names

    def _get_qa_rows(self, req: "CamcopsRequest",
                     cell_format: str="{}") -> List[List[str]]:
        """
        Percentage of people who answered x for each question
        """
        column_dict = {
            "qa": self.task.xstring(req, f"qa_q")
        }

        return self._get_response_percentages(
            req,
            column_dict=column_dict,
            num_answers=2,
            cell_format=cell_format
        )

    def _get_qb_column_headings(self, req: "CamcopsRequest") -> List[str]:
        _ = req.gettext
        names = [_("Question"),
                 _("Total responses")] + self.task.get_qb_options(req)

        return names

    def _get_qb_rows(self, req: "CamcopsRequest",
                     cell_format: str="{}") -> List[List[str]]:
        """
        Percentage of people who answered x for each question
        """
        column_dict = {
            "qb": self.task.xstring(req, f"qb_q")
        }

        return self._get_response_percentages(
            req,
            column_dict=column_dict,
            num_answers=2,
            cell_format=cell_format
        )

    def _get_q1_column_headings(self, req: "CamcopsRequest") -> List[str]:
        _ = req.gettext
        names = [_("Question"),
                 _("Total responses")] + self.task.get_q1_options(req)

        return names

    def _get_q1_rows(self, req: "CamcopsRequest",
                     cell_format: str="{}") -> List[List[str]]:
        """
        Percentage of people who answered x for each question
        """
        column_dict = {}

        for fieldname in PerinatalPoem.Q1_FIELDS:
            column_dict[fieldname] = self.task.xstring(
                req, f"{fieldname}_q")

        return self._get_response_percentages(
            req,
            column_dict=column_dict,
            num_answers=5,
            cell_format=cell_format
        )

    def _get_q2_column_headings(self, req: "CamcopsRequest") -> List[str]:
        _ = req.gettext
        names = [_("Question"),
                 _("Total responses")] + self.task.get_agree_options(req)

        return names

    def _get_q2_rows(self, req: "CamcopsRequest",
                     cell_format: str="{}") -> List[List[str]]:
        """
        Percentage of people who answered x for each question
        """
        column_dict = {}

        for fieldname in PerinatalPoem.Q2_FIELDS:
            column_dict[fieldname] = self.task.xstring(
                req, f"{fieldname}_q")

        return self._get_response_percentages(
            req,
            column_dict=column_dict,
            num_answers=4,
            cell_format=cell_format
        )

    def _get_q3_column_headings(self, req: "CamcopsRequest") -> List[str]:
        _ = req.gettext
        names = [_("Question"),
                 _("Total responses")] + self.task.get_agree_options(req)

        return names

    def _get_q3_rows(self, req: "CamcopsRequest",
                     cell_format: str="{}") -> List[List[str]]:
        """
        Percentage of people who answered x for each question
        """
        column_dict = {}

        for fieldname in PerinatalPoem.Q3_FIELDS:
            column_dict[fieldname] = self.task.xstring(
                req, f"{fieldname}_q")

        return self._get_response_percentages(
            req,
            column_dict=column_dict,
            num_answers=4,
            cell_format=cell_format
        )

    def _get_fp_column_headings(self, req: "CamcopsRequest") -> List[str]:
        _ = req.gettext
        names = [_("Question"),
                 _("Total responses")] + self.task.get_yn_options(req)

        return names

    def _get_fp_rows(self, req: "CamcopsRequest",
                     cell_format: str="{}") -> List[List[str]]:
        """
        Percentage of people who answered x for each question
        """
        column_dict = {
            "future_participation": self.task.xstring(
                req, "participation_q")
        }

        return self._get_response_percentages(
            req,
            column_dict=column_dict,
            num_answers=2,
            cell_format=cell_format
        )

    def _get_comment_rows(self, req: "CamcopsRequest") -> List[Tuple[str]]:
        """
        A list of all the additional comments
        """

        wheres = [
            column("general_comments").isnot(None)
        ]

        self._add_start_end_datetime_filters(wheres)

        # noinspection PyUnresolvedReferences
        query = (
            select([
                column("general_comments"),
            ])
            .select_from(self.task.__table__)
            .where(and_(*wheres))
        )

        comment_rows = []

        for result in req.dbsession.execute(query).fetchall():
            comment_rows.append(result)

        return comment_rows

    def _get_response_percentages(self,
                                  req: "CamcopsRequest",
                                  column_dict: Dict[str, str],
                                  num_answers: int,
                                  cell_format: str="{}") -> List[List[str]]:
        rows = []

        for column_name, question in column_dict.items():
            """
            SELECT COUNT(col) FROM perinatal_poem WHERE col IS NOT NULL
            """
            wheres = [
                column(column_name).isnot(None)
            ]

            self._add_start_end_datetime_filters(wheres)

            # noinspection PyUnresolvedReferences
            total_query = (
                select([func.count(column_name)])
                .select_from(PerinatalPoem.__table__)
                .where(and_(*wheres))
            )

            total_responses = req.dbsession.execute(total_query).fetchone()[0]

            row = [question] + [total_responses] + [""] * num_answers

            """
            SELECT total_responses,col, ((100 * COUNT(col)) / total_responses)
            FROM perinatal_poem WHERE col is not NULL
            GROUP BY col
            """
            # noinspection PyUnresolvedReferences
            query = (
                select([
                    column(column_name),
                    ((100 * func.count(column_name))/total_responses)
                ])
                .select_from(PerinatalPoem.__table__)
                .where(and_(*wheres))
                .group_by(column_name)
            )

            for result in req.dbsession.execute(query):
                row[result[0] + self.COL_RESPONSE_OFFSET] = cell_format.format(
                    result[1])

            rows.append(row)

        return rows

    def _add_start_end_datetime_filters(self, wheres: List[ColumnElement]):
        if self.start_datetime is not None:
            wheres.append(
                column("when_created") >= self.start_datetime
            )

        if self.end_datetime is not None:
            wheres.append(
                column("when_created") < self.end_datetime
            )


# =============================================================================
# Unit tests
# =============================================================================

class PerinatalPoemReportTests(DemoDatabaseTestCase):
    """
    Most of the base class tested in APEQCPFT Perinatal so just some basic
    sanity checking here
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id_sequence = self.get_id()

    def setUp(self) -> None:
        super().setUp()

        self.report = PerinatalPoemReport()

        # Really only needed for tests
        self.report.start_datetime = None
        self.report.end_datetime = None

    @staticmethod
    def get_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1

    def create_tasks(self):
        self._create_task(general_comments="comment 1")
        self._create_task(general_comments="comment 2")
        self._create_task(general_comments="comment 3")

        self.dbsession.commit()

    def _create_task(self, **kwargs) -> None:
        task = PerinatalPoem()
        self.apply_standard_task_fields(task)
        task.id = next(self.id_sequence)

        for name, value in kwargs.items():
            setattr(task, name, value)

        self.dbsession.add(task)

    def test_qa_rows_counts(self) -> None:
        rows = self.report._get_qa_rows(self.req)

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 4)

    def test_qb_rows_counts(self) -> None:
        rows = self.report._get_qb_rows(self.req)

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 4)

    def test_q1_rows_counts(self) -> None:
        rows = self.report._get_q1_rows(self.req)

        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), 7)

    def test_q2_rows_counts(self) -> None:
        rows = self.report._get_q2_rows(self.req)

        self.assertEqual(len(rows), 12)
        self.assertEqual(len(rows[0]), 6)

    def test_q3_rows_counts(self) -> None:
        rows = self.report._get_q3_rows(self.req)

        self.assertEqual(len(rows), 6)
        self.assertEqual(len(rows[0]), 6)

    def test_participation_rows_counts(self) -> None:
        rows = self.report._get_fp_rows(self.req)

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 4)

    def test_comments(self) -> None:
        expected_comments = [
            ("comment 1",), ("comment 2",), ("comment 3",),
        ]

        comments = self.report._get_comment_rows(self.req)

        self.assertEqual(comments, expected_comments)
