#!/usr/bin/env python3
# nart.py

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

import math
from cc_modules.cc_constants import PV
from cc_modules.cc_html import (
    answer,
    td,
    tr_qa,
)
from cc_modules.cc_task import (
    CLINICIAN_FIELDSPECS,
    CTV_DICTLIST_INCOMPLETE,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


WORDLIST = [
    "chord",  # True for CORRECT, False for INCORRECT
    "ache",
    "depot",
    "aisle",
    "bouquet",
    "psalm",
    "capon",
    "deny",  # NB reserved word in SQL (auto-handled)
    "nausea",
    "debt",
    "courteous",
    "rarefy",
    "equivocal",
    "naive",
    "catacomb",
    "gaoled",
    "thyme",
    "heir",
    "radix",
    "assignate",
    "hiatus",
    "subtle",
    "procreate",
    "gist",
    "gouge",
    "superfluous",
    "simile",
    "banal",
    "quadruped",
    "cellist",
    "facade",
    "zealot",
    "drachm",
    "aeon",
    "placebo",
    "abstemious",
    "detente",
    "idyll",
    "puerperal",
    "aver",
    "gauche",
    "topiary",
    "leviathan",
    "beatify",
    "prelate",
    "sidereal",
    "demesne",
    "syncope",
    "labile",
    "campanile"
]
ACCENTED_WORDLIST = list(WORDLIST)
ACCENTED_WORDLIST[ACCENTED_WORDLIST.index("naive")] = "naïve"
ACCENTED_WORDLIST[ACCENTED_WORDLIST.index("facade")] = "façade"
ACCENTED_WORDLIST[ACCENTED_WORDLIST.index("detente")] = "détente"


# =============================================================================
# NART
# =============================================================================

class Nart(Task):
    @classmethod
    def get_tablename(cls):
        return "nart"

    @classmethod
    def get_taskshortname(cls):
        return "NART"

    @classmethod
    def get_tasklongname(cls):
        return "National Adult Reading Test"

    @classmethod
    def get_fieldspecs(cls):
        fieldspecs = []
        for w in WORDLIST:
            fieldspecs.append(
                dict(name=w, cctype="BOOL", pv=PV.BIT,
                     comment="Pronounced {} correctly "
                     "(0 no, 1 yes)".format(w)))
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + fieldspecs

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "NART predicted FSIQ {}, VIQ {}, PIQ {}".format(
                self.fsiq(), self.viq(), self.piq())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="fsiq", cctype="FLOAT", value=self.fsiq(),
                 comment="Predicted full-scale IQ"),
            dict(name="viq", cctype="FLOAT", value=self.viq(),
                 comment="Predicted verbal IQ"),
            dict(name="piq", cctype="FLOAT", value=self.piq(),
                 comment="Predicted performance IQ"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(WORDLIST)
            and self.field_contents_valid()
        )

    def n_errors(self):
        e = 0
        for w in WORDLIST:
            if getattr(self, w) is not None and not getattr(self, w):
                e += 1
        return e

    def fsiq(self):
        if not self.is_complete():
            return None
        return 127.7 - 0.826 * self.n_errors()

    def viq(self):
        if not self.is_complete():
            return None
        return 129.0 - 0.919 * self.n_errors()

    def piq(self):
        if not self.is_complete():
            return None
        return 123.5 - 0.645 * self.n_errors()

    def get_task_html(self):
        h = self.get_standard_clinician_block() + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa("Total errors", self.n_errors())
        h += tr_qa("Predicted full-scale IQ <sup>[1]</sup>", self.fsiq())
        h += tr_qa("Predicted verbal IQ <sup>[2]</sup>", self.viq())
        h += tr_qa("Predicted performance IQ <sup>[3]</sup>", self.piq())
        h += """
                </table>
            </div>
            <div class="explanation">
                Estimates premorbid IQ by pronunciation of irregular words.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="16%">Word</th><th width="16%">Correct?</th>
                    <th width="16%">Word</th><th width="16%">Correct?</th>
                    <th width="16%">Word</th><th width="16%">Correct?</th>
                </tr>
        """
        nwords = len(WORDLIST)
        ncolumns = 3
        nrows = int(math.ceil(float(nwords)/float(ncolumns)))

        column = 0
        row = 0
        # x: word index (shown in top-to-bottom then left-to-right sequence)
        for unused_loopvar in range(nwords):
            x = (column * nrows) + row
            if column == 0:  # first column
                h += "<tr>"
            h += td(ACCENTED_WORDLIST[x])
            h += td(answer(getattr(self, WORDLIST[x])))
            if column == (ncolumns - 1):  # last column
                h += "</tr>"
                row += 1
            column = (column + 1) % ncolumns
        h += """
            </table>
            <div class="footnotes">
                [1] Full-scale IQ ≈ 127.7 – 0.826 × errors.
                [2] Verbal IQ ≈ 129.0 – 0.919 × errors.
                [3] Performance IQ ≈ 123.5 – 0.645 × errors.
            </div>
            <div class="copyright">
                NART: Copyright © Hazel E. Nelson. Used with permission.
            </div>
        """
        return h
