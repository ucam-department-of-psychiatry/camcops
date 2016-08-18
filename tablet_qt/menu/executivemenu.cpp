#include "executivemenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


ExecutiveMenu::ExecutiveMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Executive functioning"),
               ICON_EXECUTIVE)
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("ifs", app),
    };
}
