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

#include "setmenucpftpsychooncology1.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/pcl5.h"


SetMenuCpftPsychooncology1::SetMenuCpftPsychooncology1(CamcopsApp& app) :
    MenuWindow(app,
               tr("CPFT Psycho-oncology Service"),
               uifunc::iconFilename(uiconst::ICON_SETS_CLINICAL))
{
    m_subtitle = "Cambridgeshire and Peterborough NHS Foundation Trust, UK — "
                 "psycho-oncology service";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM(Pcl5::PCL5_TABLENAME, app),
    };
}
