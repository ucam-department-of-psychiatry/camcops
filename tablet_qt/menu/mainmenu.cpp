/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#include "mainmenu.h"
#include <QDebug>
#include <QSharedPointer>
#include "common/uiconst.h"
#include "core/networkmanager.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "menulib/menuproxy.h"

#include "menu/addictionmenu.h"
#include "menu/affectivemenu.h"
#include "menu/alltasksmenu.h"
#include "menu/anonymousmenu.h"
#include "menu/catatoniaepsemenu.h"
#include "menu/clinicalmenu.h"
#include "menu/clinicalsetsmenu.h"
#include "menu/cognitivemenu.h"
#include "menu/executivemenu.h"
#include "menu/globalmenu.h"
#include "menu/helpmenu.h"
#include "menu/patientsummarymenu.h"
#include "menu/personalitymenu.h"
#include "menu/psychosismenu.h"
#include "menu/researchmenu.h"
#include "menu/researchsetsmenu.h"
#include "menu/settingsmenu.h"


MainMenu::MainMenu(CamcopsApp& app)
    : MenuWindow(
          app,
          tr("CamCOPS: Cambridge Cognitive and Psychiatric Assessment Kit"),
          uifunc::iconFilename(uiconst::ICON_CAMCOPS),
          true)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_MENU_MENU_ITEM(PatientSummaryMenu, app),
        MenuItem(
            tr("Upload data to server"),
            std::bind(&MainMenu::upload, this),
            uifunc::iconFilename(uiconst::ICON_UPLOAD)
        ),
        MAKE_MENU_MENU_ITEM(HelpMenu, app),
        MAKE_MENU_MENU_ITEM(SettingsMenu, app),
        MAKE_MENU_MENU_ITEM(ClinicalMenu, app),
        MAKE_MENU_MENU_ITEM(GlobalMenu, app),
        MAKE_MENU_MENU_ITEM(CognitiveMenu, app),
        MAKE_MENU_MENU_ITEM(AffectiveMenu, app),
        MAKE_MENU_MENU_ITEM(AddictionMenu, app),
        MAKE_MENU_MENU_ITEM(PsychosisMenu, app),
        MAKE_MENU_MENU_ITEM(CatatoniaEpseMenu, app),
        MAKE_MENU_MENU_ITEM(PersonalityMenu, app),
        MAKE_MENU_MENU_ITEM(ExecutiveMenu, app),
        MAKE_MENU_MENU_ITEM(ResearchMenu, app),
        MAKE_MENU_MENU_ITEM(AnonymousMenu, app),
        MAKE_MENU_MENU_ITEM(ClinicalSetsMenu, app),
        MAKE_MENU_MENU_ITEM(ResearchSetsMenu, app),
        MAKE_MENU_MENU_ITEM(AllTasksMenu, app),
    };
    connect(&m_app, &CamcopsApp::fontSizeChanged,
            this, &MainMenu::reloadStyleSheet);
}


void MainMenu::upload()
{
    m_app.upload();
}
