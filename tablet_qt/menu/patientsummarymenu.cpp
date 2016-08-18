#include "patientsummarymenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


PatientSummaryMenu::PatientSummaryMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Patient summary"), ICON_PATIENT_SUMMARY)
{
    // m_items is EXPENSIVE, so leave it to buildMenu()
}

// *** think about the "lock changed" signal (a call to buildMenu() is probably insufficient as task eligibility may change?)


void PatientSummaryMenu::buildMenu()
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
    qDebug() << "PatientSummaryMenu::buildMenu:" << tasklist.size() << "tasks";
    for (auto task : tasklist) {
        m_items.append(MenuItem(task));
    }

    // Call parent buildMenu()
    MenuWindow::buildMenu();
}
