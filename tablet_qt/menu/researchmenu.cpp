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

#include "researchmenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


ResearchMenu::ResearchMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Research tasks (experimental)"),
               uifunc::iconFilename(uiconst::ICON_RESEARCH))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("qolbasic", app),
        MAKE_TASK_MENU_ITEM("qolsg", app),
        MenuItem("*** soundtest for ExpDetThreshold/ExpDet"),
        MAKE_TASK_MENU_ITEM("cardinal_expdetthreshold", app),
        MAKE_TASK_MENU_ITEM("cardinal_expdet", app),
        MAKE_TASK_MENU_ITEM("diagnosis_icd9cm", app),
        MAKE_TASK_MENU_ITEM("ided3d", app),
        MenuItem("*** chain: qolbasic -> phq9 -> phq15"),
    };
}
