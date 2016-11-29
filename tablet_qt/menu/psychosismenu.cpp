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

#include "psychosismenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


PsychosisMenu::PsychosisMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Psychosis"),
               UiFunc::iconFilename(UiConst::ICON_PSYCHOSIS))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("cape42", app),
        MAKE_TASK_MENU_ITEM("caps", app),
        MAKE_TASK_MENU_ITEM("cgisch", app),
        MAKE_TASK_MENU_ITEM("panss", app),
        MAKE_TASK_MENU_ITEM("icd10schizophrenia", app),
        MAKE_TASK_MENU_ITEM("icd10schizotypal", app),
    };
}
