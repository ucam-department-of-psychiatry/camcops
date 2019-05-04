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

#include "setmenuobrien1.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/ace3.h"
#include "tasks/badls.h"
#include "tasks/cbir.h"
#include "tasks/copebrief.h"
#include "tasks/dad.h"
#include "tasks/demqol.h"
#include "tasks/demqolproxy.h"
#include "tasks/frs.h"
#include "tasks/hads.h"
#include "tasks/hadsrespondent.h"
#include "tasks/ifs.h"
#include "tasks/mdsupdrs.h"
#include "tasks/npiq.h"
#include "tasks/zbi12.h"


SetMenuOBrien1::SetMenuOBrien1(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETS_RESEARCH))
{
}


QString SetMenuOBrien1::title() const
{
    return "O’Brien JT — 1";
}


QString SetMenuOBrien1::subtitle() const
{
    return tr("O’Brien JT, University of Cambridge, UK — "
              "dementia research clinic");
}


void SetMenuOBrien1::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_TASK_MENU_ITEM(Ace3::ACE3_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Badls::BADLS_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(CbiR::CBIR_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(CopeBrief::COPEBRIEF_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Dad::DAD_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Demqol::DEMQOL_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(DemqolProxy::DEMQOLPROXY_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Frs::FRS_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Hads::HADS_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(HadsRespondent::HADSRESPONDENT_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Ifs::IFS_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(NpiQ::NPIQ_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(MdsUpdrs::MDS_UPDRS_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Zbi12::ZBI12_TABLENAME, m_app),
    };
}
