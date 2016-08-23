#include "cognitivemenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


CognitiveMenu::CognitiveMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Cognitive assessment"),
               UiFunc::iconFilename(UiConst::ICON_COGNITIVE))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("ace3", app),
        MAKE_TASK_MENU_ITEM("moca", app),
        MAKE_TASK_MENU_ITEM("slums", app),
        MAKE_TASK_MENU_ITEM("nart", app),
    };
}
