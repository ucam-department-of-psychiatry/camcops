#!/usr/bin/env python
# nart.py

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

import math
from typing import List, Optional

from ..cc_modules.cc_constants import PV
from ..cc_modules.cc_html import answer, td, tr_qa
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task


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
    tablename = "nart"
    shortname = "NART"
    longname = "National Adult Reading Test"
    fieldspecs = []
    for w in WORDLIST:
        fieldspecs.append(
            dict(name=w, cctype="BOOL", pv=PV.BIT,
                 comment="Pronounced {} correctly "
                 "(0 no, 1 yes)".format(w)))
    has_clinician = True

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="NART predicted FSIQ {}, VIQ {}, PIQ {}".format(
                self.fsiq(), self.viq(), self.piq())
        )]

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

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(WORDLIST) and
            self.field_contents_valid()
        )

    def n_errors(self) -> int:
        e = 0
        for w in WORDLIST:
            if getattr(self, w) is not None and not getattr(self, w):
                e += 1
        return e

    def fsiq(self) -> Optional[float]:
        if not self.is_complete():
            return None
        return 127.7 - 0.826 * self.n_errors()

    def viq(self) -> Optional[float]:
        if not self.is_complete():
            return None
        return 129.0 - 0.919 * self.n_errors()

    def piq(self) -> Optional[float]:
        if not self.is_complete():
            return None
        return 123.5 - 0.645 * self.n_errors()

    def get_task_html(self) -> str:
        h = """
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
