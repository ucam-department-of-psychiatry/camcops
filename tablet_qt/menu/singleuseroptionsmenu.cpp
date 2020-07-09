/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include "singleuseroptionsmenu.h"
#include "lib/uifunc.h"

SingleUserOptionsMenu::SingleUserOptionsMenu(CamcopsApp& app)
    : MenuWindow(
          app,
          uifunc::iconFilename(uiconst::ICON_SETTINGS)
    )
{
}


QString SingleUserOptionsMenu::title() const
{
    return tr("Options");
}


void SingleUserOptionsMenu::makeItems()
{
    m_items = {MenuItem(tr("Options")).setLabelOnly()};

    if (!m_app.needToRegisterSinglePatient()) {
        m_items.append(
            MenuItem(
                tr("Get updates to my schedules"),
                std::bind(&SingleUserOptionsMenu::updateTaskSchedules, this)
            ).setNotIfLocked()
        );
    }

    m_items.append({
        MenuItem(
            tr("Change operating mode"),
            std::bind(&SingleUserOptionsMenu::changeMode, this)
        ).setNotIfLocked(),
        MenuItem(
            tr("Re-register me"),
            std::bind(&SingleUserOptionsMenu::registerPatient, this)
            ).setNotIfLocked(),
    });
}


void SingleUserOptionsMenu::changeMode()
{
    m_app.setModeFromUser();
}


void SingleUserOptionsMenu::registerPatient()
{
    m_app.registerPatientWithServer();
}


void SingleUserOptionsMenu::updateTaskSchedules()
{
    m_app.updateTaskSchedules();
}
