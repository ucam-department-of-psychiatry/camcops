/*
    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "helpmenu.h"
#include <QMessageBox>
#include <QTextStream>
#include <QtNetwork/QSslSocket>
#include <QSqlDriver>
#include <QtSql/QtSqlVersion>
#include "common/uiconstants.h"
#include "common/camcopsversion.h"
#include "db/dbfunc.h"
#include "lib/datetimefunc.h"
#include "lib/filefunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

const QString CAMCOPS_URL("http://camcops.org/");
const QString CAMCOPS_DOCS_URL("http://camcops.org/documentation/index.html");


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
        MenuItem(tr("View device (installation) ID and database details"),
                 std::bind(&HelpMenu::showDeviceIdAndDbDetails, this)),
        MenuItem(tr("View terms and conditions of use"),
                 std::bind(&HelpMenu::viewTermsConditions, this)),
    };
}


void HelpMenu::visitCamcopsWebsite() const
{
    UiFunc::visitUrl(CAMCOPS_URL);
}


void HelpMenu::visitCamcopsDocumentation() const
{
    UiFunc::visitUrl(CAMCOPS_DOCS_URL);
}


void HelpMenu::softwareVersions() const
{
    QStringList versions;
    QString newline = "";

    // ------------------------------------------------------------------------
    // CamCOPS
    // ------------------------------------------------------------------------
    versions.append(QString("<b>CamCOPS tablet version:</b> %1").arg(
                        CamcopsVersion::CAMCOPS_VERSION.toString()));
    versions.append(newline);

    // ------------------------------------------------------------------------
    // Qt
    // ------------------------------------------------------------------------
    versions.append(QString("<b>Qt version:</b> %1").arg(QT_VERSION_STR));
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
    versions.append(QString("<b>Embedded SQLite version:</b> %1").arg(sqlite_version));
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
    // http://stackoverflow.com/questions/39480724/use-openssl-in-qt-c
    // https://www.openssl.org/docs/manmaster/crypto/OPENSSL_VERSION_NUMBER.html
    //      OPENSSL_VERSION_NUMBER
    //      OpenSSL_version
    //      OpenSSL_version_num
    // ... all available within QtNetwork/provate/qssql*.h, but not exposed.
    // However, we have this:
    versions.append(QString("<b>Compile-time OpenSSL version:</b> %1").arg(
        QSslSocket::sslLibraryBuildVersionString()));
    versions.append(QString("<b>Run-time OpenSSL version:</b> %1").arg(
        QSslSocket::sslLibraryVersionString()));

    UiFunc::alert(versions.join("<br>"), tr("Software versions"));
}


void HelpMenu::aboutQt()
{
    QMessageBox::aboutQt(this, tr("About Qt"));
}


void HelpMenu::showDeviceIdAndDbDetails() const
{
    QStringList lines;
    lines.append(QString("<b>Device ID:</b> %1").arg(m_app.deviceId()));
    lines.append(QString("<b>Main database:</b> %1").arg(
        DbFunc::dbFullPath(DbFunc::DATA_DATABASE_FILENAME)));
    lines.append(QString("<b>System database:</b> %1").arg(
        DbFunc::dbFullPath(DbFunc::SYSTEM_DATABASE_FILENAME)));
    UiFunc::alert(StringFunc::joinHtmlLines(lines),
                  tr("Device/installation ID; databases"));
}


void HelpMenu::viewTermsConditions() const
{
    QString title = QString("You agreed to these terms and conditions at: %1")
            .arg(DateTime::shortDateTime(m_app.agreedTermsAt()));
    UiFunc::alert(UiConst::TERMS_CONDITIONS, title);
}
