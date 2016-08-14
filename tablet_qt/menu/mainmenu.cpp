#include "mainmenu.h"
#include <QDebug>
#include <QSharedPointer>
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
          ICON_CAMCOPS,
          true)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_MENU_MENU_ITEM(PatientSummaryMenu, app),
        MenuItem(tr("Upload data to server")),  // *** + ICON_UPLOAD
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

    buildMenu();
}
