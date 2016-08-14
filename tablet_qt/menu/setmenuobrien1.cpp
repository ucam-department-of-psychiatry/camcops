#include "setmenuobrien1.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


SetMenuOBrien1::SetMenuOBrien1(CamcopsApp& app) :
    MenuWindow(app, tr("O’Brien JT — 1"))
{
    m_subtitle = "O’Brien JT, University of Cambridge, UK — "
                 "dementia research clinic";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("ace3", app),
        MAKE_TASK_MENU_ITEM("badls", app),
        MAKE_TASK_MENU_ITEM("cbir", app),
        MAKE_TASK_MENU_ITEM("cope_brief", app),
        MAKE_TASK_MENU_ITEM("dad", app),
        MAKE_TASK_MENU_ITEM("demqol", app),
        MAKE_TASK_MENU_ITEM("demqolproxy", app),
        MAKE_TASK_MENU_ITEM("frs", app),
        MAKE_TASK_MENU_ITEM("hads", app),
        MAKE_TASK_MENU_ITEM("ifs", app),
        MAKE_TASK_MENU_ITEM("npiq", app),
        MAKE_TASK_MENU_ITEM("mds_updrs", app),
        MAKE_TASK_MENU_ITEM("zbi12", app),
    };
    buildMenu();
}
