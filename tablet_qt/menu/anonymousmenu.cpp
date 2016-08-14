#include "anonymousmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


AnonymousMenu::AnonymousMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Anonymous questionnaires"), ICON_ANONYMOUS)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("gmcpq", app),
        MAKE_TASK_MENU_ITEM("ref_satis_gen", app),
    };
    buildMenu();
}
