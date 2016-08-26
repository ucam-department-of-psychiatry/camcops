#include "helpmenu.h"
#include <QMessageBox>
#include <QtNetwork/QSslSocket>
#include <QtSql/QtSqlVersion>
#include "common/uiconstants.h"
#include "common/version.h"
#include "lib/dbfunc.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

const QString CAMCOPS_URL = "http://camcops.org/";
const QString CAMCOPS_DOCS_URL = "http://camcops.org/documentation/index.html";


HelpMenu::HelpMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Help"), UiFunc::iconFilename(UiConst::ICON_INFO))
{
    QString title_missing = tr("Why isn’t task X here?");
    m_items = {
        MenuItem(tr("Online CamCOPS documentation"),
                 std::bind(&HelpMenu::visitCamcopsDocumentation, this),
                 UiFunc::iconFilename(UiConst::ICON_CAMCOPS)),
        MenuItem(tr("Visit") + " " + CAMCOPS_URL,
                 std::bind(&HelpMenu::visitCamcopsWebsite, this),
                 UiFunc::iconFilename(UiConst::ICON_CAMCOPS)),
        MAKE_TASK_MENU_ITEM("demoquestionnaire", app),
        MenuItem(title_missing,
                 HtmlMenuItem(title_missing,
                              FileFunc::taskHtmlFilename("MISSING_TASKS"),
                              UiFunc::iconFilename(UiConst::ICON_INFO))),
        MenuItem(tr("Show software versions"),
                 std::bind(&HelpMenu::softwareVersions, this)),
        MenuItem(tr("About Qt"),
                 std::bind(&HelpMenu::aboutQt, this)),
        MenuItem(tr("View device (installation) ID")),  // ***
        MenuItem(tr("View terms and conditions of use")),  // ***
    };
}


void HelpMenu::visitCamcopsWebsite()
{
    UiFunc::visitUrl(CAMCOPS_URL);
}


void HelpMenu::visitCamcopsDocumentation()
{
    UiFunc::visitUrl(CAMCOPS_DOCS_URL);
}


void HelpMenu::softwareVersions()
{
    QStringList versions;

    // CamCOPS
    versions.append(QString("CamCOPS tablet version: %1").arg(
                        Version::CAMCOPS_VERSION_STRING));

    // Qt
    versions.append(QString("Qt version: %1").arg(QT_VERSION_STR));

    // SQLite
    // http://stackoverflow.com/questions/12685563/how-to-find-out-version-sqlite-in-qt
    // We can't #include <sqlite3.h>; that's the system version.
    // The Qt driver (in qsql_sqlite.cpp) uses SQLITE_VERSION_NUMBER but
    // doesn't expose it. So we have to ask the database itself.
    QString sql = "SELECT sqlite_version()";
    QString sqlite_version = DbFunc::dbFetchFirstValue(m_app.sysdb(),
                                                       sql).toString();
    versions.append(QString("Embedded SQLite version: %1").arg(sqlite_version));

    // OpenSSL
    // http://stackoverflow.com/questions/23320480
    //      SSLEAY_VERSION
    // https://www.openssl.org/docs/manmaster/crypto/OPENSSL_VERSION_NUMBER.html
    //      OPENSSL_VERSION_NUMBER
    //      OpenSSL_version
    //      OpenSSL_version_num
    // ... all available within QtNetwork/provate/qssql*.h, but not exposed.
    // However, we have this:
    versions.append(QString("Embedded OpenSSL version: %1").arg(
        QSslSocket::sslLibraryVersionString()));

    UiFunc::alert(versions.join("\n"));
}


void HelpMenu::aboutQt()
{
    QMessageBox::aboutQt(this, tr("About Qt"));
}
