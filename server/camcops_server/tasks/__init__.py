#!/usr/bin/env python
# camcops_server/tasks/__init__.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

from .ace3 import Ace3
from .aims import Aims
from .audit import Audit, AuditC
from .badls import Badls
from .bdi import Bdi
from .bmi import Bmi
from .bprs import Bprs
from .bprse import Bprse
from .cage import Cage
from .cape42 import Cape42
from .caps import Caps
from .cardinal_expdetthreshold import CardinalExpDetThreshold
from .cardinal_expectationdetection import CardinalExpectationDetection
from .cbir import CbiR
from .ceca import CecaQ3
from .cgi_task import Cgi
from .cgisch import CgiSch
from .cisr import Cisr
from .ciwa import Ciwa
from .contactlog import ContactLog
from .cope import CopeBrief
from .cpft_lps import (
    CPFTLPSReferral,
    CPFTLPSResetResponseClock,
    CPFTLPSDischarge,
)
from .dad import Dad
from .dast import Dast
from .deakin_1_healthreview import Deakin1HealthReview
from .demoquestionnaire import DemoQuestionnaire
from .demqol import Demqol
from .diagnosis import DiagnosisIcd9CM, DiagnosisIcd10
from .distressthermometer import DistressThermometer
from .fast import Fast
from .fft import Fft
from .frs import Frs
from .gad7 import Gad7
from .gaf import Gaf
from .gds import Gds15
from .gmcpq import GMCPQ
from .hads import Hads
from .hama import Hama
from .hamd import Hamd
from .hamd7 import Hamd7
from .honos import Honos, Honos65, Honosca
from .icd10depressive import Icd10Depressive
from .icd10manic import Icd10Manic
from .icd10mixed import Icd10Mixed
from .icd10schizophrenia import Icd10Schizophrenia
from .icd10schizotypal import Icd10Schizotypal
from .icd10specpd import Icd10SpecPD
from .ided3d import IDED3D
from .iesr import Iesr
from .ifs import Ifs
from .irac import Irac
from .khandaker_1_medicalhistory import Khandaker1MedicalHistory
from .mast import Mast
from .mds_updrs import MdsUpdrs
from .moca import Moca
from .nart import Nart
from .npiq import NpiQ
from .panss import Panss
from .pcl import PclC, PclM, PclS
from .pdss import Pdss
from .photo import Photo, PhotoSequence
from .phq9 import Phq9
from .phq15 import Phq15
from .progressnote import ProgressNote
from .pswq import Pswq
from .psychiatricclerking import PsychiatricClerking
from .qolbasic import QolBasic
from .qolsg import QolSG
from .rand36 import Rand36
from .service_satisfaction import (
    PatientSatisfaction,
    ReferrerSatisfactionGen,
    ReferrerSatisfactionSpec,
)
from .slums import Slums
from .smast import Smast
from .wemwbs import Swemwbs, Wemwbs
from .wsas import Wsas
from .ybocs import Ybocs, YbocsSc
from .zbi import Zbi12
