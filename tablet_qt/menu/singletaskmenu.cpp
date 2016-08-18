#include "singletaskmenu.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "menulib/menuheader.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


SingleTaskMenu::SingleTaskMenu(const QString& tablename, CamcopsApp& app) :
    MenuWindow(app, ""),  // start with a blank title
    m_tablename(tablename)
{
    // Title
    TaskFactoryPtr factory = app.factory();
    TaskPtr specimen = factory->create(m_tablename);
    m_title = specimen->menutitle();
    m_anonymous = specimen->isAnonymous();

    // m_items is EXPENSIVE, so leave it to buildMenu()
}


void SingleTaskMenu::buildMenu()
{
    TaskFactoryPtr factory = m_app.factory();
    TaskPtr specimen = factory->create(m_tablename);

    // Common items
    m_items = {
        MenuItem(tr("Options")).setLabelOnly(),
        MAKE_CHANGE_PATIENT(app),
        MenuItem(
            tr("Task information"),
            HtmlMenuItem(m_title,
                         taskHtmlFilename(specimen->getInfoFilenameStem()),
                         ICON_INFO),
            ICON_INFO
        ),
        MenuItem(tr("Task instances") + ": " + m_title).setLabelOnly(),
    };

    // Task items
    TaskPtrList tasklist = factory->fetch(m_tablename);
    qDebug() << "SingleTaskMenu::buildMenu:" << tasklist.size() << "tasks";
    for (auto task : tasklist) {
        m_items.append(MenuItem(task, false));
    }

    // Call parent buildMenu()
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
    task->save();
    task->edit(m_app);
}


void SingleTaskMenu::selectedPatientChanged(bool selected,
                                            const QString& details)
{
    (void)details;
    emit offerAdd(m_anonymous || selected);
}
