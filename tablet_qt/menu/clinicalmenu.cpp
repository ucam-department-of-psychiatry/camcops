/*
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
*/

#include "clinicalmenu.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/bmi.h"
#include "tasks/contactlog.h"
#include "tasks/cpftlpsdischarge.h"
#include "tasks/cpftlpsreferral.h"
#include "tasks/cpftlpsresetresponseclock.h"
#include "tasks/diagnosisicd10.h"
#include "tasks/fft.h"
#include "tasks/irac.h"
#include "tasks/patientsatisfaction.h"
#include "tasks/photo.h"
#include "tasks/photosequence.h"
#include "tasks/progressnote.h"
#include "tasks/psychiatricclerking.h"
#include "tasks/referrersatisfactionspec.h"


ClinicalMenu::ClinicalMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Clinical notes and logs"),
               uifunc::iconFilename(uiconst::ICON_CLINICAL))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM(Bmi::BMI_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(ContactLog::CONTACTLOG_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(CPFTLPSReferral::CPFTLPSREFERRAL_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(CPFTLPSResetResponseClock::CPFTLPSRESETCLOCK_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(CPFTLPSDischarge::CPFTLPSDISCHARGE_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(DiagnosisIcd10::DIAGNOSIS_ICD10_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Fft::FFT_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Irac::IRAC_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(PatientSatisfaction::PT_SATIS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Photo::PHOTO_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(PhotoSequence::PHOTOSEQUENCE_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(ProgressNote::PROGNOTE_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(PsychiatricClerking::PSYCLERK_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(ReferrerSatisfactionSpec::REF_SATIS_SPEC_TABLENAME, app),
    };
}
