#!/usr/bin/env python

"""
camcops_server/tasks/basdai.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

** EATING DISORDER EXAMINATION QUESTIONNAIRE (EDE-Q 6.0) task.**

"""

from typing import Optional

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta

from camcops_server.cc_modules.cc_task import TaskHasPatientMixin, Task


class EdeqMetaclass(DeclarativeMeta):
    pass


class Edeq(TaskHasPatientMixin, Task, metaclass=EdeqMetaclass):
    __tablename__ = "edeq"
    shortname = "EDE-Q"

    def restraint(self) -> Optional[float]:
        restraint_field_names = strseq("q", 1, 5)

        return sum([getattr(self, q) for q in restraint_field_names]) / 5

    def is_complete(self) -> bool:
        return True
