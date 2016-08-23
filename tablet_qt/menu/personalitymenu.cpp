#include "personalitymenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


PersonalityMenu::PersonalityMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Personality"),
               UiFunc::iconFilename(UiConst::ICON_PERSONALITY))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("cecaq3", app),
        MAKE_TASK_MENU_ITEM("icd10specpd", app),
        MAKE_TASK_MENU_ITEM("icd10schizotypal", app),
    };
}
