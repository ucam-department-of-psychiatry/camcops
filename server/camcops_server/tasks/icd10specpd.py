#!/usr/bin/env python
# camcops_server/tasks/icd10specpd.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import List, Optional

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_dt import format_datetime_string
from ..cc_modules.cc_constants import (
    DATEFORMAT,
    ICD10_COPYRIGHT_DIV,
    PV,
)
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    get_yes_no_unknown,
    subheading_spanning_two_columns,
    tr_qa,
)
from ..cc_modules.cc_lang import is_false
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task


# =============================================================================
# Icd10SpecPD
# =============================================================================

def ctv_info_pd(condition: str, has_it: Optional[bool]) -> CtvInfo:
    return CtvInfo(content=condition + ": " + get_yes_no_unknown(has_it))


class Icd10SpecPD(Task):
    N_GENERAL = 6
    N_GENERAL_1 = 4
    N_PARANOID = 7
    N_SCHIZOID = 9
    N_DISSOCIAL = 6
    N_EU = 10
    N_EUPD_I = 5
    N_HISTRIONIC = 6
    N_ANANKASTIC = 8
    N_ANXIOUS = 5
    N_DEPENDENT = 6

    tablename = "icd10specpd"
    shortname = "ICD10-PD"
    longname = "ICD-10 criteria for specific personality disorders (F60)"
    fieldspecs = (
        [
            dict(name="date_pertains_to", cctype="ISO8601",
                 comment="Date the assessment pertains to"),
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
            dict(name="skip_paranoid", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for paranoid PD?"),
            dict(name="skip_schizoid", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for schizoid PD?"),
            dict(name="skip_dissocial", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for dissocial PD?"),
            dict(name="skip_eu", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for emotionally unstable PD?"),
            dict(name="skip_histrionic", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for histrionic PD?"),
            dict(name="skip_anankastic", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for anankastic PD?"),
            dict(name="skip_anxious", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for anxious PD?"),
            dict(name="skip_dependent", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for dependent PD?"),
            dict(name="other_pd_present", cctype="BOOL", pv=PV.BIT,
                 comment="Is another personality disorder present?"),
            dict(name="vignette", cctype="TEXT",
                 comment="Vignette"),
        ] +
        repeat_fieldspec(
            "g", 1, N_GENERAL, "BOOL", pv=PV.BIT,
            comment_fmt="G{n}: {s}",
            comment_strings=["pathological 1", "pervasive",
                             "pathological 2", "persistent",
                             "primary 1", "primary 2"]) +
        repeat_fieldspec(
            "g1_", 1, N_GENERAL_1, "BOOL", pv=PV.BIT,
            comment_fmt="G1{n}: {s}",
            comment_strings=["cognition", "affectivity",
                             "impulse control", "interpersonal"]) +
        repeat_fieldspec(
            "paranoid", 1, N_PARANOID, "BOOL", pv=PV.BIT,
            comment_fmt="Paranoid ({n}): {s}",
            comment_strings=["sensitive", "grudges", "suspicious",
                             "personal rights", "sexual jealousy",
                             "self-referential", "conspiratorial"]) +
        repeat_fieldspec(
            "schizoid", 1, N_SCHIZOID, "BOOL", pv=PV.BIT,
            comment_fmt="Schizoid ({n}): {s}",
            comment_strings=["little pleasure",
                             "cold/detached",
                             "limited capacity for warmth",
                             "indifferent to praise/criticism",
                             "little interest in sex",
                             "solitary",
                             "fantasy/introspection",
                             "0/1 close friends/confidants",
                             "insensitive to social norms"]) +
        repeat_fieldspec(
            "dissocial", 1, N_DISSOCIAL, "BOOL", pv=PV.BIT,
            comment_fmt="Dissocial ({n}): {s}",
            comment_strings=["unconcern", "irresponsibility",
                             "incapacity to maintain relationships",
                             "low tolerance to frustration",
                             "incapacity for guilt",
                             "prone to blame others"]) +
        repeat_fieldspec(
            "eu", 1, N_EU, "BOOL", pv=PV.BIT,
            comment_fmt="Emotionally unstable ({n}): {s}",
            comment_strings=["act without considering consequences",
                             "quarrelsome", "outbursts of anger",
                             "can't maintain actions with immediate reward",
                             "unstable/capricious mood",
                             "uncertain self-image",
                             "intense/unstable relationships",
                             "avoids abandonment",
                             "threats/acts of self-harm",
                             "feelings of emptiness"]) +
        repeat_fieldspec(
            "histrionic", 1, N_HISTRIONIC, "BOOL", pv=PV.BIT,
            comment_fmt="Histrionic ({n}): {s}",
            comment_strings=["theatricality",
                             "suggestibility",
                             "shallow/labile affect",
                             "centre of attention",
                             "inappropriately seductive",
                             "concerned with attractivness"]) +
        repeat_fieldspec(
            "anankastic", 1, N_ANANKASTIC, "BOOL", pv=PV.BIT,
            comment_fmt="Anankastic ({n}): {s}",
            comment_strings=["doubt/caution",
                             "preoccupation with details",
                             "perfectionism",
                             "excessively conscientious",
                             "preoccupied with productivity",
                             "excessive pedantry",
                             "rigid/stubborn",
                             "require others do things specific way"]) +
        repeat_fieldspec(
            "anxious", 1, N_ANXIOUS, "BOOL", pv=PV.BIT,
            comment_fmt="Anxious ({n}), {s}",
            comment_strings=["tension/apprehension",
                             "preoccupied with criticism/rejection",
                             "won't get involved unless certain liked",
                             "need for security restricts lifestyle",
                             "avoidance of interpersonal contact"]) +
        repeat_fieldspec(
            "dependent", 1, N_DEPENDENT, "BOOL", pv=PV.BIT,
            comment_fmt="Dependent ({n}): {s}",
            comment_strings=["others decide",
                             "subordinate needs to those of others",
                             "unwilling to make reasonable demands",
                             "uncomfortable/helpless when alone",
                             "fears of being left to oneself",
                             "everyday decisions require advice/reassurance"])
    )
    has_clinician = True

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        infolist = [ctv_info_pd(self.wxstring("meets_general_criteria"),
                                self.has_pd()),
                    ctv_info_pd(self.wxstring("paranoid_pd_title"),
                                self.has_paranoid_pd()),
                    ctv_info_pd(self.wxstring("schizoid_pd_title"),
                                self.has_schizoid_pd()),
                    ctv_info_pd(self.wxstring("dissocial_pd_title"),
                                self.has_dissocial_pd()),
                    ctv_info_pd(self.wxstring("eu_pd_i_title"),
                                self.has_eupd_i()),
                    ctv_info_pd(self.wxstring("eu_pd_b_title"),
                                self.has_eupd_b()),
                    ctv_info_pd(self.wxstring("histrionic_pd_title"),
                                self.has_histrionic_pd()),
                    ctv_info_pd(self.wxstring("anankastic_pd_title"),
                                self.has_anankastic_pd()),
                    ctv_info_pd(self.wxstring("anxious_pd_title"),
                                self.has_anxious_pd()),
                    ctv_info_pd(self.wxstring("dependent_pd_title"),
                                self.has_dependent_pd())]
        return infolist

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="meets_general_criteria", cctype="BOOL",
                 value=self.has_pd(),
                 comment="Meets general criteria for personality disorder?"),
            dict(name="paranoid_pd", cctype="BOOL",
                 value=self.has_paranoid_pd(),
                 comment="Meets criteria for paranoid PD?"),
            dict(name="schizoid_pd", cctype="BOOL",
                 value=self.has_schizoid_pd(),
                 comment="Meets criteria for schizoid PD?"),
            dict(name="dissocial_pd", cctype="BOOL",
                 value=self.has_dissocial_pd(),
                 comment="Meets criteria for dissocial PD?"),
            dict(name="eupd_i", cctype="BOOL",
                 value=self.has_eupd_i(),
                 comment="Meets criteria for EUPD (impulsive type)?"),
            dict(name="eupd_b", cctype="BOOL",
                 value=self.has_eupd_b(),
                 comment="Meets criteria for EUPD (borderline type)?"),
            dict(name="histrionic_pd", cctype="BOOL",
                 value=self.has_histrionic_pd(),
                 comment="Meets criteria for histrionic PD?"),
            dict(name="anankastic_pd", cctype="BOOL",
                 value=self.has_anankastic_pd(),
                 comment="Meets criteria for anankastic PD?"),
            dict(name="anxious_pd", cctype="BOOL",
                 value=self.has_anxious_pd(),
                 comment="Meets criteria for anxious PD?"),
            dict(name="dependent_pd", cctype="BOOL",
                 value=self.has_dependent_pd(),
                 comment="Meets criteria for dependent PD?"),
        ]

    def is_pd_excluded(self) -> bool:
        return (
            is_false(self.g1) or
            is_false(self.g2) or
            is_false(self.g3) or
            is_false(self.g4) or
            is_false(self.g5) or
            is_false(self.g6) or
            (
                self.are_all_fields_complete(
                    repeat_fieldname("g1_", 1, Icd10SpecPD.N_GENERAL_1)) and
                self.count_booleans(
                    repeat_fieldname("g1_", 1, Icd10SpecPD.N_GENERAL_1)) <= 1
            )
        )

    def is_complete_general(self) -> bool:
        return (
            self.are_all_fields_complete(
                repeat_fieldname("g", 1, Icd10SpecPD.N_GENERAL)) and
            self.are_all_fields_complete(
                repeat_fieldname("g1_", 1, Icd10SpecPD.N_GENERAL_1))
        )

    def is_complete_paranoid(self) -> bool:
        return self.are_all_fields_complete(
            repeat_fieldname("paranoid", 1, Icd10SpecPD.N_PARANOID))

    def is_complete_schizoid(self) -> bool:
        return self.are_all_fields_complete(
            repeat_fieldname("schizoid", 1, Icd10SpecPD.N_SCHIZOID))

    def is_complete_dissocial(self) -> bool:
        return self.are_all_fields_complete(
            repeat_fieldname("dissocial", 1, Icd10SpecPD.N_DISSOCIAL))

    def is_complete_eu(self) -> bool:
        return self.are_all_fields_complete(
            repeat_fieldname("eu", 1, Icd10SpecPD.N_EU))

    def is_complete_histrionic(self) -> bool:
        return self.are_all_fields_complete(
            repeat_fieldname("histrionic", 1, Icd10SpecPD.N_HISTRIONIC))

    def is_complete_anankastic(self) -> bool:
        return self.are_all_fields_complete(
            repeat_fieldname("anankastic", 1, Icd10SpecPD.N_ANANKASTIC))

    def is_complete_anxious(self) -> bool:
        return self.are_all_fields_complete(
            repeat_fieldname("anxious", 1, Icd10SpecPD.N_ANXIOUS))

    def is_complete_dependent(self) -> bool:
        return self.are_all_fields_complete(
            repeat_fieldname("dependent", 1, Icd10SpecPD.N_DEPENDENT))

    # Meets criteria? These also return null for unknown.
    def has_pd(self) -> Optional[bool]:
        if self.is_pd_excluded():
            return False
        if not self.is_complete_general():
            return None
        return (
            self.all_true(repeat_fieldname("g", 1, Icd10SpecPD.N_GENERAL)) and
            self.count_booleans(
                repeat_fieldname("g1_", 1, Icd10SpecPD.N_GENERAL_1)) > 1
        )

    def has_paranoid_pd(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_paranoid():
            return None
        return (self.count_booleans(
            repeat_fieldname("paranoid", 1, Icd10SpecPD.N_PARANOID)) >= 4)

    def has_schizoid_pd(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_schizoid():
            return None
        return (self.count_booleans(
            repeat_fieldname("schizoid", 1, Icd10SpecPD.N_SCHIZOID)) >= 4)

    def has_dissocial_pd(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_dissocial():
            return None
        return (self.count_booleans(
            repeat_fieldname("dissocial", 1, Icd10SpecPD.N_DISSOCIAL)) >= 3)

    def has_eupd_i(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_eu():
            return None
        return (
            self.count_booleans(
                repeat_fieldname("eu", 1, Icd10SpecPD.N_EUPD_I)) >= 3 and
            self.eu2
        )

    def has_eupd_b(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_eu():
            return None
        return (
            self.count_booleans(
                repeat_fieldname("eu", 1, Icd10SpecPD.N_EUPD_I)) >= 3 and
            self.count_booleans(
                repeat_fieldname("eu",
                                 Icd10SpecPD.N_EUPD_I + 1,
                                 Icd10SpecPD.N_EU)) >= 2
        )

    def has_histrionic_pd(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_histrionic():
            return None
        return (self.count_booleans(
            repeat_fieldname("histrionic", 1, Icd10SpecPD.N_HISTRIONIC)) >= 4)

    def has_anankastic_pd(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_anankastic():
            return None
        return (self.count_booleans(
            repeat_fieldname("anankastic", 1, Icd10SpecPD.N_ANANKASTIC)) >= 4)

    def has_anxious_pd(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_anxious():
            return None
        return (self.count_booleans(
            repeat_fieldname("anxious", 1, Icd10SpecPD.N_ANXIOUS)) >= 4)

    def has_dependent_pd(self) -> Optional[bool]:
        if not self.has_pd():
            return self.has_pd()
        if not self.is_complete_dependent():
            return None
        return (self.count_booleans(
            repeat_fieldname("dependent", 1, Icd10SpecPD.N_DEPENDENT)) >= 4)

    def is_complete(self) -> bool:
        return (
            self.date_pertains_to is not None and (
                self.is_pd_excluded() or (
                    self.is_complete_general() and
                    (self.skip_paranoid or self.is_complete_paranoid()) and
                    (self.skip_schizoid or self.is_complete_schizoid()) and
                    (self.skip_dissocial or self.is_complete_dissocial()) and
                    (self.skip_eu or self.is_complete_eu()) and
                    (self.skip_histrionic or self.is_complete_histrionic()) and
                    (self.skip_anankastic or self.is_complete_anankastic()) and
                    (self.skip_anxious or self.is_complete_anxious()) and
                    (self.skip_dependent or self.is_complete_dependent())
                )
            ) and
            self.field_contents_valid()
        )

    def pd_heading(self, wstringname: str) -> str:
        return """
            <tr class="heading"><td colspan="2">{}</td></tr>
        """.format(self.wxstring(wstringname))

    def pd_skiprow(self, stem: str) -> str:
        return self.get_twocol_bool_row("skip_" + stem,
                                        label=self.wxstring("skip_this_pd"))

    def pd_subheading(self, wstringname: str) -> str:
        return """
            <tr class="subheading"><td colspan="2">{}</td></tr>
        """.format(self.wxstring(wstringname))

    def pd_general_criteria_bits(self) -> str:
        return """
            <tr><td>{}</td><td><i><b>{}</b></i></td></tr>
        """.format(
            self.wxstring("general_criteria_must_be_met"),
            get_yes_no_unknown(self.has_pd())
        )

    def pd_b_text(self, wstringname: str) -> str:
        return """
            <tr><td>{}</td><td class="subheading"></td></tr>
        """.format(self.wxstring(wstringname))

    def pd_basic_row(self, stem: str, i: int) -> str:
        return self.get_twocol_bool_row_true_false(
            stem + str(i), self.wxstring(stem + str(i)))

    def standard_pd_html(self, stem: str, n: int) -> str:
        html = self.pd_heading(stem + "_pd_title")
        html += self.pd_skiprow(stem)
        html += self.pd_general_criteria_bits()
        html += self.pd_b_text(stem + "_pd_B")
        for i in range(1, n + 1):
            html += self.pd_basic_row(stem, i)
        return html

    def get_task_html(self) -> str:
        h = self.get_standard_clinician_comments_block(self.comments) + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa(wappstring("date_pertains_to"),
                   format_datetime_string(self.date_pertains_to,
                                          DATEFORMAT.LONG_DATE, default=None))
        h += tr_qa(self.wxstring("meets_general_criteria"),
                   get_yes_no_none(self.has_pd()))
        h += tr_qa(self.wxstring("paranoid_pd_title"),
                   get_yes_no_none(self.has_paranoid_pd()))
        h += tr_qa(self.wxstring("schizoid_pd_title"),
                   get_yes_no_none(self.has_schizoid_pd()))
        h += tr_qa(self.wxstring("dissocial_pd_title"),
                   get_yes_no_none(self.has_dissocial_pd()))
        h += tr_qa(self.wxstring("eu_pd_i_title"),
                   get_yes_no_none(self.has_eupd_i()))
        h += tr_qa(self.wxstring("eu_pd_b_title"),
                   get_yes_no_none(self.has_eupd_b()))
        h += tr_qa(self.wxstring("histrionic_pd_title"),
                   get_yes_no_none(self.has_histrionic_pd()))
        h += tr_qa(self.wxstring("anankastic_pd_title"),
                   get_yes_no_none(self.has_anankastic_pd()))
        h += tr_qa(self.wxstring("anxious_pd_title"),
                   get_yes_no_none(self.has_anxious_pd()))
        h += tr_qa(self.wxstring("dependent_pd_title"),
                   get_yes_no_none(self.has_dependent_pd()))

        h += """
                </table>
            </div>
            <div>
                <p><i>Vignette:</i></p>
                <p>{}</p>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """.format(
            answer(ws.webify(self.vignette), default_for_blank_strings=True)
        )

        # General
        h += subheading_spanning_two_columns(self.wxstring("general"))
        h += self.get_twocol_bool_row_true_false("g1", self.wxstring("G1"))
        h += self.pd_b_text("G1b")
        for i in range(1, Icd10SpecPD.N_GENERAL_1 + 1):
            h += self.get_twocol_bool_row_true_false(
                "g1_" + str(i), self.wxstring("G1_" + str(i)))
        for i in range(2, Icd10SpecPD.N_GENERAL + 1):
            h += self.get_twocol_bool_row_true_false(
                "g" + str(i), self.wxstring("G" + str(i)))

        # Paranoid, etc.
        h += self.standard_pd_html("paranoid", Icd10SpecPD.N_PARANOID)
        h += self.standard_pd_html("schizoid", Icd10SpecPD.N_SCHIZOID)
        h += self.standard_pd_html("dissocial", Icd10SpecPD.N_DISSOCIAL)

        # EUPD is special
        h += self.pd_heading("eu_pd_title")
        h += self.pd_skiprow("eu")
        h += self.pd_general_criteria_bits()
        h += self.pd_subheading("eu_pd_i_title")
        h += self.pd_b_text("eu_pd_i_B")
        for i in range(1, Icd10SpecPD.N_EUPD_I + 1):
            h += self.pd_basic_row("eu", i)
        h += self.pd_subheading("eu_pd_b_title")
        h += self.pd_b_text("eu_pd_b_B")
        for i in range(Icd10SpecPD.N_EUPD_I + 1, Icd10SpecPD.N_EU + 1):
            h += self.pd_basic_row("eu", i)

        # Back to plain ones
        h += self.standard_pd_html("histrionic", Icd10SpecPD.N_HISTRIONIC)
        h += self.standard_pd_html("anankastic", Icd10SpecPD.N_ANANKASTIC)
        h += self.standard_pd_html("anxious", Icd10SpecPD.N_ANXIOUS)
        h += self.standard_pd_html("dependent", Icd10SpecPD.N_DEPENDENT)

        # Done
        h += """
            </table>
        """ + ICD10_COPYRIGHT_DIV
        return h
