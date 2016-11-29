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

#include "globalmenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


GlobalMenu::GlobalMenu(CamcopsApp& app) :
    MenuWindow(app,
               tr("Global function and multiple aspects of psychopathology"),
               UiFunc::iconFilename(UiConst::ICON_GLOBAL))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("badls", app),
        MAKE_TASK_MENU_ITEM("bprs", app),
        MAKE_TASK_MENU_ITEM("bprse", app),
        MAKE_TASK_MENU_ITEM("cbir", app),
        MAKE_TASK_MENU_ITEM("cgi", app),
        MAKE_TASK_MENU_ITEM("cgi_i", app),
        MAKE_TASK_MENU_ITEM("cope_brief", app),
        MAKE_TASK_MENU_ITEM("dad", app),
        MAKE_TASK_MENU_ITEM("demqol", app),
        MAKE_TASK_MENU_ITEM("demqolproxy", app),
        MAKE_TASK_MENU_ITEM("distressthermometer", app),
        MAKE_TASK_MENU_ITEM("frs", app),
        MAKE_TASK_MENU_ITEM("gaf", app),
        MAKE_TASK_MENU_ITEM("honos", app),
        MAKE_TASK_MENU_ITEM("honos65", app),
        MAKE_TASK_MENU_ITEM("honosca", app),
        MAKE_TASK_MENU_ITEM("npiq", app),
        MAKE_TASK_MENU_ITEM("rand36", app),
        MAKE_TASK_MENU_ITEM("swemwbs", app),
        MAKE_TASK_MENU_ITEM("wemwbs", app),
        MAKE_TASK_MENU_ITEM("wsas", app),
        MAKE_TASK_MENU_ITEM("zbi12", app),
    };
}
