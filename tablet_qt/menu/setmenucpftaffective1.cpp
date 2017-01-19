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

#include "setmenucpftaffective1.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


SetMenuCpftAffective1::SetMenuCpftAffective1(CamcopsApp& app) :
    MenuWindow(app, tr("CPFT Affective Disorders Research Database — 1"))
{
    m_subtitle = "Cambridgeshire and Peterborough NHS Foundation Trust, UK — "
                 "affective disorders";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("diagnosis_icd9cm", app),  // = DSM-IV
        MAKE_TASK_MENU_ITEM("hamd", app),
        MAKE_TASK_MENU_ITEM("iesr", app),
        MAKE_TASK_MENU_ITEM("pdss", app),
        MAKE_TASK_MENU_ITEM("pswq", app),
        MAKE_TASK_MENU_ITEM("swemwbs", app),
        MAKE_TASK_MENU_ITEM("wsas", app),
        MAKE_TASK_MENU_ITEM("ybocs", app),
        MAKE_TASK_MENU_ITEM("ybocssc", app),
    };
}
