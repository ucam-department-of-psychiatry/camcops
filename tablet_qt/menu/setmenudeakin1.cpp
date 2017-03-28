/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "setmenudeakin1.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


SetMenuDeakin1::SetMenuDeakin1(CamcopsApp& app) :
    MenuWindow(app,
               tr("Deakin JB — 1"),
               uifunc::iconFilename(uiconst::ICON_SETS_RESEARCH))
{
    m_subtitle = "Deakin JB, University of Cambridge, UK — "
                 "antibody-mediated psychosis";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("ace3", app),
        MAKE_TASK_MENU_ITEM("bdi", app),
        MAKE_TASK_MENU_ITEM("bmi", app),
        MAKE_TASK_MENU_ITEM("caps", app),
        MAKE_TASK_MENU_ITEM("cecaq3", app),
        MAKE_TASK_MENU_ITEM("cgisch", app),
        MAKE_TASK_MENU_ITEM("diagnosis_icd9cm", app),
        MAKE_TASK_MENU_ITEM("deakin_1_healthreview", app),
        MenuItem("*** soundtest for ExpDetThreshold/ExpDet"),
        MAKE_TASK_MENU_ITEM("cardinal_expdetthreshold", app),
        MAKE_TASK_MENU_ITEM("cardinal_expdet", app),
        MAKE_TASK_MENU_ITEM("gaf", app),
        MAKE_TASK_MENU_ITEM("nart", app),
        MAKE_TASK_MENU_ITEM("panss", app),
    };
}
