#include "clinicalsetsmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "menu/setmenucpftaffective1.h"
#include "menu/setmenufromlp.h"


ClinicalSetsMenu::ClinicalSetsMenu(CamcopsApp& app) :
    MenuWindow(app,
               tr("Sets of tasks collected together for clinical purposes"),
               ICON_SETS_CLINICAL)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_MENU_MENU_ITEM(SetMenuCpftAffective1, app),
        MAKE_MENU_MENU_ITEM(SetMenuFromLp, app),
    };
    buildMenu();
}
