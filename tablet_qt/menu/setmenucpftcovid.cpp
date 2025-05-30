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

#include "setmenucpftcovid.h"

#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasks/cpftcovidmedical.h"
#include "tasks/cpftresearchpreferences.h"

SetMenuCpftCovid::SetMenuCpftCovid(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETS_CLINICAL))
{
}

QString SetMenuCpftCovid::title() const
{
    return tr("CPFT Post-COVID-19 Clinic");
}

QString SetMenuCpftCovid::subtitle() const
{
    return tr(
        "Cambridgeshire and Peterborough NHS Foundation Trust, UK — "
        "post-COVID-19 clinic"
    );
}

void SetMenuCpftCovid::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_TASK_MENU_ITEM(
            CPFTResearchPreferences::CPFTRESEARCHPREFERENCES_TABLENAME, m_app
        ),
        MAKE_TASK_MENU_ITEM(
            CPFTCovidMedical::CPFTCOVIDMEDICAL_TABLENAME, m_app
        )};
}
