#!/usr/bin/env python3
# fft.py

"""
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
"""

from typing import List

from ..cc_modules.cc_html import tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# FFT
# =============================================================================

class Fft(Task):
    tablename = "fft"
    shortname = "FFT"
    longname = "Friends and Family Test"
    fieldspecs = [
        dict(name="service", cctype="TEXT",
             comment="Clinical service being rated"),
        dict(name="rating", cctype="INT", min=1, max=6,
             comment="Likelihood of recommendation to friends/family (1 "
                     "extremely likely - 5 extremely unlikely, 6 don't know)"),
    ]

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self) -> bool:
        return self.rating is not None and self.field_contents_valid()

    def get_rating_text(self) -> str:
        ratingdict = {
            None: None,
            1: WSTRING("fft_a1"),
            2: WSTRING("fft_a2"),
            3: WSTRING("fft_a3"),
            4: WSTRING("fft_a4"),
            5: WSTRING("fft_a5"),
            6: WSTRING("fft_a6"),
        }
        return get_from_dict(ratingdict, self.rating)

    def get_task_html(self) -> str:
        if self.rating is not None:
            r = "{}. {}".format(self.rating, self.get_rating_text())
        else:
            r = None
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr() + """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        h += tr_qa(WSTRING("service_being_rated"), self.service)
        h += tr_qa(WSTRING("fft_q"), r)
        h += """
            </table>
        """
        return h
