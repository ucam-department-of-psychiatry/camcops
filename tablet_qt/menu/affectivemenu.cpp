#include "affectivemenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


AffectiveMenu::AffectiveMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Affective (mood and anxiety) disorders"),
               UiFunc::iconFilename(UiConst::ICON_AFFECTIVE))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("asrm", app),
        MAKE_TASK_MENU_ITEM("bdi", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("epds", app),
        MAKE_TASK_MENU_ITEM("gad7", app),
        MAKE_TASK_MENU_ITEM("gds15", app),
        MAKE_TASK_MENU_ITEM("hads", app),
        MAKE_TASK_MENU_ITEM("hama", app),
        MAKE_TASK_MENU_ITEM("hamd", app),
        MAKE_TASK_MENU_ITEM("hamd7", app),
        MAKE_TASK_MENU_ITEM("icd10depressive", app),
        MAKE_TASK_MENU_ITEM("icd10manic", app),
        MAKE_TASK_MENU_ITEM("icd10mixed", app),
        MAKE_TASK_MENU_ITEM("iesr", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("madrs", app),
        MAKE_TASK_MENU_ITEM("pclm", app),
        MAKE_TASK_MENU_ITEM("pclc", app),
        MAKE_TASK_MENU_ITEM("pcls", app),
        MAKE_TASK_MENU_ITEM("pdss", app),
        MAKE_TASK_MENU_ITEM("phq9", app),
        MAKE_TASK_MENU_ITEM("phq15", app),
        MAKE_TASK_MENU_ITEM("pswq", app),
        MAKE_TASK_MENU_ITEM("ybocs", app),
        MAKE_TASK_MENU_ITEM("ybocssc", app),
    };
}
