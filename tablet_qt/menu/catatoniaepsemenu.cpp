/*
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

#include "catatoniaepsemenu.h"
#include "common/uiconstants.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


CatatoniaEpseMenu::CatatoniaEpseMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Catatonia and extrapyramidal side effects"),
               UiFunc::iconFilename(UiConst::ICON_CATATONIA))
{
    QString examtitle = tr("Catatonia examination technique");
    QString examsubtitle = tr("Standardized technique (for BFCRS, BFCSI)");
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("aims", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("bars", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("bfcrs", app),

        MenuItem(examtitle,
                 HtmlMenuItem(examtitle,
                              FileFunc::taskHtmlFilename("catatoniaexam")),
                 "",
                 examsubtitle),
        // *** COPYRIGHT PROBLEM? CATATONIA EXAMINATION. GONE FROM UKPPG SITE. REMOVE ***

        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("csi", app), // == bfcsi
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("gass", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("lunsers", app),
        MAKE_TASK_MENU_ITEM("updrs", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("sas", app),
    };
}
