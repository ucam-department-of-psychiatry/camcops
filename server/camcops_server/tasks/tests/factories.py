"""
camcops_server/tasks/tests/factories.py

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

**Factory Boy SQL Alchemy test factories for tasks.**

"""

import factory
import pendulum

from camcops_server.cc_modules.cc_testfactories import (
    GenericTabletRecordFactory,
)

from camcops_server.tasks.bmi import Bmi
from camcops_server.tasks.phq9 import Phq9


class TaskFactory(GenericTabletRecordFactory):
    class Meta:
        abstract = True

    @factory.lazy_attribute
    def when_created(self) -> pendulum.DateTime:
        return pendulum.parse(self.default_iso_datetime)


class TaskHasPatientFactory(TaskFactory):
    class Meta:
        abstract = True

    patient_id = None


class BmiFactory(TaskHasPatientFactory):
    class Meta:
        model = Bmi

    id = factory.Sequence(lambda n: n)


class Phq9Factory(TaskHasPatientFactory):
    class Meta:
        model = Phq9

    id = factory.Sequence(lambda n: n)
