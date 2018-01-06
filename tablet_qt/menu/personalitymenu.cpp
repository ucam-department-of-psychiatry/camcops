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

#include "personalitymenu.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/cecaq3.h"
#include "tasks/icd10schizotypal.h"
#include "tasks/icd10specpd.h"


PersonalityMenu::PersonalityMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Personality"),
               uifunc::iconFilename(uiconst::ICON_PERSONALITY))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM(CecaQ3::CECAQ3_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Icd10SpecPD::ICD10SPECPD_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Icd10Schizotypal::ICD10SZTYPAL_TABLENAME, app),
    };
}
