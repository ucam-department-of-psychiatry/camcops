/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "setmenucpftadulteatingdisorders.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/chit.h"
#include "tasks/eq5d5l.h"
#include "tasks/gad7.h"
#include "tasks/gbogras.h"
#include "tasks/gbogres.h"
#include "tasks/gbogpc.h"
#include "tasks/phq9.h"
#include "tasks/suppsp.h"
#include "tasks/swemwbs.h"


SetMenuCpftAdultEatingDisorders::SetMenuCpftAdultEatingDisorders(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETS_CLINICAL))
{
}


QString SetMenuCpftAdultEatingDisorders::title() const
{
    return tr("CPFT Adult Eating Disorders Service");
}


QString SetMenuCpftAdultEatingDisorders::subtitle() const
{
    return tr("Cambridgeshire and Peterborough NHS Foundation Trust, UK — "
              "adult eating disorders service");
}


void SetMenuCpftAdultEatingDisorders::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MenuItem(tr("Generic measures")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(Chit::CHIT_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Eq5d5l::EQ5D5L_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Suppsp::SUPPSP_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Swemwbs::SWEMWBS_TABLENAME, m_app),

        MenuItem(tr("Specific conditions")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(Gad7::GAD7_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Phq9::PHQ9_TABLENAME, m_app),
        // todo:: CIA
        // todo:: EDE-Q
        // todo:: ISAAQ

        MenuItem(tr("Treatment/care")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(GboGReS::GBOGRES_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(GboGPC::GBOGPC_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(GboGRaS::GBOGRAS_TABLENAME, m_app),
    };
}
