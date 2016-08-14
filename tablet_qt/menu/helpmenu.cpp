#include "helpmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


HelpMenu::HelpMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Help"), ICON_INFO)
{
    m_items = {
        MenuItem(tr("Online CamCOPS documentation")),  // ***
        MenuItem(tr("Visit http://camcops.org")),  // ***
        MAKE_TASK_MENU_ITEM("demoquestionnaire", app),
        MenuItem(tr("Why isn’t task X here?")),  // ***
        MenuItem(tr("Show software versions")),  // ***
        MenuItem(tr("View device (installation) ID")),  // ***
        MenuItem(tr("View terms and conditions of use")),  // ***
    };
    buildMenu();
}
