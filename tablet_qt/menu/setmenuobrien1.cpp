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

#include "setmenuobrien1.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


SetMenuOBrien1::SetMenuOBrien1(CamcopsApp& app) :
    MenuWindow(app,
               tr("O’Brien JT — 1"),
               uifunc::iconFilename(uiconst::ICON_SETS_RESEARCH))
{
    m_subtitle = "O’Brien JT, University of Cambridge, UK — "
                 "dementia research clinic";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("ace3", app),
        MAKE_TASK_MENU_ITEM("badls", app),
        MAKE_TASK_MENU_ITEM("cbir", app),
        MAKE_TASK_MENU_ITEM("cope_brief", app),
        MAKE_TASK_MENU_ITEM("dad", app),
        MAKE_TASK_MENU_ITEM("demqol", app),
        MAKE_TASK_MENU_ITEM("demqolproxy", app),
        MAKE_TASK_MENU_ITEM("frs", app),
        MAKE_TASK_MENU_ITEM("hads", app),
        MAKE_TASK_MENU_ITEM("ifs", app),
        MAKE_TASK_MENU_ITEM("npiq", app),
        MAKE_TASK_MENU_ITEM("mds_updrs", app),
        MAKE_TASK_MENU_ITEM("zbi12", app),
    };
}
