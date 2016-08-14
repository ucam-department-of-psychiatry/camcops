#include "singletaskmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


SingleTaskMenu::SingleTaskMenu(const QString& tablename, CamcopsApp& app) :
    MenuWindow(app, "")  // start with a blank title
{
    TaskFactoryPtr factory = app.m_p_task_factory;

    // Title
    TaskPtr specimen = factory->create(tablename);
    m_title = specimen->menutitle();

    // Offer task addition
    m_offer_add_task = true;

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
        m_items.append(MenuItem(task));
    }

    // Build
    buildMenu();
}

// *** think about the "lock changed" signal (a call to buildMenu() is probably insufficient as task eligibility may change?)
