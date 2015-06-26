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
# LUNSERS
#==============================================================================

class Lunsers(Task):
    NQUESTIONS = 51
    list_epse = [19, 29, 34, 37, 40, 43, 48]
    list_anticholinergic = [6, 10, 32, 38, 51]
    list_allergic = [1, 35, 47, 49]
    list_miscellaneous = [5, 22, 39, 44]
    list_psychic = [2, 4, 9, 14, 18, 21, 23, 26, 31, 41]
    list_otherautonomic = [15, 16, 20, 27, 36]
    list_hormonal_female = [7, 13, 17, 24, 46, 50]
    list_hormonal_male = [7, 17, 24, 46]
    list_redherrings = [3, 8, 11, 12, 25, 28, 30, 33, 42, 45]

    @classmethod
    def get_tablename(cls):
        return "lunsers"
    @classmethod
    def get_taskshortname(cls):
        return "LUNSERS"
    @classmethod
    def get_tasklongname(cls):
        return "Liverpool University Neuroleptic Side Effect Rating Scale"
    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + repeat_fieldspec("q", 1, Lunsers.NQUESTIONS)
        
    @classmethod
    def provides_trackers(cls):
        return True
    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "LUNSERS total score",
                "axis_label": "Total score (out of {})".format(self.max_score()),
                "axis_min": -0.5,
                "axis_max": 0.5 + self.max_score(),
            }
        ]
    
    def get_summaries(self):
        return [
            ( "is_complete", SQLTYPE_BOOL, self.is_complete() ),
            ( "total", SQLTYPE_INT, self.total_score() ),
        ]

    def get_fieldlist(self, group):
        return ["q" + str(q) for q in group]
        
    def get_relevant_fieldlist(self):
        qnums = range(1, Lunsers.NQUESTIONS + 1)
        if not self.is_female():
            qnums.remove(13)
            qnums.remove(50)
        return ["q" + str(q) for q in qnums]
        
    def is_complete(self):
        return self.are_all_fields_complete(self.get_relevant_fieldlist())
    
    def total_score(self):
        return self.sum_fields(self.get_relevant_fieldlist())
        
    def group_score(self, qnums):
        return self.sum_fields(self.get_fieldlist(qnums))
    
    def get_subheading(self, subtitle, score, max_score):
        return u"""
            <tr class="subheading"><td>{}</td><td><i><b>{}</b> / {}</i></td></tr>
        """.format(
            subtitle,
            score,
            max_score
        )
    
    def get_row(self, q, ANSWER_DICT):
        return u"""<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
            "Q" + str(q) + u" — " + WSTRING("lunsers_q" + str(q)),
            get_from_dict( ANSWER_DICT, getattr(self, "q" + str(q)) )
        )
        
    def get_group_html(self, qnums, subtitle, ANSWER_DICT):
        h = self.get_subheading(
            subtitle,
            self.group_score(qnums),
            len(qnums) * 4
        )
        for q in qnums:
            h += self.get_row(q, ANSWER_DICT)
        return h
    
    def max_score(self):
        return 204 if self.is_female() else 196

    def get_task_html(self):
        score = self.total_score()
        
        ANSWER_DICT = { None: "?" }
        for option in range(0, 5):
            ANSWER_DICT[option] = WSTRING("lunsers_option" + str(option))
        h = u"""
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / {}</td></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings pertain to the past month.
            </div>
            <table class="taskdetail">
                <tr><th width="70%">Question</th><th width="30%">Answer</th></tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score, self.max_score()
        )
        h += self.get_group_html(Lunsers.list_epse, WSTRING("lunsers_group_epse"), ANSWER_DICT)
        h += self.get_group_html(Lunsers.list_anticholinergic, WSTRING("lunsers_group_anticholinergic"), ANSWER_DICT)
        h += self.get_group_html(Lunsers.list_allergic, WSTRING("lunsers_group_allergic"), ANSWER_DICT)
        h += self.get_group_html(Lunsers.list_miscellaneous, WSTRING("lunsers_group_miscellaneous"), ANSWER_DICT)
        h += self.get_group_html(Lunsers.list_psychic, WSTRING("lunsers_group_psychic"), ANSWER_DICT)
        h += self.get_group_html(Lunsers.list_otherautonomic, WSTRING("lunsers_group_otherautonomic"), ANSWER_DICT)
        if self.is_female():
            h += self.get_group_html(Lunsers.list_hormonal_female, WSTRING("lunsers_group_hormonal") + " (" + WSTRING("female") + ")", ANSWER_DICT)
        else:
            h += self.get_group_html(Lunsers.list_hormonal_male, WSTRING("lunsers_group_hormonal") + " (" + WSTRING("male") + ")", ANSWER_DICT)
        h += self.get_group_html(Lunsers.list_redherrings, WSTRING("lunsers_group_redherrings"), ANSWER_DICT)
        h += u"""
            </table>
        """
        return h