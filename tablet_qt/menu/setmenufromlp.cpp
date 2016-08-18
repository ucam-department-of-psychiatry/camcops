#include "setmenufromlp.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


SetMenuFromLp::SetMenuFromLp(CamcopsApp& app) :
    MenuWindow(app, tr("FROM-LP"))
{
    m_subtitle = "Framework for Routine Outcome Measurement in Liaison "
                 "Psychiatry (FROM-LP)";
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MenuItem(tr("GENERIC SCALES")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM("cgi_i", app),
        // CORE-10 -- copyright conditions prohibit
        MAKE_TASK_MENU_ITEM("irac", app),
        MAKE_TASK_MENU_ITEM("pt_satis", app),
        MAKE_TASK_MENU_ITEM("fft", app),
        MAKE_TASK_MENU_ITEM("ref_satis_gen", app),
        MAKE_TASK_MENU_ITEM("ref_satis_spec", app),

        MenuItem(tr("DISEASE-SPECIFIC SCALES")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM("ace3", app),
        MAKE_TASK_MENU_ITEM("phq9", app),
        // EPDS -- Royal College not currently permitting use
        MAKE_TASK_MENU_ITEM("gad7", app),
        MAKE_TASK_MENU_ITEM("honos", app),
        MAKE_TASK_MENU_ITEM("audit_c", app),
        MAKE_TASK_MENU_ITEM("bmi", app),
        // *** EQ-5D-5L, if permitted?
    };
}
