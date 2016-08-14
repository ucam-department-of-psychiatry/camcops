#include "psychosismenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


PsychosisMenu::PsychosisMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Psychosis"), ICON_PSYCHOSIS)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("cape42", app),
        MAKE_TASK_MENU_ITEM("caps", app),
        MAKE_TASK_MENU_ITEM("cgisch", app),
        MAKE_TASK_MENU_ITEM("panss", app),
        MAKE_TASK_MENU_ITEM("icd10schizophrenia", app),
        MAKE_TASK_MENU_ITEM("icd10schizotypal", app),
    };
    buildMenu();
}
