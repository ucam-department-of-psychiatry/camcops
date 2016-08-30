#include "singletaskmenu.h"
#include "common/uiconstants.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "menulib/menuheader.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


SingleTaskMenu::SingleTaskMenu(const QString& tablename, CamcopsApp& app) :
    MenuWindow(app, ""),  // start with a blank title
    m_tablename(tablename),
    m_current_task(nullptr)
{
    // Title
    TaskFactoryPtr factory = app.factory();
    TaskPtr specimen = factory->create(m_tablename);
    m_title = specimen->menutitle();
    m_anonymous = specimen->isAnonymous();

    // m_items is EXPENSIVE (and depends on security), so leave it to build()
}


void SingleTaskMenu::build()
{
    TaskFactoryPtr factory = m_app.factory();
    TaskPtr specimen = factory->create(m_tablename);

    // Common items
    QString info_icon_filename = UiFunc::iconFilename(UiConst::ICON_INFO);
    m_items = {
        MenuItem(tr("Options")).setLabelOnly(),
        MAKE_CHANGE_PATIENT(app),
        MenuItem(
            tr("Task information"),
            HtmlMenuItem(
                m_title,
                FileFunc::taskHtmlFilename(specimen->infoFilenameStem()),
                info_icon_filename),
            info_icon_filename
        ),
        MenuItem(tr("Task instances") + ": " + m_title).setLabelOnly(),
    };

    // Task items
    TaskPtrList tasklist = factory->fetch(m_tablename);
    qDebug() << Q_FUNC_INFO << "-" << tasklist.size() << "tasks";
    for (auto task : tasklist) {
        m_items.append(MenuItem(task, false));
    }

    // Call parent buildMenu()
    MenuWindow::build();

    // Signals
    connect(&m_app, &CamcopsApp::selectedPatientChanged,
            this, &SingleTaskMenu::selectedPatientChanged,
            Qt::UniqueConnection);
    connect(&m_app, &CamcopsApp::taskAlterationFinished,
            this, &SingleTaskMenu::taskFinished,
            Qt::UniqueConnection);
    connect(this, &SingleTaskMenu::offerAdd,
            m_p_header, &MenuHeader::offerAdd,
            Qt::UniqueConnection);
    connect(m_p_header, &MenuHeader::addClicked,
            this, &SingleTaskMenu::addTask,
            Qt::UniqueConnection);

    emit offerAdd(m_anonymous || m_app.patientSelected());
}


void SingleTaskMenu::addTask()
{
    // The task we create here needs to stay in scope for the duration of the
    // editing! The simplest way is to use a member object to hold the pointer.
    TaskFactoryPtr factory = m_app.factory();
    TaskPtr task = factory->create(m_tablename);
    if (!task->isAnonymous()) {
        int patient_id = m_app.currentPatientId();
        if (patient_id == DbConst::NONEXISTENT_PK) {
            qCritical() << Q_FUNC_INFO << "- no patient selected";
            return;
        }
        task->setPatient(m_app.currentPatientId());
    }
    task->save();
    OpenableWidget* widget = task->editor(m_app);
    m_app.open(widget, task, true);
}


void SingleTaskMenu::selectedPatientChanged(bool selected,
                                            const QString& details)
{
    (void)details;
    // ... mark as unused; http://stackoverflow.com/questions/1486904/how-do-i-best-silence-a-warning-about-unused-variables
    emit offerAdd(m_anonymous || selected);
}


void SingleTaskMenu::taskFinished()
{
    build();
}
