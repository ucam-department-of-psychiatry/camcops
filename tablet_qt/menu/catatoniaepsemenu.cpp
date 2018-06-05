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

// #define INCLUDE_CATATONIA_EXAMINATION

#include "catatoniaepsemenu.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#ifdef INCLUDE_CATATONIA_EXAMINATION
#include "common/urlconst.h"
#endif

#include "tasks/aims.h"
#include "tasks/mdsupdrs.h"


CatatoniaEpseMenu::CatatoniaEpseMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Catatonia and extrapyramidal side effects"),
               uifunc::iconFilename(uiconst::ICON_CATATONIA))
{
#ifdef INCLUDE_CATATONIA_EXAMINATION
    const QString examtitle = tr("Catatonia examination technique");
    const QString examsubtitle = tr("Standardized technique (for BFCRS, BFCSI)");
#endif
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM(Aims::AIMS_TABLENAME, app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("bars", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("bfcrs", app),
#ifdef INCLUDE_CATATONIA_EXAMINATION
        MenuItem(examtitle,
                 HtmlMenuItem(examtitle,
                              urlconst::taskDocUrl("catatoniaexam")),
                 "",
                 examsubtitle),
#endif
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("csi", app), // == bfcsi
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("gass", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("lunsers", app),
        MAKE_TASK_MENU_ITEM(MdsUpdrs::MDS_UPDRS_TABLENAME, app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("sas", app),
    };
}
