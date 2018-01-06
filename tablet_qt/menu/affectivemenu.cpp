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

#include "affectivemenu.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/bdi.h"
#include "tasks/cisr.h"
#include "tasks/gad7.h"
#include "tasks/gds15.h"
#include "tasks/hads.h"
#include "tasks/hama.h"
#include "tasks/hamd.h"
#include "tasks/hamd7.h"
#include "tasks/icd10depressive.h"
#include "tasks/icd10manic.h"
#include "tasks/icd10mixed.h"
#include "tasks/iesr.h"
#include "tasks/pclc.h"
#include "tasks/pclm.h"
#include "tasks/pcls.h"
#include "tasks/pdss.h"
#include "tasks/phq9.h"
#include "tasks/phq15.h"
#include "tasks/pswq.h"
#include "tasks/ybocs.h"
#include "tasks/ybocssc.h"


AffectiveMenu::AffectiveMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Affective (mood and anxiety) disorders"),
               uifunc::iconFilename(uiconst::ICON_AFFECTIVE))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("asrm", app),
        MAKE_TASK_MENU_ITEM(Bdi::BDI_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Cisr::CISR_TABLENAME, app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("epds", app),
        MAKE_TASK_MENU_ITEM(Gad7::GAD7_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Gds15::GDS15_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Hads::HADS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(HamA::HAMA_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(HamD::HAMD_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(HamD7::HAMD7_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Icd10Depressive::ICD10DEP_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Icd10Manic::ICD10MANIC_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Icd10Mixed::ICD10MIXED_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Iesr::IESR_TABLENAME, app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("madrs", app),
        MAKE_TASK_MENU_ITEM(PclM::PCLM_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(PclC::PCLC_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(PclS::PCLS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Pdss::PDSS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Phq9::PHQ9_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Phq15::PHQ15_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Pswq::PSWQ_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Ybocs::YBOCS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(YbocsSc::YBOCSSC_TABLENAME, app),
    };
}
