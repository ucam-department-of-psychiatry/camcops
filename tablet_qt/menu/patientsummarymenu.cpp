#include "patientsummarymenu.h"
#include "common/uiconstants.h"
#include "dbobjects/patient.h"
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
    TaskFactoryPtr factory = m_app.taskFactory();

    // Common items
    m_items = {
        MenuItem(tr("Options")).setLabelOnly(),
        MAKE_CHANGE_PATIENT(m_app),
        MenuItem(tr("Task instances")).setLabelOnly(),
    };

    // Task items
    TaskPtrList tasklist = factory->fetch();
    qDebug() << Q_FUNC_INFO << "-" << tasklist.size() << "tasks";
    for (auto task : tasklist) {
        m_items.append(MenuItem(task));
    }

    // Call parent build()
    MenuWindow::build();

    // Signals
    connect(&m_app, &CamcopsApp::selectedPatientChanged,
            this, &PatientSummaryMenu::selectedPatientChanged,
            Qt::UniqueConnection);
    connect(&m_app, &CamcopsApp::taskAlterationFinished,
            this, &PatientSummaryMenu::taskFinished,
            Qt::UniqueConnection);
}


void PatientSummaryMenu::selectedPatientChanged(const Patient* patient)
{
    Q_UNUSED(patient);
    build();  // refresh task list
}


void PatientSummaryMenu::taskFinished()
{
    build();  // refresh task list
}
