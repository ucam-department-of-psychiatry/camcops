#include "catatoniaepsemenu.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


CatatoniaEpseMenu::CatatoniaEpseMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Catatonia and extrapyramidal side effects"),
               ICON_CATATONIA)
{
    QString examtitle = tr("Catatonia examination technique");
    QString examsubtitle = tr("Standardized technique (for BFCRS, BFCSI)");
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("aims", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("bars", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("bfcrs", app),

        MenuItem(examtitle,
                 HtmlMenuItem(examtitle, taskHtmlFilename("catatoniaexam")),
                 "",
                 examsubtitle),
        // *** COPYRIGHT PROBLEM? CATATONIA EXAMINATION. GONE FROM UKPPG SITE. REMOVE ***

        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("csi", app), // == bfcsi
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("gass", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("lunsers", app),
        MAKE_TASK_MENU_ITEM("updrs", app),
        // PERMISSION REFUSED: MAKE_TASK_MENU_ITEM("sas", app),
    };
}
