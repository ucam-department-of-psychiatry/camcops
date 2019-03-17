/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#include "setmenucpftperinatal1.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/apeqpt.h"
#include "tasks/core10.h"
#include "tasks/gad7.h"
#include "tasks/gbogras.h"
#include "tasks/gbogres.h"
#include "tasks/gbogpc.h"
#include "tasks/honos.h"
#include "tasks/perinatalpoem.h"
#include "tasks/ors.h"
#include "tasks/srs.h"


SetMenuCpftPerinatal1::SetMenuCpftPerinatal1(CamcopsApp& app) :
    MenuWindow(app,
               tr("CPFT Perinatal Service"),
               uifunc::iconFilename(uiconst::ICON_SETS_CLINICAL))
{
    m_subtitle = "Cambridgeshire and Peterborough NHS Foundation Trust, UK — "
                 "perinatal psychiatry service";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM(Apeqpt::APEQPT_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Core10::CORE10_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Gad7::GAD7_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(GboGReS::GBOGRES_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(GboGPC::GBOGPC_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(GboGRaS::GBOGRAS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Honos::HONOS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(PerinatalPoem::PERINATAL_POEM_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Ors::ORS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Srs::SRS_TABLENAME, app),
    };
}
