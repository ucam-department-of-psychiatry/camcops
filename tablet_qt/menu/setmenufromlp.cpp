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

#include "setmenufromlp.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/ace3.h"
#include "tasks/auditc.h"
#include "tasks/bmi.h"
#include "tasks/cgii.h"
#include "tasks/fft.h"
#include "tasks/gad7.h"
#include "tasks/honos.h"
#include "tasks/irac.h"
#include "tasks/patientsatisfaction.h"
#include "tasks/phq9.h"
#include "tasks/referrersatisfactiongen.h"
#include "tasks/referrersatisfactionspec.h"


SetMenuFromLp::SetMenuFromLp(CamcopsApp& app) :
    MenuWindow(app,
               tr("FROM-LP"),
               uifunc::iconFilename(uiconst::ICON_SETS_CLINICAL))
{
    m_subtitle = "Framework for Routine Outcome Measurement in Liaison "
                 "Psychiatry (FROM-LP)";
    m_items = {
        MAKE_CHANGE_PATIENT(app),

        MenuItem(tr("GENERIC SCALES")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(CgiI::CGI_I_TABLENAME, app),
        // CORE-10 -- copyright conditions prohibit
        MAKE_TASK_MENU_ITEM(Fft::FFT_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Irac::IRAC_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(PatientSatisfaction::PT_SATIS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(ReferrerSatisfactionGen::REF_SATIS_GEN_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(ReferrerSatisfactionSpec::REF_SATIS_SPEC_TABLENAME, app),

        MenuItem(tr("DISEASE-SPECIFIC SCALES")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(Ace3::ACE3_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(AuditC::AUDITC_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Bmi::BMI_TABLENAME, app),
        // EPDS -- Royal College not currently permitting use
        MAKE_TASK_MENU_ITEM(Gad7::GAD7_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Honos::HONOS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Phq9::PHQ9_TABLENAME, app),
        // *** EQ-5D-5L, if permitted?
    };
}
