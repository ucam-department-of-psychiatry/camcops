#include "setmenucpftaffective1.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


SetMenuCpftAffective1::SetMenuCpftAffective1(CamcopsApp& app) :
    MenuWindow(app, tr("CPFT Affective Disorders Research Database — 1"))
{
    m_subtitle = "Cambridgeshire and Peterborough NHS Foundation Trust, UK — "
                 "affective disorders";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("diagnosis_icd9cm", app),  // = DSM-IV
        MAKE_TASK_MENU_ITEM("hamd", app),
        MAKE_TASK_MENU_ITEM("iesr", app),
        MAKE_TASK_MENU_ITEM("pdss", app),
        MAKE_TASK_MENU_ITEM("pswq", app),
        MAKE_TASK_MENU_ITEM("swemwbs", app),
        MAKE_TASK_MENU_ITEM("wsas", app),
        MAKE_TASK_MENU_ITEM("ybocs", app),
        MAKE_TASK_MENU_ITEM("ybocssc", app),
    };
    buildMenu();
}
