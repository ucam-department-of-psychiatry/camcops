#include "anonymousmenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


AnonymousMenu::AnonymousMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Anonymous questionnaires"),
               UiFunc::iconFilename(UiConst::ICON_ANONYMOUS))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("gmcpq", app),
        MAKE_TASK_MENU_ITEM("ref_satis_gen", app),
    };
}
