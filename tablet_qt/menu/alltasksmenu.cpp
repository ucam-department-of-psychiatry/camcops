#include "alltasksmenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


AllTasksMenu::AllTasksMenu(CamcopsApp& app) :
    MenuWindow(app, tr("All tasks, listed alphabetically"),
               UiFunc::iconFilename(UiConst::ICON_ALLTASKS))
{
    TaskFactoryPtr factory = app.taskFactory();
    QStringList tablenames = factory->tablenames();
    for (auto tablename : tablenames) {
        m_items.append(MAKE_TASK_MENU_ITEM(tablename, app));
    }
}
