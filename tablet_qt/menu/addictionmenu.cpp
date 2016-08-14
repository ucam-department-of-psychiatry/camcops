#include "addictionmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


AddictionMenu::AddictionMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Drug/alcohol abuse and addiction"), ICON_ADDICTION)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("audit", app),
        MAKE_TASK_MENU_ITEM("audit_c", app),
        MAKE_TASK_MENU_ITEM("cage", app),
        MAKE_TASK_MENU_ITEM("ciwa", app),
        MAKE_TASK_MENU_ITEM("dast", app),
        MAKE_TASK_MENU_ITEM("fast", app),
        MAKE_TASK_MENU_ITEM("mast", app),
        MAKE_TASK_MENU_ITEM("smast", app),
    };
    buildMenu();
}
