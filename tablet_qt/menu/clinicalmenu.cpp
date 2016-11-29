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

#include "clinicalmenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


ClinicalMenu::ClinicalMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Clinical notes and logs"),
               UiFunc::iconFilename(UiConst::ICON_CLINICAL))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("bmi", app),
        MAKE_TASK_MENU_ITEM("contactlog", app),
        MAKE_TASK_MENU_ITEM("cpft_lps_referral", app),
        MAKE_TASK_MENU_ITEM("cpft_lps_resetresponseclock", app),
        MAKE_TASK_MENU_ITEM("cpft_lps_discharge", app),
        MAKE_TASK_MENU_ITEM("diagnosis_icd10", app),
        MAKE_TASK_MENU_ITEM("fft", app),
        MAKE_TASK_MENU_ITEM("irac", app),
        MAKE_TASK_MENU_ITEM("pt_satis", app),
        MAKE_TASK_MENU_ITEM("photo", app),
        MAKE_TASK_MENU_ITEM("photosequence", app),
        MAKE_TASK_MENU_ITEM("progressnote", app),
        MAKE_TASK_MENU_ITEM("psychiatricclerking", app),
        MAKE_TASK_MENU_ITEM("ref_satis_spec", app),
    };
}
