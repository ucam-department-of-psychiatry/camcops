#!/usr/bin/env python3
# ybocs.py

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

from typing import List

from ..cc_modules.cc_constants import DATA_COLLECTION_UNLESS_UPGRADED_DIV, PV
from ..cc_modules.cc_html import (
    answer,
    get_ternary,
    subheading_spanning_four_columns,
    tr,
)
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo


# =============================================================================
# Y-BOCS
# =============================================================================

class Ybocs(Task):
    TARGET_FIELDSPECS = [
        dict(name="target_obsession_1", cctype="TEXT",
             comment="Target symptoms: obsession 1"),
        dict(name="target_obsession_2", cctype="TEXT",
             comment="Target symptoms: obsession 2"),
        dict(name="target_obsession_3", cctype="TEXT",
             comment="Target symptoms: obsession 3"),
        dict(name="target_compulsion_1", cctype="TEXT",
             comment="Target symptoms: compulsion 1"),
        dict(name="target_compulsion_2", cctype="TEXT",
             comment="Target symptoms: compulsion 2"),
        dict(name="target_compulsion_3", cctype="TEXT",
             comment="Target symptoms: compulsion 3"),
        dict(name="target_avoidance_1", cctype="TEXT",
             comment="Target symptoms: avoidance 1"),
        dict(name="target_avoidance_2", cctype="TEXT",
             comment="Target symptoms: avoidance 2"),
        dict(name="target_avoidance_3", cctype="TEXT",
             comment="Target symptoms: avoidance 3"),
    ]
    QINFO = [  # number, max score, minimal comment
        ('1',  4, "obsessions: time"),
        ('1b', 4, "obsessions: obsession-free interval"),
        ('2',  4, "obsessions: interference"),
        ('3',  4, "obsessions: distress"),
        ('4',  4, "obsessions: resistance"),
        ('5',  4, "obsessions: control"),
        ('6',  4, "compulsions: time"),
        ('6b', 4, "compulsions: compulsion-free interval"),
        ('7',  4, "compulsions: interference"),
        ('8',  4, "compulsions: distress"),
        ('9',  4, "compulsions: resistance"),
        ('10', 4, "compulsions: control"),
        ('11', 4, "insight"),
        ('12', 4, "avoidance"),
        ('13', 4, "indecisiveness"),
        ('14', 4, "overvalued responsibility"),
        ('15', 4, "slowness"),
        ('16', 4, "doubting"),
        ('17', 4, "global severity"),
        ('18', 6, "global improvement"),
        ('19', 3, "reliability"),
    ]

    tablename = "ybocs"
    shortname = "Y-BOCS"
    longname = "Yale–Brown Obsessive Compulsive Scale"
    fieldspecs = list(TARGET_FIELDSPECS)  # copy
    for qnumstr, maxscore, comment in QINFO:
        fieldspecs.append({
            'name': 'q' + qnumstr,
            'cctype': 'INT',
            'comment': "Q{n}, {s} (0-{m}, higher worse)".format(
                n=qnumstr, s=comment, m=maxscore),
            'min': 0,
            'max': maxscore,
        })
    has_clinician = True

    QUESTION_FIELDS = ["q" + x[0] for x in QINFO]
    SCORED_QUESTIONS = ["q" + str(x) for x in range(1, 10 + 1)]
    OBSESSION_QUESTIONS = ["q" + str(x) for x in range(1, 5 + 1)]
    COMPULSION_QUESTIONS = ["q" + str(x) for x in range(6, 10 + 1)]

    def get_trackers(self) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.total_score(),
                plot_label="Y-BOCS total score (lower is better)",
                axis_label="Total score (out of 40)",
                axis_min=-0.5,
                axis_max=40.5
            ),
            TrackerInfo(
                value=self.obsession_score(),
                plot_label="Y-BOCS obsession score (lower is better)",
                axis_label="Total score (out of 20)",
                axis_min=-0.5,
                axis_max=20.5
            ),
            TrackerInfo(
                value=self.compulsion_score(),
                plot_label="Y-BOCS compulsion score (lower is better)",
                axis_label="Total score (out of 20)",
                axis_min=-0.5,
                axis_max=20.5
            ),
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (/ 40)"),
            dict(name="obsession_score", cctype="INT",
                 value=self.obsession_score(),
                 comment="Obsession score (/ 20)"),
            dict(name="compulsion_score", cctype="INT",
                 value=self.compulsion_score(),
                 comment="Compulsion score (/ 20)"),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        t = self.total_score()
        o = self.obsession_score()
        c = self.compulsion_score()
        return [CtvInfo(content="Y-BOCS total score {t}/40 (obsession {o}/20, "
                                "compulsion {c}/20)".format(t=t, o=o, c=c))]

    def total_score(self) -> int:
        return self.sum_fields(self.SCORED_QUESTIONS)

    def obsession_score(self) -> int:
        return self.sum_fields(self.OBSESSION_QUESTIONS)

    def compulsion_score(self) -> int:
        return self.sum_fields(self.COMPULSION_QUESTIONS)

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.are_all_fields_complete(self.SCORED_QUESTIONS)
        )

    def get_task_html(self) -> str:
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score</td>
                        <td>{total_score} / 40</td>
                    </td>
                    <tr>
                        <td>Obsession score</td>
                        <td>{obsession_score} / 20</td>
                    </td>
                    <tr>
                        <td>Compulsion score</td>
                        <td>{compulsion_score} / 20</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Target symptom</th>
                    <th width="50%">Detail</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total_score=answer(self.total_score()),
            obsession_score=answer(self.obsession_score()),
            compulsion_score=answer(self.compulsion_score()),
        )
        for tsdict in self.TARGET_FIELDSPECS:
            h += tr(
                tsdict['comment'],
                answer(getattr(self, tsdict['name']))
            )
        h += """
            </table>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        for qi in self.QINFO:
            fieldname = "q" + qi[0]
            value = getattr(self, fieldname)
            h += tr(
                self.WXSTRING(fieldname + "_title"),
                answer(self.WXSTRING(fieldname + "_a" + str(value), value)
                       if value is not None else None)
            )
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h


# =============================================================================
# Y-BOCS-SC
# =============================================================================

class YbocsSc(Task):
    SC_PREFIX = "sc_"
    SUFFIX_CURRENT = "_current"
    SUFFIX_PAST = "_past"
    SUFFIX_PRINCIPAL = "_principal"
    SUFFIX_OTHER = "_other"
    SUFFIX_DETAIL = "_detail"
    GROUPS = [
        "obs_aggressive",
        "obs_contamination",
        "obs_sexual",
        "obs_hoarding",
        "obs_religious",
        "obs_symmetry",
        "obs_misc",
        "obs_somatic",
        "com_cleaning",
        "com_checking",
        "com_repeat",
        "com_counting",
        "com_arranging",
        "com_hoarding",
        "com_misc"
    ]
    ITEMS = [
        "obs_aggressive_harm_self",
        "obs_aggressive_harm_others",
        "obs_aggressive_imagery",
        "obs_aggressive_obscenities",
        "obs_aggressive_embarrassing",
        "obs_aggressive_impulses",
        "obs_aggressive_steal",
        "obs_aggressive_accident",
        "obs_aggressive_responsible",
        "obs_aggressive_other",

        "obs_contamination_bodily_waste",
        "obs_contamination_dirt",
        "obs_contamination_environmental",
        "obs_contamination_household",
        "obs_contamination_animals",
        "obs_contamination_sticky",
        "obs_contamination_ill",
        "obs_contamination_others_ill",
        "obs_contamination_feeling",
        "obs_contamination_other",

        "obs_sexual_forbidden",
        "obs_sexual_children_incest",
        "obs_sexual_homosexuality",
        "obs_sexual_to_others",
        "obs_sexual_other",

        "obs_hoarding_other",

        "obs_religious_sacrilege",
        "obs_religious_morality",
        "obs_religious_other",

        "obs_symmetry_with_magical",
        "obs_symmetry_without_magical",

        "obs_misc_know_remember",
        "obs_misc_fear_saying",
        "obs_misc_fear_not_saying",
        "obs_misc_fear_losing",
        "obs_misc_intrusive_nonviolent_images",
        "obs_misc_intrusive_sounds",
        "obs_misc_bothered_sounds",
        "obs_misc_numbers",
        "obs_misc_colours",
        "obs_misc_superstitious",
        "obs_misc_other",

        "obs_somatic_illness",
        "obs_somatic_appearance",
        "obs_somatic_other",

        "com_cleaning_handwashing",
        "com_cleaning_toileting",
        "com_cleaning_cleaning_items",
        "com_cleaning_other_contaminant_avoidance",
        "com_cleaning_other",

        "com_checking_locks_appliances",
        "com_checking_not_harm_others",
        "com_checking_not_harm_self",
        "com_checking_nothing_bad_happens",
        "com_checking_no_mistake",
        "com_checking_somatic",
        "com_checking_other",

        "com_repeat_reread_rewrite",
        "com_repeat_routine",
        "com_repeat_other",

        "com_counting_other",

        "com_arranging_other",

        "com_hoarding_other",

        "com_misc_mental_rituals",
        "com_misc_lists",
        "com_misc_tell_ask",
        "com_misc_touch",
        "com_misc_blink_stare",
        "com_misc_prevent_harm_self",
        "com_misc_prevent_harm_others",
        "com_misc_prevent_terrible",
        "com_misc_eating_ritual",
        "com_misc_superstitious",
        "com_misc_trichotillomania",
        "com_misc_self_harm",
        "com_misc_other"
    ]

    tablename = "ybocssc"
    shortname = "Y-BOCS-SC"
    longname = "Y-BOCS Symptom Checklist"
    fieldspecs = []
    for item in ITEMS:
        fieldspecs.append(dict(
            name=item + SUFFIX_CURRENT,
            cctype="BOOL",
            pv=PV.BIT,
            comment=item + " (current symptom)"
        ))
        fieldspecs.append(dict(
            name=item + SUFFIX_PAST,
            cctype="BOOL",
            pv=PV.BIT,
            comment=item + " (past symptom)"
        ))
        fieldspecs.append(dict(
            name=item + SUFFIX_PRINCIPAL,
            cctype="BOOL",
            pv=PV.BIT,
            comment=item + " (principal symptom)"
        ))
        if item.endswith(SUFFIX_OTHER):
            fieldspecs.append(dict(
                name=item + SUFFIX_DETAIL,
                cctype="TEXT",
                comment=item + " (details)"
            ))
    has_clinician = True
    extrastring_taskname = "ybocs"  # shares with Y-BOCS

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        current_list = []
        past_list = []
        principal_list = []
        for item in self.ITEMS:
            if getattr(self, item + self.SUFFIX_CURRENT):
                current_list.append(item)
            if getattr(self, item + self.SUFFIX_PAST):
                past_list.append(item)
            if getattr(self, item + self.SUFFIX_PRINCIPAL):
                principal_list.append(item)
        return [
            CtvInfo(content="Current symptoms: {}".format(
                ", ".join(current_list))),
            CtvInfo(content="Past symptoms: {}".format(
                ", ".join(past_list))),
            CtvInfo(content="Principal symptoms: {}".format(
                ", ".join(principal_list))),
        ]

    # noinspection PyMethodOverriding
    @staticmethod
    def is_complete() -> bool:
        return True

    def get_task_html(self) -> str:
        h = """
            <table class="taskdetail">
                <tr>
                    <th width="55%">Symptom</th>
                    <th width="15%">Current</th>
                    <th width="15%">Past</th>
                    <th width="15%">Principal</th>
                </tr>
        """
        for group in self.GROUPS:
            h += subheading_spanning_four_columns(
                self.WXSTRING(self.SC_PREFIX + group))
            for item in self.ITEMS:
                if not item.startswith(group):
                    continue
                h += tr(
                    self.WXSTRING(self.SC_PREFIX + item),
                    answer(get_ternary(getattr(self,
                                               item + self.SUFFIX_CURRENT),
                                       value_true="Current",
                                       value_false="",
                                       value_none="")),
                    answer(get_ternary(getattr(self,
                                               item + self.SUFFIX_PAST),
                                       value_true="Past",
                                       value_false="",
                                       value_none="")),
                    answer(get_ternary(getattr(self,
                                               item + self.SUFFIX_PRINCIPAL),
                                       value_true="Principal",
                                       value_false="",
                                       value_none="")),
                )
                if item.endswith(self.SUFFIX_OTHER):
                    h += """
                        <tr>
                            <td><i>Specify:</i></td>
                            <td colspan="3">{content}</td>
                        </tr>
                    """.format(
                        content=answer(
                            getattr(self, item + self.SUFFIX_DETAIL),
                            "")
                    )
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
