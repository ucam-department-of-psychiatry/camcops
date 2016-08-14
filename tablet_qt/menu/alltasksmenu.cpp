#include "alltasksmenu.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


AllTasksMenu::AllTasksMenu(CamcopsApp& app) :
    MenuWindow(app, tr("All tasks, listed alphabetically"), ICON_ALLTASKS)
{
    TaskFactoryPtr factory = app.m_p_task_factory;
    QStringList tablenames = factory->tablenames();
    for (auto tablename : tablenames) {
        m_items.append(MAKE_TASK_MENU_ITEM(tablename, app));
    }
    buildMenu();
}
