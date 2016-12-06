#!/usr/bin/env python
# irac.py

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

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_html import tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# IRAC
# =============================================================================

class Irac(Task):
    tablename = "irac"
    shortname = "IRAC"
    longname = "Identify and Rate the Aim of the Contact"
    fieldspecs = [
        dict(name="aim", cctype="TEXT",
             comment="Main aim of the contact"),
        dict(name="achieved", cctype="INT", min=0, max=2,
             comment="Was the aim achieved? (0 not, 1 partially, 2 fully)"),
    ]

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self) -> bool:
        return (self.are_all_fields_complete(self.TASK_FIELDS) and
                self.field_contents_valid())

    def get_achieved_text(self) -> str:
        achieveddict = {
            None: None,
            0: WSTRING("irac_achieved_0"),
            1: WSTRING("irac_achieved_1"),
            2: WSTRING("irac_achieved_2"),
        }
        return get_from_dict(achieveddict, self.achieved)

    def get_task_html(self) -> str:
        if self.achieved is not None:
            achieved = "{}. {}".format(self.achieved,
                                       self.get_achieved_text())
        else:
            achieved = None
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
        h += tr_qa(WSTRING("irac_q_aim"), ws.webify(self.aim))
        h += tr_qa(WSTRING("irac_q_achieved"), achieved)
        h += """
            </table>
        """
        return h
