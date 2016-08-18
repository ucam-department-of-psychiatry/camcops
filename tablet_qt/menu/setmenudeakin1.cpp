#include "setmenudeakin1.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


SetMenuDeakin1::SetMenuDeakin1(CamcopsApp& app) :
    MenuWindow(app, tr("Deakin JB — 1"))
{
    m_subtitle = "Deakin JB, University of Cambridge, UK — "
                 "antibody-mediated psychosis";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("ace3", app),
        MAKE_TASK_MENU_ITEM("bdi", app),
        MAKE_TASK_MENU_ITEM("bmi", app),
        MAKE_TASK_MENU_ITEM("caps", app),
        MAKE_TASK_MENU_ITEM("cecaq3", app),
        MAKE_TASK_MENU_ITEM("cgisch", app),
        MAKE_TASK_MENU_ITEM("diagnosis_icd9cm", app),
        MAKE_TASK_MENU_ITEM("deakin_1_healthreview", app),
        MenuItem("*** soundtest for ExpDetThreshold/ExpDet"),
        MAKE_TASK_MENU_ITEM("cardinal_expdetthreshold", app),
        MAKE_TASK_MENU_ITEM("cardinal_expdet", app),
        MAKE_TASK_MENU_ITEM("gaf", app),
        MAKE_TASK_MENU_ITEM("nart", app),
        MAKE_TASK_MENU_ITEM("panss", app),
    };
}
