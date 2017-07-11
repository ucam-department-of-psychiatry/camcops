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

#define INCLUDE_CATATONIA_EXAMINATION

#include "catatoniaepsemenu.h"
#include "common/uiconst.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/aims.h"
#include "tasks/mdsupdrs.h"


CatatoniaEpseMenu::CatatoniaEpseMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Catatonia and extrapyramidal side effects"),
               uifunc::iconFilename(uiconst::ICON_CATATONIA))
{
    QString examtitle = tr("Catatonia examination technique");
    QString examsubtitle = tr("Standardized technique (for BFCRS, BFCSI)");
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM(Aims::AIMS_TABLENAME, app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("bars", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("bfcrs", app),
        MenuItem(examtitle,
                 HtmlMenuItem(examtitle,
                              filefunc::taskHtmlFilename("catatoniaexam")),
                 "",
                 examsubtitle),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("csi", app), // == bfcsi
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("gass", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("lunsers", app),
        MAKE_TASK_MENU_ITEM(MdsUpdrs::MDS_UPDRS_TABLENAME, app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("sas", app),
    };
}
