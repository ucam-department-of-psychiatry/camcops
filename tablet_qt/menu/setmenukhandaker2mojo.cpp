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

#include "setmenukhandaker2mojo.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/asdas.h"
#include "tasks/chit.h"
#include "tasks/cisr.h"
#include "tasks/das28.h"
#include "tasks/elixhauserci.h"
#include "tasks/eq5d5l.h"
#include "tasks/esspri.h"
#include "tasks/mfi20.h"
#include "tasks/sfmpq2.h"
#include "tasks/suppsp.h"


SetMenuKhandaker2Mojo::SetMenuKhandaker2Mojo(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETS_RESEARCH))
{
}


QString SetMenuKhandaker2Mojo::title() const
{
    return tr("Khandaker GM — 2 — MOJO study");
}


QString SetMenuKhandaker2Mojo::subtitle() const
{
    return tr("Khandaker GM, University of Cambridge, UK — "
              "MOJO immunopsychiatry study");
}


void SetMenuKhandaker2Mojo::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        // *** MOJO anthropometrics/sociodemographics/medical history
        MAKE_TASK_MENU_ITEM(ElixhauserCI::ELIXHAUSERCI_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Esspri::ESSPRI_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Asdas::ASDAS_TABLENAME, m_app),
        // *** Snaith-Hamilton Pleasure Scale (SHAPS)
        MAKE_TASK_MENU_ITEM(Mfi20::MFI20_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Sfmpq2::SFMPQ2_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Das28::DAS28_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Chit::CHIT_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Suppsp::SUPPSP_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Cisr::CISR_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Eq5d5l::EQ5D5L_TABLENAME, m_app),
    };
}
