#include "helpmenu.h"
#include <QMessageBox>
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

const QString CAMCOPS_URL = "http://camcops.org/";
const QString CAMCOPS_DOCS_URL = "http://camcops.org/documentation/index.html";


HelpMenu::HelpMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Help"), ICON_INFO)
{
    m_items = {
        MenuItem(tr("Online CamCOPS documentation"),
                 std::bind(&HelpMenu::visitCamcopsDocumentation, this),
                 ICON_CAMCOPS),
        MenuItem(tr("Visit") + " " + CAMCOPS_URL,
                 std::bind(&HelpMenu::visitCamcopsWebsite, this),
                 ICON_CAMCOPS),
        MAKE_TASK_MENU_ITEM("demoquestionnaire", app),
        MenuItem(tr("Why isn’t task X here?")),  // ***
        MenuItem(tr("Show software versions"),
                 std::bind(&HelpMenu::softwareVersions, this)),
        MenuItem(tr("About Qt"),
                 std::bind(&HelpMenu::aboutQt, this)),
        MenuItem(tr("View device (installation) ID")),  // ***
        MenuItem(tr("View terms and conditions of use")),  // ***
    };
    buildMenu();
}


void HelpMenu::visitCamcopsWebsite()
{
    visitUrl(CAMCOPS_URL);
}


void HelpMenu::visitCamcopsDocumentation()
{
    visitUrl(CAMCOPS_DOCS_URL);
}


void HelpMenu::softwareVersions()
{
    QStringList versions;
    versions.append(QString("CamCOPS tablet version: %1").arg("??? *** ???"));
    versions.append(QString("Qt version: %1").arg(QT_VERSION_STR));
    alert(versions.join("\n"));
}


void HelpMenu::aboutQt()
{
    QMessageBox::aboutQt(this, tr("About Qt"));
}
