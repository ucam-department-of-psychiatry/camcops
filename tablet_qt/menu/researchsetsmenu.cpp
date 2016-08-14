#include "researchsetsmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "menu/setmenudeakin1.h"
#include "menu/setmenuobrien1.h"


ResearchSetsMenu::ResearchSetsMenu(CamcopsApp& app) :
    MenuWindow(app,
               tr("Sets of tasks collected together for research purposes"),
               ICON_SETS_RESEARCH)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_MENU_MENU_ITEM(SetMenuDeakin1, app),
        MAKE_MENU_MENU_ITEM(SetMenuOBrien1, app),
    };
    buildMenu();
}
