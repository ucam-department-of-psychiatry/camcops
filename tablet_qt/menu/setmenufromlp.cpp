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

#include "setmenufromlp.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


SetMenuFromLp::SetMenuFromLp(CamcopsApp& app) :
    MenuWindow(app, tr("FROM-LP"))
{
    m_subtitle = "Framework for Routine Outcome Measurement in Liaison "
                 "Psychiatry (FROM-LP)";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MenuItem(tr("GENERIC SCALES")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM("cgi_i", app),
        // CORE-10 -- copyright conditions prohibit
        MAKE_TASK_MENU_ITEM("irac", app),
        MAKE_TASK_MENU_ITEM("pt_satis", app),
        MAKE_TASK_MENU_ITEM("fft", app),
        MAKE_TASK_MENU_ITEM("ref_satis_gen", app),
        MAKE_TASK_MENU_ITEM("ref_satis_spec", app),

        MenuItem(tr("DISEASE-SPECIFIC SCALES")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM("ace3", app),
        MAKE_TASK_MENU_ITEM("phq9", app),
        // EPDS -- Royal College not currently permitting use
        MAKE_TASK_MENU_ITEM("gad7", app),
        MAKE_TASK_MENU_ITEM("honos", app),
        MAKE_TASK_MENU_ITEM("audit_c", app),
        MAKE_TASK_MENU_ITEM("bmi", app),
        // *** EQ-5D-5L, if permitted?
    };
}
