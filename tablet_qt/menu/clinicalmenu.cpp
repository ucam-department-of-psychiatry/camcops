#include "clinicalmenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


ClinicalMenu::ClinicalMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Clinical notes and logs"),
               UiFunc::iconFilename(UiConst::ICON_CLINICAL))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM("bmi", app),
        MAKE_TASK_MENU_ITEM("contactlog", app),
        MAKE_TASK_MENU_ITEM("cpft_lps_referral", app),
        MAKE_TASK_MENU_ITEM("cpft_lps_resetresponseclock", app),
        MAKE_TASK_MENU_ITEM("cpft_lps_discharge", app),
        MAKE_TASK_MENU_ITEM("diagnosis_icd10", app),
        MAKE_TASK_MENU_ITEM("fft", app),
        MAKE_TASK_MENU_ITEM("irac", app),
        MAKE_TASK_MENU_ITEM("pt_satis", app),
        MAKE_TASK_MENU_ITEM("photo", app),
        MAKE_TASK_MENU_ITEM("photosequence", app),
        MAKE_TASK_MENU_ITEM("progressnote", app),
        MAKE_TASK_MENU_ITEM("psychiatricclerking", app),
        MAKE_TASK_MENU_ITEM("ref_satis_spec", app),
    };
}
