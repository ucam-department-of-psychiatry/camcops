#include "researchmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


ResearchMenu::ResearchMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Research tasks (experimental)"), ICON_RESEARCH)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("qolbasic", app),
        MAKE_TASK_MENU_ITEM("qolsg", app),
        MenuItem("*** soundtest for ExpDetThreshold/ExpDet"),
        MAKE_TASK_MENU_ITEM("cardinal_expdetthreshold", app),
        MAKE_TASK_MENU_ITEM("cardinal_expdet", app),
        MAKE_TASK_MENU_ITEM("diagnosis_icd9cm", app),
        MAKE_TASK_MENU_ITEM("ided3d", app),
        MenuItem("*** chain: qolbasic -> phq9 -> phq15"),
    };
    buildMenu();
}
