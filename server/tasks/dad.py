#!/usr/bin/env python3
# dad.py

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

from ..cc_modules.cc_constants import (
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
)
from ..cc_modules.cc_html import (
    answer,
    subheading_spanning_two_columns,
    tr,
)
from ..cc_modules.cc_task import Task

YES = 1
NO = 0
NA = -99

# =============================================================================
# DAD
# =============================================================================


class Dad(Task):
    GROUPS = [
        "hygiene",
        "dressing",
        "continence",
        "eating",
        "mealprep",
        "telephone",
        "outing",
        "finance",
        "medications",
        "leisure"
    ]
    ITEMS = [
        "hygiene_init_wash",
        "hygiene_init_teeth",
        "hygiene_init_hair",
        "hygiene_plan_wash",
        "hygiene_exec_wash",
        "hygiene_exec_hair",
        "hygiene_exec_teeth",

        "dressing_init_dress",
        "dressing_plan_clothing",
        "dressing_plan_order",
        "dressing_exec_dress",
        "dressing_exec_undress",

        "continence_init_toilet",
        "continence_exec_toilet",

        "eating_init_eat",
        "eating_plan_utensils",
        "eating_exec_eat",

        "mealprep_init_meal",
        "mealprep_plan_meal",
        "mealprep_exec_meal",

        "telephone_init_phone",
        "telephone_plan_dial",
        "telephone_exec_conversation",
        "telephone_exec_message",

        "outing_init_outing",
        "outing_plan_outing",
        "outing_exec_reach_destination",
        "outing_exec_mode_transportation",
        "outing_exec_return_with_shopping",

        "finance_init_interest",
        "finance_plan_pay_bills",
        "finance_plan_organise_correspondence",
        "finance_exec_handle_money",

        "medications_init_medication",
        "medications_exec_take_medications",

        "leisure_init_interest_leisure",
        "leisure_init_interest_chores",
        "leisure_plan_chores",
        "leisure_exec_complete_chores",
        "leisure_exec_safe_at_home"
    ]
    explan = " ({} yes, {} no, {} not applicable)".format(YES, NO, NA)

    tablename = "dad"
    shortname = "DAD"
    longname = "Disability Assessment for Dementia"
    fieldspecs = []
    for item in ITEMS:
        fieldspecs.append(dict(
            name=item,
            cctype="INT",
            pv=[YES, NO, NA],
            comment=item + explan,
        ))
    has_clinician = True
    has_respondent = True

    def get_summaries(self):
        d = self.get_score_dict()
        s = [self.is_complete_summary_field()]
        for item in d:
            s.extend([
                dict(name=item + "_n", cctype="INT",
                     value=d[item][0], comment=item + " (numerator)"),
                dict(name=item + "_d", cctype="INT",
                     value=d[item][1], comment=item + " (denominator)"),
            ])
        return s

    @staticmethod
    def is_complete():
        return True

    @classmethod
    def get_items_activity(cls, activity):
        return [item for item in cls.ITEMS if item.startswith(activity)]

    @classmethod
    def get_items_activities(cls, activities):
        return [item for item in cls.ITEMS
                if any(item.startswith(activity) for activity in activities)]

    @classmethod
    def get_items_phase(cls, phase):
        return [item for item in cls.ITEMS if phase in item]

    def get_score(self, fields):
        score = self.count_where(fields, [YES])
        possible = self.count_wherenot(fields, [None, NA])
        return score, possible

    def get_score_dict(self):
        total = self.get_score(self.ITEMS)
        hygiene = self.get_score(self.get_items_activity('hygiene'))
        dressing = self.get_score(self.get_items_activity('dressing'))
        continence = self.get_score(self.get_items_activity('continence'))
        eating = self.get_score(self.get_items_activity('eating'))
        badl = self.get_score(self.get_items_activities(
            ['hygiene', 'dressing', 'continence', 'eating']))
        mealprep = self.get_score(self.get_items_activity('mealprep'))
        telephone = self.get_score(self.get_items_activity('telephone'))
        outing = self.get_score(self.get_items_activity('outing'))
        finance = self.get_score(self.get_items_activity('finance'))
        medications = self.get_score(self.get_items_activity('medications'))
        leisure = self.get_score(self.get_items_activity('leisure'))
        iadl = self.get_score(self.get_items_activities(
            ['mealprep', 'telephone', 'outing', 'finance',
             'medications', 'leisure']))
        initiation = self.get_score(self.get_items_phase('init'))
        planning = self.get_score(self.get_items_phase('plan'))
        execution = self.get_score(self.get_items_phase('exec'))
        # n for numerator, d for denominator
        return dict(
            total=total,
            hygiene=hygiene,
            dressing=dressing,
            continence=continence,
            eating=eating,
            badl=badl,
            mealprep=mealprep,
            telephone=telephone,
            outing=outing,
            finance=finance,
            medications=medications,
            leisure=leisure,
            iadl=iadl,
            initiation=initiation,
            planning=planning,
            execution=execution,
        )

    @staticmethod
    def report_score(score_tuple):
        return "{} / {}".format(answer(score_tuple[0]), score_tuple[1])

    def report_answer(self, field):
        value = getattr(self, field)
        if value == YES:
            text = "Yes (1)"
        elif value == NO:
            text = "No (0)"
        elif value == NA:
            text = "N/A"
        else:
            text = None
        return answer(text)

    def get_task_html(self):
        d = self.get_score_dict()
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr><td>Total</td><td>{total}</td></tr>
                    <tr><td>Activity: hygiene</td><td>{hygiene}</td></tr>
                    <tr><td>Activity: dressing</td><td>{dressing}</td></tr>
                    <tr><td>Activity: continence</td><td>{continence}</td></tr>
                    <tr><td>Activity: eating</td><td>{eating}</td></tr>
                    <tr>
                        <td>Basic activities of daily living (BADLs) (hygiene,
                        dressing, continence, eating)</td>
                        <td>{badl}</td>
                    </tr>
                    <tr>
                        <td>Activity: meal preparation</td><td>{mealprep}</td>
                    </tr>
                    <tr><td>Activity: telephone</td><td>{telephone}</td></tr>
                    <tr><td>Activity: outings</td><td>{outing}</td></tr>
                    <tr><td>Activity: finance</td><td>{finance}</td></tr>
                    <tr>
                        <td>Activity: medications</td><td>{medications}</td>
                    </tr>
                    <tr><td>Activity: leisure</td><td>{leisure}</td></tr>
                    <tr>
                        <td>Instrumental activities of daily living (IADLs)
                        (meal prep., telephone, outings, finance, medications,
                        leisure)</td>
                        <td>{iadl}</td>
                    </tr>
                    <tr>
                        <td>Phase: initiation</td>
                        <td>{initiation}</td>
                    </tr>
                    <tr>
                        <td>Phase: planning/organisation</td>
                        <td>{planning}</td>
                    </tr>
                    <tr>
                        <td>Phase: execution/performance</td>
                        <td>{execution}</td>
                    </tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question (I = initiation, P = planning,
                        E = execution)</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=self.report_score(d['total']),
            hygiene=self.report_score(d['hygiene']),
            dressing=self.report_score(d['dressing']),
            continence=self.report_score(d['continence']),
            eating=self.report_score(d['eating']),
            badl=self.report_score(d['badl']),
            mealprep=self.report_score(d['mealprep']),
            telephone=self.report_score(d['telephone']),
            outing=self.report_score(d['outing']),
            finance=self.report_score(d['finance']),
            medications=self.report_score(d['medications']),
            leisure=self.report_score(d['leisure']),
            iadl=self.report_score(d['iadl']),
            initiation=self.report_score(d['initiation']),
            planning=self.report_score(d['planning']),
            execution=self.report_score(d['execution']),
        )
        for group in self.GROUPS:
            h += subheading_spanning_two_columns(self.WXSTRING(group))
            for item in self.ITEMS:
                if not item.startswith(group):
                    continue
                q = self.WXSTRING(item)
                if '_init_' in item:
                    q += " (I)"
                elif '_plan_' in item:
                    q += " (P)"
                elif '_exec_' in item:
                    q += " (E)"
                else:
                    # Shouldn't happen
                    q += " (?)"
                h += tr(q, self.report_answer(item))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
