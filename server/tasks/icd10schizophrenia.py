#!/usr/bin/env python3
# icd10schizophrenia.py

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

import cardinal_pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
    DATEFORMAT,
    ICD10_COPYRIGHT_DIV,
    PV,
)
from cc_modules.cc_dt import format_datetime_string
from cc_modules.cc_html import (
    get_true_false_none,
    heading_spanning_two_columns,
    subheading_spanning_two_columns,
    tr_qa,
)
from cc_modules.cc_lang import is_false
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task


# =============================================================================
# Icd10Schizophrenia
# =============================================================================

class Icd10Schizophrenia(Task):
    A_FIELDSPECS = [
        dict(name="passivity_bodily", cctype="BOOL", pv=PV.BIT,
             comment="Passivity: delusions of control, influence, or "
             "passivity, clearly referred to body or limb movements..."),
        dict(name="passivity_mental", cctype="BOOL", pv=PV.BIT,
             comment="(passivity) ... or to specific thoughts, actions, or "
             "sensations."),
        dict(name="hv_commentary", cctype="BOOL", pv=PV.BIT,
             comment="Hallucinatory voices giving a running commentary on the "
             "patient's behaviour"),
        dict(name="hv_discussing", cctype="BOOL", pv=PV.BIT,
             comment="Hallucinatory voices discussing the patient among "
             "themselves"),
        dict(name="hv_from_body", cctype="BOOL", pv=PV.BIT,
             comment="Other types of hallucinatory voices coming from some "
             "part of the body"),
        dict(name="delusions", cctype="BOOL", pv=PV.BIT,
             comment="Delusions: persistent delusions of other kinds that are "
             "culturally inappropriate and completely impossible, such as "
             "religious or political identity, or superhuman powers and "
             "abilities (e.g. being able to control the weather, or being in "
             "communication with aliens from another world)."),
        dict(name="delusional_perception", cctype="BOOL", pv=PV.BIT,
             comment="Delusional perception [a normal perception, "
             "delusionally interpreted]"),
        dict(name="thought_echo", cctype="BOOL", pv=PV.BIT,
             comment="Thought echo [hearing one's own thoughts aloud, just "
             "before, just after, or simultaneously with the thought]"),
        dict(name="thought_withdrawal", cctype="BOOL", pv=PV.BIT,
             comment="Thought withdrawal [the feeling that one's thoughts "
             "have been removed by an outside agency]"),
        dict(name="thought_insertion", cctype="BOOL", pv=PV.BIT,
             comment="Thought insertion [the feeling that one's thoughts have "
             "been placed there from outside]"),
        dict(name="thought_broadcasting", cctype="BOOL", pv=PV.BIT,
             comment="Thought broadcasting [the feeling that one's thoughts "
             "leave oneself and are diffused widely, or are audible to "
             "others, or that others think the same thoughts in unison]"),
    ]
    B_FIELDSPECS = [
        dict(name="hallucinations_other", cctype="BOOL", pv=PV.BIT,
             comment="Hallucinations: persistent hallucinations in any "
             "modality, when accompanied either by fleeting or half-formed "
             "delusions without clear affective content, or by persistent "
             "over-valued ideas, or when occurring every day for weeks or "
             "months on end."),
        dict(name="thought_disorder", cctype="BOOL", pv=PV.BIT,
             comment="Thought disorder: breaks or interpolations in the train "
             "of thought, resulting in incoherence or irrelevant speech, or "
             "neologisms."),
        dict(name="catatonia", cctype="BOOL", pv=PV.BIT,
             comment="Catatonia: catatonic behaviour, such as excitement, "
             "posturing, or waxy flexibility, negativism, mutism, and "
             "stupor."),
    ]
    C_FIELDSPECS = [
        dict(name="negative", cctype="BOOL", pv=PV.BIT,
             comment="Negative symptoms: 'negative' symptoms such as marked "
             "apathy, paucity of speech, and blunting or incongruity of "
             "emotional responses, usually resulting in social withdrawal and "
             "lowering of social performance; it must be clear that these are "
             "not due to depression or to neuroleptic medication."),
    ]
    D_FIELDSPECS = [
        dict(name="present_one_month", cctype="BOOL", pv=PV.BIT,
             comment="Symptoms in groups A-C present for most of the time "
             "during an episode of psychotic illness lasting for at least one "
             "month (or at some time during most of the days)."),
    ]
    E_FIELDSPECS = [
        dict(name="also_manic", cctype="BOOL", pv=PV.BIT,
             comment="Also meets criteria for manic episode (F30)?"),
        dict(name="also_depressive", cctype="BOOL", pv=PV.BIT,
             comment="Also meets criteria for depressive episode (F32)?"),
        dict(name="if_mood_psychosis_first", cctype="BOOL", pv=PV.BIT,
             comment="If the patient also meets criteria for manic episode "
             "(F30) or depressive episode (F32), the criteria listed above "
             "must have been met before the disturbance of mood developed."),
    ]
    F_FIELDSPECS = [
        dict(name="not_organic_or_substance", cctype="BOOL", pv=PV.BIT,
             comment="The disorder is not attributable to organic brain "
             "disease (in the sense of F0), or to alcohol- or drug-related "
             "intoxication, dependence or withdrawal."),
    ]
    G_FIELDSPECS = [
        dict(name="behaviour_change", cctype="BOOL", pv=PV.BIT,
             comment="A significant and consistent change in the overall "
             "quality of some aspects of personal behaviour, manifest as loss "
             "of interest, aimlessness, idleness, a self-absorbed attitude, "
             "and social withdrawal."),
        dict(name="performance_decline", cctype="BOOL", pv=PV.BIT,
             comment="Marked decline in social, scholastic, or occupational "
             "performance."),
    ]
    H_FIELDSPECS = [
        dict(name="subtype_paranoid", cctype="BOOL", pv=PV.BIT,
             comment="PARANOID (F20.0): dominated by delusions or "
             "hallucinations."),
        dict(name="subtype_hebephrenic", cctype="BOOL", pv=PV.BIT,
             comment="HEBEPHRENIC (F20.1): dominated by affective changes "
             "(shallow, flat, incongruous, or inappropriate affect) and "
             "either pronounced thought disorder or aimless, disjointed "
             "behaviour is present."),
        dict(name="subtype_catatonic", cctype="BOOL", pv=PV.BIT,
             comment="CATATONIC (F20.2): psychomotor disturbances dominate "
             "(such as stupor, mutism, excitement, posturing, negativism, "
             "rigidity, waxy flexibility, command automatisms, or verbal "
             "perseveration)."),
        dict(name="subtype_undifferentiated", cctype="BOOL", pv=PV.BIT,
             comment="UNDIFFERENTIATED (F20.3): schizophrenia with active "
             "psychosis fitting none or more than one of the above three "
             "types."),
        dict(name="subtype_postschizophrenic_depression", cctype="BOOL",
             pv=PV.BIT, comment="POST-SCHIZOPHRENIC DEPRESSION "
             "(F20.4): in which a depressive episode has developed for at "
             "least 2 weeks following a schizophrenic episode within the last "
             "12 months and in which schizophrenic symptoms persist but are "
             "not as prominent as the depression."),
        dict(name="subtype_residual", cctype="BOOL", pv=PV.BIT,
             comment="RESIDUAL (F20.5): in which previous psychotic episodes "
             "of schizophrenia have given way to a chronic condition with "
             "'negative' symptoms of schizophrenia for at least 1 year."),
        dict(name="subtype_simple", cctype="BOOL", pv=PV.BIT,
             comment="SIMPLE SCHIZOPHRENIA (F20.6), in which 'negative' "
             "symptoms (C) with a change in personal behaviour (D) develop "
             "for at least one year without any psychotic episodes (no "
             "symptoms from groups A or B or other hallucinations or "
             "well-formed delusions), and with a marked decline in social, "
             "scholastic, or occupational performance."),
        dict(name="subtype_cenesthopathic", cctype="BOOL", pv=PV.BIT,
             comment="CENESTHOPATHIC (within OTHER F20.8): body image "
             "aberration (e.g. desomatization, loss of bodily boundaries, "
             "feelings of body size change) or abnormal bodily sensations "
             "(e.g. numbness, stiffness, feeling strange, depersonalization, "
             "or sensations of pain, temperature, electricity, heaviness, "
             "lightness, or discomfort when touched) dominate."),
    ]
    A_NAMES = [x["name"] for x in A_FIELDSPECS]
    B_NAMES = [x["name"] for x in B_FIELDSPECS]
    C_NAMES = [x["name"] for x in C_FIELDSPECS]
    D_NAMES = [x["name"] for x in D_FIELDSPECS]
    E_NAMES = [x["name"] for x in E_FIELDSPECS]
    F_NAMES = [x["name"] for x in F_FIELDSPECS]
    G_NAMES = [x["name"] for x in G_FIELDSPECS]
    H_NAMES = [x["name"] for x in H_FIELDSPECS]

    tablename = "icd10schizophrenia"
    shortname = "ICD10-SZ"
    longname = "ICD-10 criteria for schizophrenia (F20)"
    fieldspecs = (
        [
            dict(name="date_pertains_to", cctype="ISO8601",
                 comment="Date the assessment pertains to"),
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
        ]
        + A_FIELDSPECS
        + B_FIELDSPECS
        + C_FIELDSPECS
        + D_FIELDSPECS
        + E_FIELDSPECS
        + F_FIELDSPECS
        + G_FIELDSPECS
        + H_FIELDSPECS
    )
    has_clinician = True

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        c = self.meets_general_criteria()
        if c is None:
            category = "Unknown if met or not met"
        elif c:
            category = "Met"
        else:
            category = "Not met"
        dl = [{
            "content":  "Pertains to: {}. General criteria for "
                        "schizophrenia: {}.".format(
                            format_datetime_string(self.date_pertains_to,
                                                   DATEFORMAT.LONG_DATE),
                            category)
        }]
        if self.comments:
            dl.append({"content": ws.webify(self.comments)})
        return dl

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="meets_general_criteria", cctype="BOOL",
                 value=self.meets_general_criteria(),
                 comment="Meets general criteria for paranoid/hebephrenic/"
                 "catatonic/undifferentiated schizophrenia (F20.0-F20.3)?"),
        ]

    # Meets criteria? These also return null for unknown.
    def meets_general_criteria(self):
        t_a = self.count_booleans(Icd10Schizophrenia.A_NAMES)
        u_a = self.n_incomplete(Icd10Schizophrenia.A_NAMES)
        t_b = self.count_booleans(Icd10Schizophrenia.B_NAMES) + \
            self.count_booleans(Icd10Schizophrenia.C_NAMES)
        u_b = self.n_incomplete(Icd10Schizophrenia.B_NAMES) + \
            self.n_incomplete(Icd10Schizophrenia.C_NAMES)
        if t_a + u_a < 1 and t_b + u_b < 2:
            return False
        if self.present_one_month is not None and not self.present_one_month:
            return False
        if ((self.also_manic or self.also_depressive)
                and is_false(self.if_mood_psychosis_first)):
            return False
        if is_false(self.not_organic_or_substance):
            return False
        if ((t_a >= 1 or t_b >= 2)
                and self.present_one_month
                and (
                    (is_false(self.also_manic)
                        and is_false(self.also_depressive))
                    or self.if_mood_psychosis_first
                )
                and self.not_organic_or_substance):
            return True
        return None

    def is_complete(self):
        return (
            self.date_pertains_to is not None
            and self.meets_general_criteria() is not None
            and self.field_contents_valid()
        )

    def heading_row(self, wstringname, extra=None):
        return heading_spanning_two_columns(
            WSTRING(wstringname) + (extra or "")
        )

    def text_row(self, wstringname):
        return subheading_spanning_two_columns(WSTRING(wstringname))

    def row_true_false(self, fieldname):
        return self.get_twocol_bool_row_true_false(
            fieldname, WSTRING("icd10sz_" + fieldname))

    def row_present_absent(self, fieldname):
        return self.get_twocol_bool_row_present_absent(
            fieldname, WSTRING("icd10sz_" + fieldname))

    def get_task_html(self):
        h = self.get_standard_clinician_comments_block(self.comments) + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa(WSTRING("date_pertains_to"),
                   format_datetime_string(self.date_pertains_to,
                                          DATEFORMAT.LONG_DATE, default=None))
        h += tr_qa(WSTRING("icd10sz_meets_general_criteria")
                   + " <sup>[1]</sup>",
                   get_true_false_none(self.meets_general_criteria()))
        h += """
                </table>
            </div>
            <div class="explanation">
        """
        h += WSTRING("icd10sz_comments")
        h += """
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """

        h += self.heading_row("icd10sz_core", " <sup>[2]</sup>")
        for x in Icd10Schizophrenia.A_NAMES:
            h += self.row_present_absent(x)

        h += self.heading_row("icd10sz_other_positive")
        for x in Icd10Schizophrenia.B_NAMES:
            h += self.row_present_absent(x)

        h += self.heading_row("icd10sz_negative_title")
        for x in Icd10Schizophrenia.C_NAMES:
            h += self.row_present_absent(x)

        h += self.heading_row("icd10sz_other_criteria")
        for x in Icd10Schizophrenia.D_NAMES:
            h += self.row_true_false(x)
        h += self.text_row("icd10sz_duration_comment")
        for x in Icd10Schizophrenia.E_NAMES:
            h += self.row_true_false(x)
        h += self.text_row("icd10sz_affective_comment")
        for x in Icd10Schizophrenia.F_NAMES:
            h += self.row_true_false(x)

        h += self.heading_row("icd10sz_simple_title")
        for x in Icd10Schizophrenia.G_NAMES:
            h += self.row_present_absent(x)

        h += self.heading_row("icd10sz_subtypes")
        for x in Icd10Schizophrenia.H_NAMES:
            h += self.row_present_absent(x)

        h += """
            </table>
            <div class="footnotes">
                [1] All of:
                    (a) at least one core symptom, or at least two of the other
                        positive or negative symptoms;
                    (b) present for a month (etc.);
                    (c) if also manic/depressed, schizophreniform psychosis
                        came first;
                    (d) not attributable to organic brain disease or
                        psychoactive substances.
                [2] Symptom definitions from:
                    (a) Oyebode F (2008). Sims’ Symptoms in the Mind: An
                        Introduction to Descriptive Psychopathology. Fourth
                        edition, Saunders, Elsevier, Edinburgh.
                    (b) Pawar AV &amp; Spence SA (2003), PMID 14519605.
            </div>
        """ + ICD10_COPYRIGHT_DIV
        return h
