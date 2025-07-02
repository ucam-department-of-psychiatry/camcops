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

#include "eatingdisordersmenu.h"

#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasks/bmi.h"
#include "tasks/cet.h"
#include "tasks/cia.h"
#include "tasks/edeq.h"
#include "tasks/empsa.h"

EatingDisordersMenu::EatingDisordersMenu(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_DOLPHIN))
{
    // Icon is a dolphin, per KI 2022-05-12, after the Maudsley Animal
    // Analogies and acceptance (KI reports) in the eating disorders community.
    // - https://thenewmaudsleyapproach.co.uk/index.php/research
    // - https://avedcaregiver.ca/wp-content/uploads/2018/12/Maudsley-Animal-Analogies.pdf
}

QString EatingDisordersMenu::title() const
{
    return tr("Eating disorders");
}

void EatingDisordersMenu::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_TASK_MENU_ITEM(Bmi::BMI_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Cet::CET_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Cia::CIA_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Edeq::EDEQ_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Empsa::EMPSA_TABLENAME, m_app),
    };
}
