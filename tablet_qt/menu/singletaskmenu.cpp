#include "singletaskmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuheader.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


SingleTaskMenu::SingleTaskMenu(const QString& tablename, CamcopsApp& app) :
    MenuWindow(app, ""),  // start with a blank title
    m_tablename(tablename)
{
    TaskFactoryPtr factory = app.factory();

    // Title
    TaskPtr specimen = factory->create(tablename);
    m_title = specimen->menutitle();
    m_anonymous = specimen->isAnonymous();

    // Common items
    m_items = {
        MenuItem(tr("Options")).setLabelOnly(),
        MAKE_CHANGE_PATIENT(app),
        MenuItem(tr("Task information")),  // ***
        MenuItem(tr("Task instances") + ": " + m_title).setLabelOnly(),
    };

    // Task items
    TaskPtrList tasklist = factory->fetch(tablename);
    for (auto task : tasklist) {
        m_items.append(MenuItem(task, false));
    }

    // Build
    buildMenu();
}


void SingleTaskMenu::buildMenu()
{
    MenuWindow::buildMenu();

    // Signals
    connect(&m_app, &CamcopsApp::selectedPatientChanged,
            this, &SingleTaskMenu::selectedPatientChanged);
    connect(this, &SingleTaskMenu::offerAdd,
            m_p_header, &MenuHeader::offerAdd);
    connect(m_p_header, &MenuHeader::addClicked,
            this, &SingleTaskMenu::addTask);

    emit offerAdd(m_anonymous || m_app.patientSelected());
}


// *** think about the "lock changed" signal (a call to buildMenu() is probably insufficient as task eligibility may change?)

void SingleTaskMenu::addTask()
{
    TaskFactoryPtr factory = m_app.factory();
    TaskPtr task = factory->create(m_tablename);
    if (!task->isAnonymous()) {
        int patient_id = m_app.currentPatientId();
        if (patient_id == NONEXISTENT_PK) {
            qCritical() << "SingleTaskMenu::addTask(): no patient selected";
            return;
        }
        task->setPatient(m_app.currentPatientId());
    }
    task->edit(m_app);
}


void SingleTaskMenu::selectedPatientChanged(bool selected,
                                            const QString& details)
{
    (void)details;
    emit offerAdd(m_anonymous || selected);
}
