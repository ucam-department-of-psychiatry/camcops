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

#include "addictionmenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


AddictionMenu::AddictionMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Drug/alcohol abuse and addiction"),
               uifunc::iconFilename(uiconst::ICON_ADDICTION))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("audit", app),
        MAKE_TASK_MENU_ITEM("audit_c", app),
        MAKE_TASK_MENU_ITEM("cage", app),
        MAKE_TASK_MENU_ITEM("ciwa", app),
        MAKE_TASK_MENU_ITEM("dast", app),
        MAKE_TASK_MENU_ITEM("fast", app),
        MAKE_TASK_MENU_ITEM("mast", app),
        MAKE_TASK_MENU_ITEM("smast", app),
    };
}
