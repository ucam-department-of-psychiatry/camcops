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
from typing import TypeVar

from camcops_server.cc_modules.cc_testfactories import (
    GenericTabletRecordFactory,
)

from camcops_server.tasks.apeq_cpft_perinatal import APEQCPFTPerinatal
from camcops_server.tasks.bmi import Bmi
from camcops_server.tasks.core10 import Core10
from camcops_server.tasks.maas import Maas
from camcops_server.tasks.perinatalpoem import PerinatalPoem
from camcops_server.tasks.phq9 import Phq9

T = TypeVar("T")


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

    @classmethod
    def create(cls, *args, **kwargs) -> T:
        patient = kwargs.pop("patient", None)
        if patient is not None:
            if "patient_id" in kwargs:
                raise TypeError(
                    "Both 'patient' and 'patient_id' keyword arguments "
                    "unexpectedly passed to a task factory. Use one or the "
                    "other."
                )
            kwargs["patient_id"] = patient.id

            if "_device" not in kwargs:
                kwargs["_device"] = patient._device

            if "_era" not in kwargs:
                kwargs["_era"] = patient._era

            if "_current" not in kwargs:
                kwargs["_current"] = True

        return super().create(*args, **kwargs)


class APEQCPFTPerinatalFactory(TaskFactory):
    class Meta:
        model = APEQCPFTPerinatal

    id = factory.Sequence(lambda n: n)


class BmiFactory(TaskHasPatientFactory):
    class Meta:
        model = Bmi

    id = factory.Sequence(lambda n: n)


class Core10Factory(TaskHasPatientFactory):
    class Meta:
        model = Core10

    id = factory.Sequence(lambda n: n)

    q1 = 0
    q2 = 0
    q3 = 0
    q4 = 0
    q5 = 0
    q6 = 0
    q7 = 0
    q8 = 0
    q9 = 0
    q10 = 0


class MaasFactory(TaskHasPatientFactory):
    class Meta:
        model = Maas

    id = factory.Sequence(lambda n: n)


class PerinatalPoemFactory(TaskFactory):
    class Meta:
        model = PerinatalPoem

    id = factory.Sequence(lambda n: n)


class Phq9Factory(TaskHasPatientFactory):
    class Meta:
        model = Phq9

    id = factory.Sequence(lambda n: n)
