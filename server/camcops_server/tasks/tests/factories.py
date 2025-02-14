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
from typing import cast, TYPE_CHECKING

from camcops_server.cc_modules.cc_task import Task
from camcops_server.cc_modules.cc_testfactories import (
    BlobFactory,
    Fake,
    GenericTabletRecordFactory,
)

from camcops_server.tasks.ace3 import Ace3, MiniAce
from camcops_server.tasks.aims import Aims
from camcops_server.tasks.apeqpt import Apeqpt
from camcops_server.tasks.apeq_cpft_perinatal import APEQCPFTPerinatal
from camcops_server.tasks.aq import Aq
from camcops_server.tasks.asdas import Asdas
from camcops_server.tasks.audit import Audit, AuditC
from camcops_server.tasks.badls import Badls
from camcops_server.tasks.basdai import Basdai
from camcops_server.tasks.bdi import Bdi
from camcops_server.tasks.bmi import Bmi
from camcops_server.tasks.bprs import Bprs
from camcops_server.tasks.bprse import Bprse
from camcops_server.tasks.cage import Cage
from camcops_server.tasks.cape42 import Cape42
from camcops_server.tasks.caps import Caps
from camcops_server.tasks.cardinal_expdetthreshold import (
    CardinalExpDetThreshold,
)
from camcops_server.tasks.cardinal_expectationdetection import (
    CardinalExpectationDetection,
)
from camcops_server.tasks.cbir import CbiR
from camcops_server.tasks.ceca import CecaQ3
from camcops_server.tasks.cesd import Cesd
from camcops_server.tasks.cesdr import Cesdr
from camcops_server.tasks.cet import Cet
from camcops_server.tasks.cgi_task import Cgi, CgiI
from camcops_server.tasks.cgisch import CgiSch
from camcops_server.tasks.chit import Chit
from camcops_server.tasks.cia import Cia
from camcops_server.tasks.cisr import Cisr
from camcops_server.tasks.ciwa import Ciwa
from camcops_server.tasks.contactlog import ContactLog
from camcops_server.tasks.cope import CopeBrief
from camcops_server.tasks.core10 import Core10
from camcops_server.tasks.cpft_covid_medical import CpftCovidMedical
from camcops_server.tasks.cpft_lps import (
    CPFTLPSDischarge,
    CPFTLPSReferral,
    CPFTLPSResetResponseClock,
)
from camcops_server.tasks.cpft_research_preferences import (
    CpftResearchPreferences,
)
from camcops_server.tasks.dad import Dad
from camcops_server.tasks.das28 import Das28
from camcops_server.tasks.dast import Dast
from camcops_server.tasks.deakin_s1_healthreview import DeakinS1HealthReview
from camcops_server.tasks.demoquestionnaire import DemoQuestionnaire
from camcops_server.tasks.demqol import Demqol, DemqolProxy
from camcops_server.tasks.diagnosis import (
    DiagnosisIcd10,
    DiagnosisIcd10Item,
    DiagnosisIcd9CM,
    DiagnosisIcd9CMItem,
)
from camcops_server.tasks.distressthermometer import DistressThermometer
from camcops_server.tasks.edeq import Edeq
from camcops_server.tasks.elixhauserci import ElixhauserCI
from camcops_server.tasks.epds import Epds
from camcops_server.tasks.eq5d5l import Eq5d5l
from camcops_server.tasks.esspri import Esspri
from camcops_server.tasks.factg import Factg
from camcops_server.tasks.fast import Fast
from camcops_server.tasks.fft import Fft
from camcops_server.tasks.frs import Frs
from camcops_server.tasks.gad7 import Gad7
from camcops_server.tasks.gaf import Gaf
from camcops_server.tasks.gbo import Gbogpc, Gbogras, Gbogres
from camcops_server.tasks.gds import Gds15
from camcops_server.tasks.gmcpq import GMCPQ
from camcops_server.tasks.hads import Hads, HadsRespondent
from camcops_server.tasks.hama import Hama
from camcops_server.tasks.hamd import Hamd
from camcops_server.tasks.hamd7 import Hamd7
from camcops_server.tasks.honos import Honos, Honos65, Honosca
from camcops_server.tasks.icd10depressive import Icd10Depressive
from camcops_server.tasks.icd10manic import Icd10Manic
from camcops_server.tasks.icd10mixed import Icd10Mixed
from camcops_server.tasks.icd10schizophrenia import Icd10Schizophrenia
from camcops_server.tasks.icd10schizotypal import Icd10Schizotypal
from camcops_server.tasks.icd10specpd import Icd10SpecPD
from camcops_server.tasks.ided3d import IDED3D
from camcops_server.tasks.iesr import Iesr
from camcops_server.tasks.ifs import Ifs
from camcops_server.tasks.irac import Irac
from camcops_server.tasks.isaaq10 import Isaaq10
from camcops_server.tasks.isaaqed import IsaaqEd
from camcops_server.tasks.khandaker_insight_medical import (
    KhandakerInsightMedical,
)
from camcops_server.tasks.khandaker_mojo_medical import KhandakerMojoMedical
from camcops_server.tasks.khandaker_mojo_sociodemographics import (
    KhandakerMojoSociodemographics,
)
from camcops_server.tasks.khandaker_mojo_medicationtherapy import (
    KhandakerMojoMedicationTherapy,
)
from camcops_server.tasks.kirby_mcq import Kirby
from camcops_server.tasks.lynall_iam_life import LynallIamLifeEvents
from camcops_server.tasks.lynall_iam_medical import LynallIamMedicalHistory
from camcops_server.tasks.maas import Maas
from camcops_server.tasks.mast import Mast
from camcops_server.tasks.mds_updrs import MdsUpdrs
from camcops_server.tasks.mfi20 import Mfi20
from camcops_server.tasks.moca import Moca
from camcops_server.tasks.nart import Nart
from camcops_server.tasks.npiq import NpiQ
from camcops_server.tasks.ors import Ors
from camcops_server.tasks.panss import Panss
from camcops_server.tasks.paradise24 import Paradise24
from camcops_server.tasks.pbq import Pbq
from camcops_server.tasks.pcl5 import Pcl5
from camcops_server.tasks.pcl import PclC, PclM, PclS
from camcops_server.tasks.pdss import Pdss
from camcops_server.tasks.perinatalpoem import PerinatalPoem
from camcops_server.tasks.photo import (
    Photo,
    PhotoSequence,
    PhotoSequenceSinglePhoto,
)
from camcops_server.tasks.phq15 import Phq15
from camcops_server.tasks.phq8 import Phq8
from camcops_server.tasks.phq9 import Phq9
from camcops_server.tasks.progressnote import ProgressNote
from camcops_server.tasks.pswq import Pswq
from camcops_server.tasks.psychiatricclerking import PsychiatricClerking
from camcops_server.tasks.qolbasic import QolBasic
from camcops_server.tasks.qolsg import QolSG
from camcops_server.tasks.rand36 import Rand36
from camcops_server.tasks.rapid3 import Rapid3
from camcops_server.tasks.service_satisfaction import (
    PatientSatisfaction,
    ReferrerSatisfactionGen,
    ReferrerSatisfactionSpec,
)
from camcops_server.tasks.sfmpq2 import Sfmpq2
from camcops_server.tasks.shaps import Shaps
from camcops_server.tasks.slums import Slums
from camcops_server.tasks.smast import Smast
from camcops_server.tasks.srs import Srs
from camcops_server.tasks.suppsp import Suppsp
from camcops_server.tasks.wemwbs import Swemwbs, Wemwbs
from camcops_server.tasks.wsas import Wsas
from camcops_server.tasks.ybocs import Ybocs, YbocsSc
from camcops_server.tasks.zbi import Zbi12

if TYPE_CHECKING:
    from factory.builder import Resolver


class TaskFactory(GenericTabletRecordFactory):
    class Meta:
        abstract = True

    @factory.lazy_attribute
    def when_created(self) -> pendulum.DateTime:
        datetime = cast(
            pendulum.DateTime, pendulum.parse(self.default_iso_datetime)
        )

        return datetime


class TaskHasPatientFactory(TaskFactory):
    class Meta:
        abstract = True

    patient_id = None

    @classmethod
    def create(cls, *args, **kwargs) -> Task:
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

            if "_group" not in kwargs:
                kwargs["_group"] = patient._group

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
    def create(cls, *args, **kwargs) -> DiagnosisIcd10Item:
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
    def create(cls, *args, **kwargs) -> DiagnosisIcd9CMItem:
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


class Ace3Factory(TaskHasPatientFactory):
    class Meta:
        model = Ace3

    id = factory.Sequence(lambda n: n)


class AimsFactory(TaskHasPatientFactory):
    class Meta:
        model = Aims

    id = factory.Sequence(lambda n: n)


class AqFactory(TaskHasPatientFactory):
    class Meta:
        model = Aq

    id = factory.Sequence(lambda n: n)


class AsdasFactory(TaskHasPatientFactory):
    class Meta:
        model = Asdas

    id = factory.Sequence(lambda n: n)


class AuditFactory(TaskHasPatientFactory):
    class Meta:
        model = Audit

    id = factory.Sequence(lambda n: n)


class AuditCFactory(TaskHasPatientFactory):
    class Meta:
        model = AuditC

    id = factory.Sequence(lambda n: n)


class BadlsFactory(TaskHasPatientFactory):
    class Meta:
        model = Badls

    id = factory.Sequence(lambda n: n)


class BasdaiFactory(TaskHasPatientFactory):
    class Meta:
        model = Basdai

    id = factory.Sequence(lambda n: n)


class BdiFactory(TaskHasPatientFactory):
    class Meta:
        model = Bdi

    id = factory.Sequence(lambda n: n)


class BprsFactory(TaskHasPatientFactory):
    class Meta:
        model = Bprs

    id = factory.Sequence(lambda n: n)


class BprseFactory(TaskHasPatientFactory):
    class Meta:
        model = Bprse

    id = factory.Sequence(lambda n: n)


class CageFactory(TaskHasPatientFactory):
    class Meta:
        model = Cage

    id = factory.Sequence(lambda n: n)


class Cape42Factory(TaskHasPatientFactory):
    class Meta:
        model = Cape42

    id = factory.Sequence(lambda n: n)


class CapsFactory(TaskHasPatientFactory):
    class Meta:
        model = Caps

    id = factory.Sequence(lambda n: n)


class CardinalExpectationDetectionFactory(TaskHasPatientFactory):
    class Meta:
        model = CardinalExpectationDetection

    id = factory.Sequence(lambda n: n)


class CardinalExpDetThresholdFactory(TaskHasPatientFactory):
    class Meta:
        model = CardinalExpDetThreshold

    id = factory.Sequence(lambda n: n)


class CbiRFactory(TaskHasPatientFactory):
    class Meta:
        model = CbiR

    id = factory.Sequence(lambda n: n)


class CecaQ3Factory(TaskHasPatientFactory):
    class Meta:
        model = CecaQ3

    id = factory.Sequence(lambda n: n)


class CesdFactory(TaskHasPatientFactory):
    class Meta:
        model = Cesd

    id = factory.Sequence(lambda n: n)


class CesdrFactory(TaskHasPatientFactory):
    class Meta:
        model = Cesdr

    id = factory.Sequence(lambda n: n)


class CetFactory(TaskHasPatientFactory):
    class Meta:
        model = Cet

    id = factory.Sequence(lambda n: n)


class CgiFactory(TaskHasPatientFactory):
    class Meta:
        model = Cgi

    id = factory.Sequence(lambda n: n)


class CgiIFactory(TaskHasPatientFactory):
    class Meta:
        model = CgiI

    id = factory.Sequence(lambda n: n)


class CgiSchFactory(TaskHasPatientFactory):
    class Meta:
        model = CgiSch

    id = factory.Sequence(lambda n: n)


class ChitFactory(TaskHasPatientFactory):
    class Meta:
        model = Chit

    id = factory.Sequence(lambda n: n)


class CiaFactory(TaskHasPatientFactory):
    class Meta:
        model = Cia

    id = factory.Sequence(lambda n: n)


class CisrFactory(TaskHasPatientFactory):
    class Meta:
        model = Cisr

    id = factory.Sequence(lambda n: n)


class CiwaFactory(TaskHasPatientFactory):
    class Meta:
        model = Ciwa

    id = factory.Sequence(lambda n: n)


class ContactLogFactory(TaskHasPatientFactory):
    class Meta:
        model = ContactLog

    id = factory.Sequence(lambda n: n)


class CopeBriefFactory(TaskHasPatientFactory):
    class Meta:
        model = CopeBrief

    id = factory.Sequence(lambda n: n)


class CpftCovidMedicalFactory(TaskHasPatientFactory):
    class Meta:
        model = CpftCovidMedical

    id = factory.Sequence(lambda n: n)


class CPFTLPSDischargeFactory(TaskHasPatientFactory):
    class Meta:
        model = CPFTLPSDischarge

    id = factory.Sequence(lambda n: n)


class CPFTLPSReferralFactory(TaskHasPatientFactory):
    class Meta:
        model = CPFTLPSReferral

    id = factory.Sequence(lambda n: n)


class CPFTLPSResetResponseClockFactory(TaskHasPatientFactory):
    class Meta:
        model = CPFTLPSResetResponseClock

    id = factory.Sequence(lambda n: n)


class CpftResearchPreferencesFactory(TaskHasPatientFactory):
    class Meta:
        model = CpftResearchPreferences

    id = factory.Sequence(lambda n: n)


class DadFactory(TaskHasPatientFactory):
    class Meta:
        model = Dad

    id = factory.Sequence(lambda n: n)


class Das28Factory(TaskHasPatientFactory):
    class Meta:
        model = Das28

    id = factory.Sequence(lambda n: n)


class DastFactory(TaskHasPatientFactory):
    class Meta:
        model = Dast

    id = factory.Sequence(lambda n: n)


class DeakinS1HealthReviewFactory(TaskHasPatientFactory):
    class Meta:
        model = DeakinS1HealthReview

    id = factory.Sequence(lambda n: n)


class DemoQuestionnaireFactory(TaskFactory):
    class Meta:
        model = DemoQuestionnaire

    id = factory.Sequence(lambda n: n)


class DemqolFactory(TaskHasPatientFactory):
    class Meta:
        model = Demqol

    id = factory.Sequence(lambda n: n)


class DemqolProxyFactory(TaskHasPatientFactory):
    class Meta:
        model = DemqolProxy

    id = factory.Sequence(lambda n: n)


class DistressThermometerFactory(TaskHasPatientFactory):
    class Meta:
        model = DistressThermometer

    id = factory.Sequence(lambda n: n)


class EdeqFactory(TaskHasPatientFactory):
    class Meta:
        model = Edeq

    id = factory.Sequence(lambda n: n)


class ElixhauserCIFactory(TaskHasPatientFactory):
    class Meta:
        model = ElixhauserCI

    id = factory.Sequence(lambda n: n)


class EpdsFactory(TaskHasPatientFactory):
    class Meta:
        model = Epds

    id = factory.Sequence(lambda n: n)


class Eq5d5lFactory(TaskHasPatientFactory):
    class Meta:
        model = Eq5d5l

    id = factory.Sequence(lambda n: n)


class EsspriFactory(TaskHasPatientFactory):
    class Meta:
        model = Esspri

    id = factory.Sequence(lambda n: n)


class FactgFactory(TaskHasPatientFactory):
    class Meta:
        model = Factg

    id = factory.Sequence(lambda n: n)


class FastFactory(TaskHasPatientFactory):
    class Meta:
        model = Fast

    id = factory.Sequence(lambda n: n)


class FftFactory(TaskHasPatientFactory):
    class Meta:
        model = Fft

    id = factory.Sequence(lambda n: n)


class FrsFactory(TaskHasPatientFactory):
    class Meta:
        model = Frs

    id = factory.Sequence(lambda n: n)


class GafFactory(TaskHasPatientFactory):
    class Meta:
        model = Gaf

    id = factory.Sequence(lambda n: n)


class GbogpcFactory(TaskHasPatientFactory):
    class Meta:
        model = Gbogpc

    id = factory.Sequence(lambda n: n)


class GbograsFactory(TaskHasPatientFactory):
    class Meta:
        model = Gbogras

    id = factory.Sequence(lambda n: n)


class GbogresFactory(TaskHasPatientFactory):
    class Meta:
        model = Gbogres

    id = factory.Sequence(lambda n: n)


class Gds15Factory(TaskHasPatientFactory):
    class Meta:
        model = Gds15

    id = factory.Sequence(lambda n: n)


class GMCPQFactory(TaskFactory):
    class Meta:
        model = GMCPQ

    id = factory.Sequence(lambda n: n)


class HadsFactory(TaskHasPatientFactory):
    class Meta:
        model = Hads

    id = factory.Sequence(lambda n: n)


class HadsRespondentFactory(TaskHasPatientFactory):
    class Meta:
        model = HadsRespondent

    id = factory.Sequence(lambda n: n)


class HamaFactory(TaskHasPatientFactory):
    class Meta:
        model = Hama

    id = factory.Sequence(lambda n: n)


class HamdFactory(TaskHasPatientFactory):
    class Meta:
        model = Hamd

    id = factory.Sequence(lambda n: n)


class Hamd7Factory(TaskHasPatientFactory):
    class Meta:
        model = Hamd7

    id = factory.Sequence(lambda n: n)


class HonosFactory(TaskHasPatientFactory):
    class Meta:
        model = Honos

    id = factory.Sequence(lambda n: n)


class Honos65Factory(TaskHasPatientFactory):
    class Meta:
        model = Honos65

    id = factory.Sequence(lambda n: n)


class HonoscaFactory(TaskHasPatientFactory):
    class Meta:
        model = Honosca

    id = factory.Sequence(lambda n: n)


class Icd10DepressiveFactory(TaskHasPatientFactory):
    class Meta:
        model = Icd10Depressive

    id = factory.Sequence(lambda n: n)


class Icd10ManicFactory(TaskHasPatientFactory):
    class Meta:
        model = Icd10Manic

    id = factory.Sequence(lambda n: n)


class Icd10MixedFactory(TaskHasPatientFactory):
    class Meta:
        model = Icd10Mixed

    id = factory.Sequence(lambda n: n)


class Icd10SchizophreniaFactory(TaskHasPatientFactory):
    class Meta:
        model = Icd10Schizophrenia

    id = factory.Sequence(lambda n: n)


class Icd10SchizotypalFactory(TaskHasPatientFactory):
    class Meta:
        model = Icd10Schizotypal

    id = factory.Sequence(lambda n: n)


class Icd10SpecPDFactory(TaskHasPatientFactory):
    class Meta:
        model = Icd10SpecPD

    id = factory.Sequence(lambda n: n)


class IDED3DFactory(TaskHasPatientFactory):
    class Meta:
        model = IDED3D

    id = factory.Sequence(lambda n: n)


class IesrFactory(TaskHasPatientFactory):
    class Meta:
        model = Iesr

    id = factory.Sequence(lambda n: n)


class IfsFactory(TaskHasPatientFactory):
    class Meta:
        model = Ifs

    id = factory.Sequence(lambda n: n)


class IracFactory(TaskHasPatientFactory):
    class Meta:
        model = Irac

    id = factory.Sequence(lambda n: n)


class Isaaq10Factory(TaskHasPatientFactory):
    class Meta:
        model = Isaaq10

    id = factory.Sequence(lambda n: n)


class IsaaqEdFactory(TaskHasPatientFactory):
    class Meta:
        model = IsaaqEd

    id = factory.Sequence(lambda n: n)


class KhandakerInsightMedicalFactory(TaskHasPatientFactory):
    class Meta:
        model = KhandakerInsightMedical

    id = factory.Sequence(lambda n: n)


class KhandakerMojoMedicalFactory(TaskHasPatientFactory):
    class Meta:
        model = KhandakerMojoMedical

    id = factory.Sequence(lambda n: n)


class KhandakerMojoSociodemographicsFactory(TaskHasPatientFactory):
    class Meta:
        model = KhandakerMojoSociodemographics

    id = factory.Sequence(lambda n: n)


class KirbyFactory(TaskHasPatientFactory):
    class Meta:
        model = Kirby

    id = factory.Sequence(lambda n: n)


class LynallIamMedicalHistoryFactory(TaskHasPatientFactory):
    class Meta:
        model = LynallIamMedicalHistory

    id = factory.Sequence(lambda n: n)


class LynallIamLifeEventsFactory(TaskHasPatientFactory):
    class Meta:
        model = LynallIamLifeEvents

    id = factory.Sequence(lambda n: n)


class MastFactory(TaskHasPatientFactory):
    class Meta:
        model = Mast

    id = factory.Sequence(lambda n: n)


class MdsUpdrsFactory(TaskHasPatientFactory):
    class Meta:
        model = MdsUpdrs

    id = factory.Sequence(lambda n: n)


class Mfi20Factory(TaskHasPatientFactory):
    class Meta:
        model = Mfi20

    id = factory.Sequence(lambda n: n)


class MiniAceFactory(TaskHasPatientFactory):
    class Meta:
        model = MiniAce

    id = factory.Sequence(lambda n: n)


class MocaFactory(TaskHasPatientFactory):
    class Meta:
        model = Moca

    id = factory.Sequence(lambda n: n)


class NartFactory(TaskHasPatientFactory):
    class Meta:
        model = Nart

    id = factory.Sequence(lambda n: n)


class NpiQFactory(TaskHasPatientFactory):
    class Meta:
        model = NpiQ

    id = factory.Sequence(lambda n: n)


class OrsFactory(TaskHasPatientFactory):
    class Meta:
        model = Ors

    id = factory.Sequence(lambda n: n)


class PanssFactory(TaskHasPatientFactory):
    class Meta:
        model = Panss

    id = factory.Sequence(lambda n: n)


class Paradise24Factory(TaskHasPatientFactory):
    class Meta:
        model = Paradise24

    id = factory.Sequence(lambda n: n)


class PbqFactory(TaskHasPatientFactory):
    class Meta:
        model = Pbq

    id = factory.Sequence(lambda n: n)


class Pcl5Factory(TaskHasPatientFactory):
    class Meta:
        model = Pcl5

    id = factory.Sequence(lambda n: n)


class PclCFactory(TaskHasPatientFactory):
    class Meta:
        model = PclC

    id = factory.Sequence(lambda n: n)


class PclMFactory(TaskHasPatientFactory):
    class Meta:
        model = PclM

    id = factory.Sequence(lambda n: n)


class PclSFactory(TaskHasPatientFactory):
    class Meta:
        model = PclS

    id = factory.Sequence(lambda n: n)


class PdssFactory(TaskHasPatientFactory):
    class Meta:
        model = Pdss

    id = factory.Sequence(lambda n: n)


class PhotoFactory(TaskHasPatientFactory):
    class Meta:
        model = Photo

    id = factory.Sequence(lambda n: n)

    @factory.post_generation
    def create_blob(
        obj: "Resolver", create: bool, extracted: None, **kwargs
    ) -> None:
        if not create:
            return

        obj.photo = BlobFactory.create(
            fieldname="photo_blobid",
            tablename="photo",
            tablepk=obj.id,
            **kwargs,
        )


class PhotoSequenceFactory(TaskHasPatientFactory):
    class Meta:
        model = PhotoSequence

    id = factory.Sequence(lambda n: n + 1)

    @factory.post_generation
    def photos(
        obj: "Resolver", create: bool, num_photos: int, **kwargs
    ) -> None:
        if not create:
            return

        if num_photos:
            PhotoSequenceSinglePhotoFactory.create_batch(
                size=num_photos,
                photosequence_id=obj.id,
                _device=obj._device,
                photo__patient=obj.patient,
            )


class PhotoSequenceSinglePhotoFactory(GenericTabletRecordFactory):
    class Meta:
        model = PhotoSequenceSinglePhoto

    id = factory.Sequence(lambda n: n + 1)
    seqnum = factory.Sequence(lambda n: n + 1)

    @factory.post_generation
    def photo(
        obj: "Resolver", create: bool, num_photos: int, **kwargs
    ) -> None:
        if not create:
            return

        patient = kwargs["patient"]
        obj.photo = PhotoFactory(patient=patient)


class Phq15Factory(TaskHasPatientFactory):
    class Meta:
        model = Phq15

    id = factory.Sequence(lambda n: n)


class Phq8Factory(TaskHasPatientFactory):
    class Meta:
        model = Phq8

    id = factory.Sequence(lambda n: n)


class ProgressNoteFactory(TaskHasPatientFactory):
    class Meta:
        model = ProgressNote

    id = factory.Sequence(lambda n: n)


class PswqFactory(TaskHasPatientFactory):
    class Meta:
        model = Pswq

    id = factory.Sequence(lambda n: n)


class PsychiatricClerkingFactory(TaskHasPatientFactory):
    class Meta:
        model = PsychiatricClerking

    id = factory.Sequence(lambda n: n)


class PatientSatisfactionFactory(TaskHasPatientFactory):
    class Meta:
        model = PatientSatisfaction

    id = factory.Sequence(lambda n: n)


class QolBasicFactory(TaskHasPatientFactory):
    class Meta:
        model = QolBasic

    id = factory.Sequence(lambda n: n)


class QolSGFactory(TaskHasPatientFactory):
    class Meta:
        model = QolSG

    id = factory.Sequence(lambda n: n)


class Rand36Factory(TaskHasPatientFactory):
    class Meta:
        model = Rand36

    id = factory.Sequence(lambda n: n)


class Rapid3Factory(TaskHasPatientFactory):
    class Meta:
        model = Rapid3

    id = factory.Sequence(lambda n: n)


class ReferrerSatisfactionGenFactory(TaskFactory):
    class Meta:
        model = ReferrerSatisfactionGen

    id = factory.Sequence(lambda n: n)


class ReferrerSatisfactionSpecFactory(TaskHasPatientFactory):
    class Meta:
        model = ReferrerSatisfactionSpec

    id = factory.Sequence(lambda n: n)


class Sfmpq2Factory(TaskHasPatientFactory):
    class Meta:
        model = Sfmpq2

    id = factory.Sequence(lambda n: n)


class ShapsFactory(TaskHasPatientFactory):
    class Meta:
        model = Shaps

    id = factory.Sequence(lambda n: n)


class SlumsFactory(TaskHasPatientFactory):
    class Meta:
        model = Slums

    id = factory.Sequence(lambda n: n)


class SmastFactory(TaskHasPatientFactory):
    class Meta:
        model = Smast

    id = factory.Sequence(lambda n: n)


class SrsFactory(TaskHasPatientFactory):
    class Meta:
        model = Srs

    id = factory.Sequence(lambda n: n)


class SuppspFactory(TaskHasPatientFactory):
    class Meta:
        model = Suppsp

    id = factory.Sequence(lambda n: n)


class SwemwbsFactory(TaskHasPatientFactory):
    class Meta:
        model = Swemwbs

    id = factory.Sequence(lambda n: n)


class WemwbsFactory(TaskHasPatientFactory):
    class Meta:
        model = Wemwbs

    id = factory.Sequence(lambda n: n)


class WsasFactory(TaskHasPatientFactory):
    class Meta:
        model = Wsas

    id = factory.Sequence(lambda n: n)


class YbocsFactory(TaskHasPatientFactory):
    class Meta:
        model = Ybocs

    id = factory.Sequence(lambda n: n)


class YbocsScFactory(TaskHasPatientFactory):
    class Meta:
        model = YbocsSc

    id = factory.Sequence(lambda n: n)


class Zbi12Factory(TaskHasPatientFactory):
    class Meta:
        model = Zbi12

    id = factory.Sequence(lambda n: n)
