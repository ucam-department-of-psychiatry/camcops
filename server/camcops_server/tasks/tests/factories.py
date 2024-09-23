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
    Fake,
    GenericTabletRecordFactory,
)

from camcops_server.tasks.apeqpt import Apeqpt
from camcops_server.tasks.apeq_cpft_perinatal import APEQCPFTPerinatal
from camcops_server.tasks.bmi import Bmi
from camcops_server.tasks.core10 import Core10
from camcops_server.tasks.diagnosis import (
    DiagnosisIcd10,
    DiagnosisIcd10Item,
    DiagnosisIcd9CM,
    DiagnosisIcd9CMItem,
)
from camcops_server.tasks.gad7 import Gad7
from camcops_server.tasks.khandaker_mojo_medicationtherapy import (
    KhandakerMojoMedicationTherapy,
)
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


class ApeqptFactory(TaskFactory):
    class Meta:
        model = Apeqpt

    id = factory.Sequence(lambda n: n)


class BmiFactory(TaskHasPatientFactory):
    class Meta:
        model = Bmi

    id = factory.Sequence(lambda n: n)

    height_m = factory.LazyFunction(Fake.en_gb.height_m)
    mass_kg = factory.LazyFunction(Fake.en_gb.mass_kg)
    waist_cm = factory.LazyFunction(Fake.en_gb.waist_cm)


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


class DiagnosisIcd10Factory(TaskHasPatientFactory):
    class Meta:
        model = DiagnosisIcd10

    id = factory.Sequence(lambda n: n)


class DiagnosisItemFactory(GenericTabletRecordFactory):
    class Meta:
        abstract = True


class DiagnosisIcd10ItemFactory(DiagnosisItemFactory):
    class Meta:
        model = DiagnosisIcd10Item

    id = factory.Sequence(lambda n: n)

    @classmethod
    def create(cls, *args, **kwargs) -> T:
        diagnosis_icd10 = kwargs.pop("diagnosis_icd10", None)
        if diagnosis_icd10 is not None:
            if "diagnosis_icd10_id" in kwargs:
                raise TypeError(
                    "Both 'diagnosis_icd10' and 'diagnosis_icd10_id' keyword "
                    "arguments unexpectedly passed to a task factory. Use one "
                    "or the other."
                )
            kwargs["diagnosis_icd10_id"] = diagnosis_icd10.id

            if "_device" not in kwargs:
                kwargs["_device"] = diagnosis_icd10._device

            if "_era" not in kwargs:
                kwargs["_era"] = diagnosis_icd10._era

            if "_current" not in kwargs:
                kwargs["_current"] = True

        return super().create(*args, **kwargs)


class DiagnosisIcd9CMFactory(TaskHasPatientFactory):
    class Meta:
        model = DiagnosisIcd9CM

    id = factory.Sequence(lambda n: n)


class DiagnosisIcd9CMItemFactory(DiagnosisItemFactory):
    class Meta:
        model = DiagnosisIcd9CMItem

    id = factory.Sequence(lambda n: n)

    @classmethod
    def create(cls, *args, **kwargs) -> T:
        diagnosis_icd9cm = kwargs.pop("diagnosis_icd9cm", None)
        if diagnosis_icd9cm is not None:
            if "diagnosis_icd9cm_id" in kwargs:
                raise TypeError(
                    "Both 'diagnosis_icd9cm' and 'diagnosis_icd9cm_id' "
                    "keyword arguments unexpectedly passed to a task factory. "
                    "Use one or the other."
                )
            kwargs["diagnosis_icd9cm_id"] = diagnosis_icd9cm.id

            if "_device" not in kwargs:
                kwargs["_device"] = diagnosis_icd9cm._device

            if "_era" not in kwargs:
                kwargs["_era"] = diagnosis_icd9cm._era

            if "_current" not in kwargs:
                kwargs["_current"] = True

        return super().create(*args, **kwargs)


class Gad7Factory(TaskHasPatientFactory):
    class Meta:
        model = Gad7

    id = factory.Sequence(lambda n: n)


class KhandakerMojoMedicationTherapyFactory(TaskHasPatientFactory):
    class Meta:
        model = KhandakerMojoMedicationTherapy

    id = factory.Sequence(lambda n: n)


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
