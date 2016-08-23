#include "patientsummarymenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


PatientSummaryMenu::PatientSummaryMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Patient summary"),
               UiFunc::iconFilename(UiConst::ICON_PATIENT_SUMMARY))
{
    // m_items is EXPENSIVE (and depends on security), so leave it to build()
}


void PatientSummaryMenu::build()
{
    TaskFactoryPtr factory = m_app.factory();

    // Common items
    m_items = {
        MenuItem(tr("Options")).setLabelOnly(),
        MAKE_CHANGE_PATIENT(app),
        MenuItem(tr("Task instances")).setLabelOnly(),
    };

    // Task items
    TaskPtrList tasklist = factory->fetch();
    qDebug() << "PatientSummaryMenu::build:" << tasklist.size() << "tasks";
    for (auto task : tasklist) {
        m_items.append(MenuItem(task));
    }

    // Call parent build()
    MenuWindow::build();
}
