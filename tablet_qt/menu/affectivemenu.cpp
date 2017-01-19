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

#include "affectivemenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


AffectiveMenu::AffectiveMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Affective (mood and anxiety) disorders"),
               uifunc::iconFilename(uiconst::ICON_AFFECTIVE))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("asrm", app),
        MAKE_TASK_MENU_ITEM("bdi", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("epds", app),
        MAKE_TASK_MENU_ITEM("gad7", app),
        MAKE_TASK_MENU_ITEM("gds15", app),
        MAKE_TASK_MENU_ITEM("hads", app),
        MAKE_TASK_MENU_ITEM("hama", app),
        MAKE_TASK_MENU_ITEM("hamd", app),
        MAKE_TASK_MENU_ITEM("hamd7", app),
        MAKE_TASK_MENU_ITEM("icd10depressive", app),
        MAKE_TASK_MENU_ITEM("icd10manic", app),
        MAKE_TASK_MENU_ITEM("icd10mixed", app),
        MAKE_TASK_MENU_ITEM("iesr", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("madrs", app),
        MAKE_TASK_MENU_ITEM("pclm", app),
        MAKE_TASK_MENU_ITEM("pclc", app),
        MAKE_TASK_MENU_ITEM("pcls", app),
        MAKE_TASK_MENU_ITEM("pdss", app),
        MAKE_TASK_MENU_ITEM("phq9", app),
        MAKE_TASK_MENU_ITEM("phq15", app),
        MAKE_TASK_MENU_ITEM("pswq", app),
        MAKE_TASK_MENU_ITEM("ybocs", app),
        MAKE_TASK_MENU_ITEM("ybocssc", app),
    };
}
