#!/usr/bin/python2.7
# -*- encoding: utf8 -*- 

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

from cc_task import *

#==============================================================================
# GASS
#==============================================================================

class Gass(Task):
    NQUESTIONS = 22
    list_sedation = [1, 2]
    list_cardiovascular = [3, 4]
    list_epse = [5, 6, 7, 8, 9, 10]
    list_anticholinergic = [11, 12, 13]
    list_gastrointestinal = [14]
    list_genitourinary = [15]
    list_prolactinaemic_female = [17, 18, 19, 21]
    list_prolactinaemic_male = [17, 18, 19, 20]
    list_weightgain = [22]

    @classmethod
    def get_tablename(cls):
        return "gass"
    @classmethod
    def get_taskshortname(cls):
        return "GASS"
    @classmethod
    def get_tasklongname(cls):
        return "Glasgow Antipsychotic Side-effect Scale"
    @classmethod
    def get_fieldspecs(cls):
        return (
            STANDARD_TASK_FIELDSPECS +
            [
                dict(name="medication", cctype="TEXT"),
            ] +
            repeat_fieldspec("q", 1, Gass.NQUESTIONS) +
            repeat_fieldspec("d", 1, Gass.NQUESTIONS)
        )
        
    @classmethod
    def provides_trackers(cls):
        return True
    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "GASS total score",
                "axis_label": "Total score (out of 63)",
                "axis_min": -0.5,
                "axis_max": 63.5,
            }
        ]
    
    def get_summaries(self):
        return [
            ( "is_complete", SQLTYPE_BOOL, self.is_complete() ),
            ( "total", SQLTYPE_INT, self.total_score() ),
        ]

    def get_q_fieldlist(self, group):
        return ["q" + str(q) for q in group]
        
    def get_d_fieldlist(self, group):
        return ["d" + str(q) for q in group]
        
    def get_relevant_q_fieldlist(self):
        qnums = range(1, Gass.NQUESTIONS + 1)
        if self.is_female():
            qnums.remove(20)
        else:
            qnums.remove(21)
        return ["q" + str(q) for q in qnums]
        
    def is_complete(self):
        return self.are_all_fields_complete(self.get_relevant_q_fieldlist())
    
    def total_score(self):
        return self.sum_fields(self.get_relevant_q_fieldlist())
        
    def group_score(self, qnums):
        return self.sum_fields(self.get_q_fieldlist(qnums))
    
    def get_subheading(self, subtitle, score, max_score):
        return u"""
            <tr class="subheading"><td>{}</td><td colspan="2"><i><b>{}</b> / {}</i></td></tr>
        """.format(
            subtitle,
            score,
            max_score
        )
    
    def get_row(self, q, ANSWER_DICT):
        return u"""<tr><td>{}</td><td><b>{}</b></td><td>{}</td></tr>""".format(
            WSTRING("gass_q" + str(q)),
            get_from_dict( ANSWER_DICT, getattr(self, "q" + str(q)) ),
            get_yes_no( getattr(self, "d" + str(q)) )
        )
        
    def get_group_html(self, qnums, subtitle, ANSWER_DICT):
        h = self.get_subheading(
            subtitle,
            self.group_score(qnums),
            len(qnums) * 3
        )
        for q in qnums:
            h += self.get_row(q, ANSWER_DICT)
        return h

    def get_task_html(self):
        score = self.total_score()
        ANSWER_DICT = { None: "?" }
        for option in range(0, 4):
            ANSWER_DICT[option] = str(option) + u" — " + WSTRING("gass_option" + str(option))
        h = u"""
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 63</td></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings pertain to the past week.
            </div>
            <table class="taskdetail">
                <tr><th width="65%">Question</th><th width="20%">Answer</th><th width="15%">Distressing?</th></tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score
        )
        h += self.get_group_html(Gass.list_sedation, WSTRING("gass_group_sedation"), ANSWER_DICT)
        h += self.get_group_html(Gass.list_cardiovascular, WSTRING("gass_group_cardiovascular"), ANSWER_DICT)
        h += self.get_group_html(Gass.list_epse, WSTRING("gass_group_epse"), ANSWER_DICT)
        h += self.get_group_html(Gass.list_anticholinergic, WSTRING("gass_group_anticholinergic"), ANSWER_DICT)
        h += self.get_group_html(Gass.list_gastrointestinal, WSTRING("gass_group_gastrointestinal"), ANSWER_DICT)
        h += self.get_group_html(Gass.list_genitourinary, WSTRING("gass_group_genitourinary"), ANSWER_DICT)
        if self.is_female():
            h += self.get_group_html(Gass.list_prolactinaemic_female, WSTRING("gass_group_prolactinaemic") + " (" + WSTRING("female") + ")", ANSWER_DICT)
        else:
            h += self.get_group_html(Gass.list_prolactinaemic_male, WSTRING("gass_group_prolactinaemic") + " (" + WSTRING("male") + ")", ANSWER_DICT)
        h += self.get_group_html(Gass.list_weightgain, WSTRING("gass_group_weightgain"), ANSWER_DICT)
        h += u"""
                <tr class="subheading"><td colspan="3">{}</td></tr>
                <tr><td colspan="3">{}</td></tr>
            </table>
        """.format(
            WSTRING("gass_medication_hint"),
            ws.webify(self.medication)
        )
        return h