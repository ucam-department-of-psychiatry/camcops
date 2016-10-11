#include "helpmenu.h"
#include <QMessageBox>
#include <QTextStream>
#include <QtNetwork/QSslSocket>
#include <QSqlDriver>
#include <QtSql/QtSqlVersion>
#include "common/uiconstants.h"
#include "common/version.h"
#include "db/dbfunc.h"
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
    QString newline = "";

    // ------------------------------------------------------------------------
    // CamCOPS
    // ------------------------------------------------------------------------
    versions.append(QString("CamCOPS tablet version: %1").arg(
                        Version::CAMCOPS_VERSION_STRING));
    versions.append(newline);

    // ------------------------------------------------------------------------
    // Qt
    // ------------------------------------------------------------------------
    versions.append(QString("Qt version: %1").arg(QT_VERSION_STR));
    versions.append(newline);

    // ------------------------------------------------------------------------
    // SQLite
    // ------------------------------------------------------------------------
    // http://stackoverflow.com/questions/12685563/how-to-find-out-version-sqlite-in-qt
    // We can't #include <sqlite3.h>; that's the system version.
    // The Qt driver (in qsql_sqlite.cpp) uses SQLITE_VERSION_NUMBER but
    // doesn't expose it. So we have to ask the database itself.
    QString sql = "SELECT sqlite_version()";
    QSqlDatabase& db = m_app.sysdb();
    QString sqlite_version = DbFunc::dbFetchFirstValue(db, sql).toString();
    versions.append(QString("Embedded SQLite version: %1").arg(sqlite_version));
    QString sqlite_info;
    QTextStream s(&sqlite_info);
    QSqlDriver* driver = db.driver();
    s << "... supported database features (0 no, 1 yes): "
      << "Transactions " << driver->hasFeature(QSqlDriver::Transactions)
      << "; QuerySize " << driver->hasFeature(QSqlDriver::QuerySize)
      << "; BLOB " << driver->hasFeature(QSqlDriver::BLOB)
      << "; Unicode " << driver->hasFeature(QSqlDriver::Unicode)
      << "; PreparedQueries " << driver->hasFeature(QSqlDriver::PreparedQueries)
      << "; NamedPlaceholders " << driver->hasFeature(QSqlDriver::NamedPlaceholders)
      << "; PositionalPlaceholders " << driver->hasFeature(QSqlDriver::PositionalPlaceholders)
      << "; LastInsertId " << driver->hasFeature(QSqlDriver::LastInsertId)
      << "; BatchOperations " << driver->hasFeature(QSqlDriver::BatchOperations)
      << "; SimpleLocking " << driver->hasFeature(QSqlDriver::SimpleLocking)
      << "; LowPrecisionNumbers " << driver->hasFeature(QSqlDriver::LowPrecisionNumbers)
      << "; EventNotifications " << driver->hasFeature(QSqlDriver::EventNotifications)
      << "; FinishQuery " << driver->hasFeature(QSqlDriver::FinishQuery)
      << "; MultipleResultSets " << driver->hasFeature(QSqlDriver::MultipleResultSets)
      << "; CancelQuery " << driver->hasFeature(QSqlDriver::CancelQuery);
    versions.append(sqlite_info);
    versions.append(newline);


    // ------------------------------------------------------------------------
    // OpenSSL
    // ------------------------------------------------------------------------
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
