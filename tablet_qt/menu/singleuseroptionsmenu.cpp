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

#include "singleuseroptionsmenu.h"

#include "common/urlconst.h"
#include "lib/uifunc.h"
#include "menu/singleuseradvancedmenu.h"
#include "menulib/fontsizewindow.h"

SingleUserOptionsMenu::SingleUserOptionsMenu(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETTINGS))
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
            )
                .setNotIfLocked()
        );
    }

    m_items.append(
        {MenuItem(
             tr("Choose language"),
             std::bind(&SingleUserOptionsMenu::chooseLanguage, this),
             uifunc::iconFilename(uiconst::CBS_LANGUAGE)
         ),
         MenuItem(
             tr("Online CamCOPS documentation"),
             UrlMenuItem(urlconst::CAMCOPS_URL),
             uifunc::iconFilename(uiconst::ICON_INFO)
         ),
         MenuItem(
             tr("Questionnaire font size"),
             MenuItem::OpenableWidgetMaker(std::bind(
                 &SingleUserOptionsMenu::setQuestionnaireFontSize,
                 this,
                 std::placeholders::_1
             ))
         ),
         MenuItem(
             tr("Re-register me"),
             std::bind(&SingleUserOptionsMenu::registerPatient, this)
         )
             .setNotIfLocked(),
         MAKE_MENU_MENU_ITEM(SingleUserAdvancedMenu, m_app)}
    );
}

void SingleUserOptionsMenu::registerPatient()
{
    m_app.registerPatientWithServer();
}

void SingleUserOptionsMenu::updateTaskSchedules()
{
    m_app.updateTaskSchedules();
}

void SingleUserOptionsMenu::chooseLanguage()
{
    uifunc::chooseLanguage(m_app, this);
}

OpenableWidget* SingleUserOptionsMenu::setQuestionnaireFontSize(CamcopsApp& app
)
{
    auto window = new FontSizeWindow(app);

    return window->editor();
}
