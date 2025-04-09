"""
camcops_server/tasks/demoquestionnaire.py

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

import datetime
from typing import Any, Optional, Type

from pendulum import DateTime as Pendulum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Float, Time, UnicodeText

from camcops_server.cc_modules.cc_blob import Blob, blob_relationship
from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    mapped_camcops_column,
    PendulumDateTimeAsIsoTextColType,
    DiagnosticCodeColType,
)
from camcops_server.cc_modules.cc_task import Task


# =============================================================================
# TASKS: DEMO QUESTIONNAIRE
# =============================================================================

N_MCQ = 10  # 8 in v1; 10 in v2
N_MCQBOOL = 3
N_MULTIPLERESPONSE = 6
N_BOOLTEXT = 22
N_BOOLIMAGE = 2
N_PICKER = 2
N_SLIDER = 2


def divtest(divname: str) -> str:
    return f'<div class="{divname}">.{divname}</div>\n'


class DemoQuestionnaire(
    Task,
):
    """
    Server implementation of the demo questionnaire task.
    """

    __tablename__ = "demoquestionnaire"
    shortname = "Demo"
    is_anonymous = True  # type: ignore[assignment]

    @classmethod
    def extend_columns(cls: Type["DemoQuestionnaire"], **kwargs: Any) -> None:
        add_multiple_columns(cls, "mcq", 1, N_MCQ)
        add_multiple_columns(cls, "mcqbool", 1, N_MCQBOOL)
        add_multiple_columns(cls, "multipleresponse", 1, N_MULTIPLERESPONSE)
        add_multiple_columns(cls, "booltext", 1, N_BOOLTEXT)
        add_multiple_columns(cls, "boolimage", 1, N_BOOLIMAGE)
        add_multiple_columns(cls, "picker", 1, N_PICKER)
        add_multiple_columns(cls, "slider", 1, N_SLIDER, Float)

    mcqtext_1a: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mcqtext_1b: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mcqtext_2a: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mcqtext_2b: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mcqtext_3a: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mcqtext_3b: Mapped[Optional[str]] = mapped_column(UnicodeText)
    typedvar_text: Mapped[Optional[str]] = mapped_column(UnicodeText)
    typedvar_text_multiline: Mapped[Optional[str]] = mapped_column(UnicodeText)
    typedvar_text_rich: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )  # v2
    typedvar_int: Mapped[Optional[int]] = mapped_column()
    typedvar_real: Mapped[Optional[float]] = mapped_column()
    date_only: Mapped[Optional[datetime.date]] = mapped_column()
    date_time: Mapped[Optional[Pendulum]] = mapped_column(
        PendulumDateTimeAsIsoTextColType
    )
    thermometer: Mapped[Optional[int]] = mapped_column()
    diagnosticcode_code: Mapped[Optional[str]] = mapped_column(
        DiagnosticCodeColType
    )
    diagnosticcode_description: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText,
        exempt_from_anonymisation=True,
    )
    diagnosticcode2_code: Mapped[Optional[str]] = mapped_column(
        DiagnosticCodeColType
    )  # v2
    diagnosticcode2_description: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText,
        exempt_from_anonymisation=True,
    )  # v2
    photo_blobid: Mapped[Optional[int]] = mapped_camcops_column(
        is_blob_id_field=True,
        blob_relationship_attr_name="photo",
    )
    # IGNORED. REMOVE WHEN ALL PRE-2.0.0 TABLETS GONE:
    photo_rotation: Mapped[Optional[int]] = (
        mapped_column()
    )  # DEFUNCT as of v2.0.0
    canvas_blobid: Mapped[Optional[int]] = mapped_camcops_column(
        is_blob_id_field=True,
        blob_relationship_attr_name="canvas",
    )
    canvas2_blobid: Mapped[Optional[int]] = mapped_camcops_column(
        is_blob_id_field=True,
        blob_relationship_attr_name="canvas2",
    )
    spinbox_int: Mapped[Optional[int]] = mapped_column()  # v2
    spinbox_real: Mapped[Optional[float]] = mapped_column()  # v2
    time_only: Mapped[Optional[datetime.time]] = mapped_column(
        "time_only", Time
    )  # v2

    photo = blob_relationship(  # type: ignore[assignment]
        "DemoQuestionnaire", "photo_blobid"
    )  # type: Optional[Blob]
    canvas = blob_relationship(  # type: ignore[assignment]
        "DemoQuestionnaire", "canvas_blobid"
    )  # type: Optional[Blob]
    canvas2 = blob_relationship(  # type: ignore[assignment]
        "DemoQuestionnaire", "canvas2_blobid"
    )  # type: Optional[Blob]

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Demonstration Questionnaire")

    # noinspection PyMethodOverriding
    @staticmethod
    def is_complete() -> bool:
        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        h = f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                This is a demo questionnaire, containing no genuine
                information.
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        for i in range(1, N_MCQ + 1):
            h += self.get_twocol_val_row("mcq" + str(i))
        for i in range(1, N_MCQBOOL + 1):
            h += self.get_twocol_bool_row(req, "mcqbool" + str(i))
        for i in range(1, N_MULTIPLERESPONSE + 1):
            h += self.get_twocol_bool_row(req, "multipleresponse" + str(i))
        for i in range(1, N_BOOLTEXT + 1):
            h += self.get_twocol_bool_row(req, "booltext" + str(i))
        for i in range(1, N_BOOLIMAGE + 1):
            h += self.get_twocol_bool_row(req, "boolimage" + str(i))
        for i in range(1, N_PICKER + 1):
            h += self.get_twocol_val_row("picker" + str(i))
        for i in range(1, N_SLIDER + 1):
            h += self.get_twocol_val_row("slider" + str(i))
        h += self.get_twocol_string_row("mcqtext_1a")
        h += self.get_twocol_string_row("mcqtext_1b")
        h += self.get_twocol_string_row("mcqtext_2a")
        h += self.get_twocol_string_row("mcqtext_2b")
        h += self.get_twocol_string_row("mcqtext_3a")
        h += self.get_twocol_string_row("mcqtext_3b")
        h += self.get_twocol_string_row("typedvar_text")
        h += self.get_twocol_string_row("typedvar_text_multiline")
        h += self.get_twocol_string_row("typedvar_text_rich")
        h += self.get_twocol_val_row("typedvar_int")
        h += self.get_twocol_val_row("typedvar_real")
        h += self.get_twocol_val_row("date_only")
        h += self.get_twocol_val_row("date_time")
        h += self.get_twocol_val_row("thermometer")
        h += self.get_twocol_string_row("diagnosticcode_code")
        h += self.get_twocol_string_row("diagnosticcode_description")
        h += self.get_twocol_string_row("diagnosticcode2_code")
        h += self.get_twocol_string_row("diagnosticcode2_description")
        # noinspection PyTypeChecker
        h += self.get_twocol_picture_row(self.photo, "photo")
        # noinspection PyTypeChecker
        h += self.get_twocol_picture_row(self.canvas, "canvas")
        # noinspection PyTypeChecker
        h += self.get_twocol_picture_row(self.canvas2, "canvas2")
        h += (
            """
            </table>

            <div>
                In addition to the data (above), this task demonstrates
                HTML/CSS styles used in the CamCOPS views.
            </div>

            <h1>Header 1</h1>
            <h2>Header 2</h2>
            <h3>Header 3</h3>

            <div>
                Plain div with <sup>superscript</sup> and <sub>subscript</sub>.
                <br>
                Answers look like this: """
            + answer("Answer")
            + """<br>
                Missing answers look liks this: """
            + answer(None)
            + """<br>
            </div>
        """
        )
        h += divtest(CssClass.BAD_ID_POLICY_MILD)
        h += divtest(CssClass.BAD_ID_POLICY_SEVERE)
        h += divtest(CssClass.CLINICIAN)
        h += divtest(CssClass.COPYRIGHT)
        h += divtest(CssClass.ERROR)
        h += divtest(CssClass.EXPLANATION)
        h += divtest(CssClass.FOOTNOTES)
        h += divtest(CssClass.FORMTITLE)
        h += divtest(CssClass.GREEN)
        h += divtest(CssClass.HEADING)
        h += divtest(CssClass.IMPORTANT)
        h += divtest(CssClass.INCOMPLETE)
        h += divtest(CssClass.INDENTED)
        h += divtest(CssClass.LIVE_ON_TABLET)
        h += divtest(CssClass.NAVIGATION)
        h += divtest(CssClass.OFFICE)
        h += divtest(CssClass.PATIENT)
        h += divtest(CssClass.RESPONDENT)
        h += divtest(CssClass.SMALLPRINT)
        h += divtest(CssClass.SPECIALNOTE)
        h += divtest(CssClass.SUBHEADING)
        h += divtest(CssClass.SUBSUBHEADING)
        h += divtest(CssClass.SUMMARY)
        h += divtest(CssClass.SUPERUSER)
        h += divtest(CssClass.TASKHEADER)
        h += divtest(CssClass.TRACKERHEADER)
        h += divtest(CssClass.TRACKER_ALL_CONSISTENT)
        h += divtest(CssClass.WARNING)
        h += """
            <table>
                <tr>
                    <th>Standard table heading; column 1</th><th>Column 2</th>
                </tr>
                <tr>
                    <td>Standard table row; column 1</td><td>Column 2</td>
                </tr>
            </table>

            <div>Inlined <code>code looks like this</code>.

            <div>There are some others, too.</div>
        """
        return h
