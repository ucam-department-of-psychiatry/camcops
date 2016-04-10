#!/usr/bin/env python3
# demoquestionnaire.py

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

from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import (
    answer,
)
from cc_modules.cc_task import Task


# =============================================================================
# TASKS: DEMO QUESTIONNAIRE
# =============================================================================

N_MCQ = 8
N_MCQBOOL = 3
N_MULTIPLERESPONSE = 6
N_BOOLTEXT = 22
N_BOOLIMAGE = 2
N_PICKER = 2
N_SLIDER = 2


def divtest(divname):
    return '<div class="{d}">.{d}</div>\n'.format(d=divname)


class DemoQuestionnaire(Task):
    tablename = "demoquestionnaire"
    shortname = "Demo"
    longname = "Demonstration Questionnaire"
    fieldspecs = (
        repeat_fieldspec("mcq", 1, N_MCQ) +
        repeat_fieldspec("mcqbool", 1, N_MCQBOOL) +
        repeat_fieldspec("multipleresponse", 1, N_MULTIPLERESPONSE) +
        repeat_fieldspec("booltext", 1, N_BOOLTEXT) +
        repeat_fieldspec("boolimage", 1, N_BOOLIMAGE) +
        repeat_fieldspec("picker", 1, N_PICKER) +
        repeat_fieldspec("slider", 1, N_SLIDER, "FLOAT") +
        [
            dict(name="mcqtext_1a", cctype="TEXT"),
            dict(name="mcqtext_1b", cctype="TEXT"),
            dict(name="mcqtext_2a", cctype="TEXT"),
            dict(name="mcqtext_2b", cctype="TEXT"),
            dict(name="mcqtext_3a", cctype="TEXT"),
            dict(name="mcqtext_3b", cctype="TEXT"),
            dict(name="typedvar_text", cctype="TEXT"),
            dict(name="typedvar_text_multiline", cctype="TEXT"),
            dict(name="typedvar_int", cctype="INT"),
            dict(name="typedvar_real", cctype="FLOAT"),
            dict(name="date_only", cctype="ISO8601"),
            dict(name="date_time", cctype="ISO8601"),
            dict(name="thermometer", cctype="INT"),
            dict(name="diagnosticcode_code", cctype="TEXT"),
            dict(name="diagnosticcode_description", cctype="TEXT"),
            dict(name="photo_blobid", cctype="INT"),
            dict(name="photo_rotation", cctype="INT"),
            dict(name="canvas_blobid", cctype="INT"),
        ]
    )
    for d in fieldspecs:
        if "comment" not in d:
            d["comment"] = d["name"]
    is_anonymous = True
    pngblob_name_idfield_rotationfield_list = [
        ("photo", "photo_blobid", "photo_rotation"),
        ("canvas", "canvas_blobid", None),
    ]

    @staticmethod
    def is_complete():
        return True

    def get_task_html(self):
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <div class="explanation">
                This is a demo questionnaire, containing no genuine
                information.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
        )
        for i in range(1, N_MCQ + 1):
            h += self.get_twocol_val_row("mcq" + str(i))
        for i in range(1, N_MCQBOOL + 1):
            h += self.get_twocol_bool_row("mcqbool" + str(i))
        for i in range(1, N_MULTIPLERESPONSE + 1):
            h += self.get_twocol_bool_row("multipleresponse" + str(i))
        for i in range(1, N_BOOLTEXT + 1):
            h += self.get_twocol_bool_row("booltext" + str(i))
        for i in range(1, N_BOOLIMAGE + 1):
            h += self.get_twocol_bool_row("boolimage" + str(i))
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
        h += self.get_twocol_val_row("typedvar_int")
        h += self.get_twocol_val_row("typedvar_real")
        h += self.get_twocol_val_row("date_only")
        h += self.get_twocol_val_row("date_time")
        h += self.get_twocol_val_row("thermometer")
        h += self.get_twocol_string_row("diagnosticcode_code")
        h += self.get_twocol_string_row("diagnosticcode_description")
        h += self.get_twocol_picture_row("photo_blobid",
                                         rotationfieldname="photo_rotation")
        h += self.get_twocol_picture_row("canvas_blobid",
                                         rotationfieldname=None)
        h += """
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
                Answers look like this: """ + answer("Answer") + """<br>
                Missing answers look liks this: """ + answer(None) + """<br>
            </div>
        """
        h += divtest("badidpolicy_mild")
        h += divtest("badidpolicy_severe")
        h += divtest("clinician")
        h += divtest("copyright")
        h += divtest("error")
        h += divtest("explanation")
        h += divtest("footnotes")
        h += divtest("formtitle")
        h += divtest("green")
        h += divtest("heading")
        h += divtest("important")
        h += divtest("incomplete")
        h += divtest("indented")
        h += divtest("live_on_tablet")
        h += divtest("navigation")
        h += divtest("office")
        h += divtest("patient")
        h += divtest("respondent")
        h += divtest("smallprint")
        h += divtest("specialnote")
        h += divtest("subheading")
        h += divtest("summary")
        h += divtest("superuser")
        h += divtest("taskheader")
        h += divtest("trackerheader")
        h += divtest("tracker_all_consistent")
        h += divtest("warning")
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
