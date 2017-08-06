#!/usr/bin/env python
# camcops_server/tasks/icd10manic.py

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

from cardinal_pythonlib.typetests import is_false
import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.sql.sqltypes import Boolean

from ..cc_modules.cc_dt import format_datetime_string
from ..cc_modules.cc_constants import (
    DATEFORMAT,
    ICD10_COPYRIGHT_DIV,
    PV,
)
from ..cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from ..cc_modules.cc_html import (
    get_present_absent_none,
    heading_spanning_two_columns,
    subheading_spanning_two_columns,
    tr_qa,
)
from ..cc_modules.cc_sqla_coltypes import SummaryCategoryColType
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import Task


# =============================================================================
# Icd10Manic
# =============================================================================

class Icd10Manic(Task):
    tablename = "icd10manic"
    shortname = "ICD10-MANIC"
    longname = (
        "ICD-10 symptomatic criteria for a manic/hypomanic episode "
        "(as in e.g. F06.3, F25, F30, F31)"
    )
    has_clinician = True

    CORE_FIELDSPECS = [
        dict(name="mood_elevated", cctype="BOOL", pv=PV.BIT,
             comment="The mood is 'elevated' [hypomania] or 'predominantly "
             "elevated [or] expansive' [mania] to a degree that is definitely "
             "abnormal for the individual concerned."),
        dict(name="mood_irritable", cctype="BOOL", pv=PV.BIT,
             comment="The mood is 'irritable' [hypomania] or 'predominantly "
             "irritable' [mania] to a degree that is definitely abnormal for "
             "the individual concerned."),
    ]
    HYPOMANIA_MANIA_FIELDSPECS = [
        dict(name="distractible", cctype="BOOL", pv=PV.BIT,
             comment="Difficulty in concentration or distractibility [from "
             "the criteria for hypomania]; distractibility or constant "
             "changes in activity or plans [from the criteria for mania]."),
        dict(name="activity", cctype="BOOL", pv=PV.BIT,
             comment="Increased activity or physical restlessness."),
        dict(name="sleep", cctype="BOOL", pv=PV.BIT,
             comment="Decreased need for sleep."),
        dict(name="talkativeness", cctype="BOOL", pv=PV.BIT,
             comment="Increased talkativeness (pressure of speech)."),
        dict(name="recklessness", cctype="BOOL", pv=PV.BIT,
             comment="Mild spending sprees, or other types of reckless or "
             "irresponsible behaviour [hypomania]; behaviour which is "
             "foolhardy or reckless and whose risks the subject does not "
             "recognize e.g. spending sprees, foolish enterprises, reckless "
             "driving [mania]."),
        dict(name="social_disinhibition", cctype="BOOL", pv=PV.BIT,
             comment="Increased sociability or over-familiarity [hypomania]; "
             "loss of normal social inhibitions resulting in behaviour which "
             "is inappropriate to the circumstances [mania]."),
        dict(name="sexual", cctype="BOOL", pv=PV.BIT,
             comment="Increased sexual energy [hypomania]; marked sexual "
             "energy or sexual indiscretions [mania]."),
    ]
    MANIA_FIELDSPECS = [
        dict(name="grandiosity", cctype="BOOL", pv=PV.BIT,
             comment="Inflated self-esteem or grandiosity."),
        dict(name="flight_of_ideas", cctype="BOOL", pv=PV.BIT,
             comment="Flight of ideas or the subjective experience of "
             "thoughts racing."),
    ]
    OTHER_CRITERIA_FIELDSPECS = [
        dict(name="sustained4days", cctype="BOOL", pv=PV.BIT,
             comment="Elevated/irritable mood sustained for at least 4 days."),
        dict(name="sustained7days", cctype="BOOL", pv=PV.BIT,
             comment="Elevated/irritable mood sustained for at least 7 days."),
        dict(name="admission_required", cctype="BOOL", pv=PV.BIT,
             comment="Elevated/irritable mood severe enough to require "
             "hospital admission."),
        dict(name="some_interference_functioning", cctype="BOOL",
             pv=PV.BIT, comment="Some interference with personal functioning "
             "in daily living."),
        dict(name="severe_interference_functioning", cctype="BOOL",
             pv=PV.BIT, comment="Severe interference with personal "
             "functioning in daily living."),
    ]
    PSYCHOSIS_FIELDSPECS = [
        dict(name="perceptual_alterations", cctype="BOOL", pv=PV.BIT,
             comment="Perceptual alterations (e.g. subjective hyperacusis, "
             "appreciation of colours as specially vivid, etc.)."),
        # ... not psychotic
        dict(name="hallucinations_schizophrenic", cctype="BOOL",
             pv=PV.BIT,
             comment="Hallucinations that are 'typically schizophrenic' "
             "(hallucinatory voices giving a running commentary on the "
             "patient's behaviour, or discussing him between themselves, or "
             "other types of hallucinatory voices coming from some part of "
             "the body)."),
        dict(name="hallucinations_other", cctype="BOOL", pv=PV.BIT,
             comment="Hallucinations (of any other kind)."),
        dict(name="delusions_schizophrenic", cctype="BOOL", pv=PV.BIT,
             comment="Delusions that are 'typically schizophrenic' (delusions "
             "of control, influence or passivity, clearly referred to body or "
             "limb movements or specific thoughts, actions, or sensations; "
             "delusional perception; persistent delusions of other kinds that "
             "are culturally inappropriate and completely impossible)."),
        dict(name="delusions_other", cctype="BOOL", pv=PV.BIT,
             comment="Delusions (of any other kind)."),
    ]
    CORE_NAMES = [x["name"] for x in CORE_FIELDSPECS]
    HYPOMANIA_MANIA_NAMES = [x["name"] for x in HYPOMANIA_MANIA_FIELDSPECS]
    MANIA_NAMES = [x["name"] for x in MANIA_FIELDSPECS]
    OTHER_CRITERIA_NAMES = [x["name"] for x in OTHER_CRITERIA_FIELDSPECS]
    PSYCHOSIS_NAMES = [x["name"] for x in PSYCHOSIS_FIELDSPECS]

    fieldspecs = (
        [
            dict(name="date_pertains_to", cctype="ISO8601",
                 comment="Date the assessment pertains to"),
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
        ] +
        CORE_FIELDSPECS +
        HYPOMANIA_MANIA_FIELDSPECS +
        MANIA_FIELDSPECS +
        OTHER_CRITERIA_FIELDSPECS +
        PSYCHOSIS_FIELDSPECS
    )

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        infolist = [CtvInfo(
            content="Pertains to: {}. Category: {}.".format(
                format_datetime_string(self.date_pertains_to,
                                       DATEFORMAT.LONG_DATE),
                self.get_description()
            )
        )]
        if self.comments:
            infolist.append(CtvInfo(content=ws.webify(self.comments)))
        return infolist

    def get_summaries(self) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="category",
                           coltype=SummaryCategoryColType,
                           value=self.get_description(),
                           comment="Diagnostic category"),
            SummaryElement(name="psychotic_symptoms",
                           coltype=Boolean(),
                           value=self.psychosis_present(),
                           comment="Psychotic symptoms present?"),
        ]

    # Meets criteria? These also return null for unknown.
    def meets_criteria_mania_psychotic_schizophrenic(self) -> Optional[bool]:
        x = self.meets_criteria_mania_ignoring_psychosis()
        if not x:
            return x
        if self.hallucinations_other or self.delusions_other:
            return False  # that counts as manic psychosis
        if self.hallucinations_other is None or self.delusions_other is None:
            return None  # might be manic psychosis
        if self.hallucinations_schizophrenic or self.delusions_schizophrenic:
            return True
        if (self.hallucinations_schizophrenic is None or
                self.delusions_schizophrenic is None):
            return None
        return False

    def meets_criteria_mania_psychotic_icd(self) -> Optional[bool]:
        x = self.meets_criteria_mania_ignoring_psychosis()
        if not x:
            return x
        if self.hallucinations_other or self.delusions_other:
            return True
        if self.hallucinations_other is None or self.delusions_other is None:
            return None
        return False

    def meets_criteria_mania_nonpsychotic(self) -> Optional[bool]:
        x = self.meets_criteria_mania_ignoring_psychosis()
        if not x:
            return x
        if (self.hallucinations_schizophrenic is None or
                self.delusions_schizophrenic is None or
                self.hallucinations_other is None or
                self.delusions_other is None):
            return None
        if (self.hallucinations_schizophrenic or
                self.delusions_schizophrenic or
                self.hallucinations_other or
                self.delusions_other):
            return False
        return True

    def meets_criteria_mania_ignoring_psychosis(self) -> Optional[bool]:
        # When can we say "definitely not"?
        if is_false(self.mood_elevated) and is_false(self.mood_irritable):
            return False
        if is_false(self.sustained7days) and is_false(self.admission_required):
            return False
        t = self.count_booleans(Icd10Manic.HYPOMANIA_MANIA_NAMES) + \
            self.count_booleans(Icd10Manic.MANIA_NAMES)
        u = self.n_incomplete(Icd10Manic.HYPOMANIA_MANIA_NAMES) + \
            self.n_incomplete(Icd10Manic.MANIA_NAMES)
        if self.mood_elevated and (t + u < 3):
            # With elevated mood, need at least 3 symptoms
            return False
        if is_false(self.mood_elevated) and (t + u < 4):
            # With only irritable mood, need at least 4 symptoms
            return False
        if is_false(self.severe_interference_functioning):
            return False
        # OK. When can we say "yes"?
        if ((self.mood_elevated or self.mood_irritable) and
                (self.sustained7days or self.admission_required) and
                ((self.mood_elevated and t >= 3) or
                    (self.mood_irritable and t >= 4)) and
                self.severe_interference_functioning):
            return True
        return None

    def meets_criteria_hypomania(self) -> Optional[bool]:
        # When can we say "definitely not"?
        if self.meets_criteria_mania_ignoring_psychosis():
            return False  # silly to call it hypomania if it's mania
        if is_false(self.mood_elevated) and is_false(self.mood_irritable):
            return False
        if is_false(self.sustained4days):
            return False
        t = self.count_booleans(Icd10Manic.HYPOMANIA_MANIA_NAMES)
        u = self.n_incomplete(Icd10Manic.HYPOMANIA_MANIA_NAMES)
        if t + u < 3:
            # Need at least 3 symptoms
            return False
        if is_false(self.some_interference_functioning):
            return False
        # OK. When can we say "yes"?
        if ((self.mood_elevated or self.mood_irritable) and
                self.sustained4days and
                t >= 3 and
                self.some_interference_functioning):
            return True
        return None

    def meets_criteria_none(self) -> Optional[bool]:
        h = self.meets_criteria_hypomania()
        m = self.meets_criteria_mania_ignoring_psychosis()
        if h or m:
            return False
        if is_false(h) and is_false(m):
            return True
        return None

    def psychosis_present(self) -> Optional[bool]:
        if (self.hallucinations_other or
                self.hallucinations_schizophrenic or
                self.delusions_other or
                self.delusions_schizophrenic):
            return True
        if (self.hallucinations_other is None or
                self.hallucinations_schizophrenic is None or
                self.delusions_other is None or
                self.delusions_schizophrenic is None):
            return None
        return False

    def get_description(self) -> str:
        if self.meets_criteria_mania_psychotic_schizophrenic():
            return self.wxstring("category_manic_psychotic_schizophrenic")
        elif self.meets_criteria_mania_psychotic_icd():
            return self.wxstring("category_manic_psychotic")
        elif self.meets_criteria_mania_nonpsychotic():
            return self.wxstring("category_manic_nonpsychotic")
        elif self.meets_criteria_hypomania():
            return self.wxstring("category_hypomanic")
        elif self.meets_criteria_none():
            return self.wxstring("category_none")
        else:
            return wappstring("unknown")

    def is_complete(self) -> bool:
        return (
            self.date_pertains_to is not None and
            self.meets_criteria_none() is not None and
            self.field_contents_valid()
        )

    def text_row(self, wstringname: str) -> str:
        return heading_spanning_two_columns(self.wxstring(wstringname))

    def row_true_false(self, fieldname: str) -> str:
        return self.get_twocol_bool_row_true_false(
            fieldname, self.wxstring("" + fieldname))

    def get_task_html(self) -> str:
        h = self.get_standard_clinician_comments_block(self.comments) + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa(wappstring("date_pertains_to"),
                   format_datetime_string(self.date_pertains_to,
                                          DATEFORMAT.LONG_DATE, default=None))
        h += tr_qa(wappstring("category") + " <sup>[1,2]</sup>",
                   self.get_description())
        h += tr_qa(
            self.wxstring("psychotic_symptoms") + " <sup>[2]</sup>",
            get_present_absent_none(self.psychosis_present()))
        h += """
                </table>
            </div>
            <div class="explanation">
        """
        h += wappstring("icd10_symptomatic_disclaimer")
        h += """
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """

        h += self.text_row("core")
        for x in Icd10Manic.CORE_NAMES:
            h += self.row_true_false(x)

        h += self.text_row("hypomania_mania")
        for x in Icd10Manic.HYPOMANIA_MANIA_NAMES:
            h += self.row_true_false(x)

        h += self.text_row("other_mania")
        for x in Icd10Manic.MANIA_NAMES:
            h += self.row_true_false(x)

        h += self.text_row("other_criteria")
        for x in Icd10Manic.OTHER_CRITERIA_NAMES:
            h += self.row_true_false(x)

        h += subheading_spanning_two_columns(self.wxstring("psychosis"))
        for x in Icd10Manic.PSYCHOSIS_NAMES:
            h += self.row_true_false(x)

        h += """
            </table>
            <div class="footnotes">
                [1] Hypomania:
                    elevated/irritable mood
                    + sustained for ≥4 days
                    + at least 3 of the “other hypomania” symptoms
                    + some interference with functioning.
                Mania:
                    elevated/irritable mood
                    + sustained for ≥7 days or hospital admission required
                    + at least 3 of the “other mania/hypomania” symptoms
                      (4 if mood only irritable)
                    + severe interference with functioning.
                [2] ICD-10 nonpsychotic mania requires mania without
                    hallucinations/delusions.
                ICD-10 psychotic mania requires mania plus
                hallucinations/delusions other than those that are
                “typically schizophrenic”.
                ICD-10 does not clearly categorize mania with only
                schizophreniform psychotic symptoms; however, Schneiderian
                first-rank symptoms can occur in manic psychosis
                (e.g. Conus P et al., 2004, PMID 15337330.).
            </div>
        """ + ICD10_COPYRIGHT_DIV
        return h
