/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
#include <QTextStream>
#include <QtNetwork/QSslSocket>
#include <QSqlDriver>
#include <QtSql/QtSqlVersion>
#include "common/textconst.h"
#include "common/uiconst.h"
#include "common/urlconst.h"
#include "db/databasemanager.h"
#include "db/dbfunc.h"
#include "db/whichdb.h"
#include "dialogs/scrollmessagebox.h"
#include "lib/datetime.h"
#include "lib/filefunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasks/demoquestionnaire.h"
#include "version/camcopsversion.h"


HelpMenu::HelpMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Help"), uifunc::iconFilename(uiconst::ICON_INFO))
{
    QString fname_camcopsicon(uifunc::iconFilename(uiconst::ICON_CAMCOPS));
    QString fname_infoicon(uifunc::iconFilename(uiconst::ICON_INFO));
    // You can't point a standard web browser at a Qt resource file.
    // (They are not necessarily actual files on disk.)
    // Creating an HtmlMenuItem that points to Sphinx documentation just looks
    // rubbish.
    // Copying lots of Qt resource files to the filesystem would be possible,
    // but would require care about when to do it (not too often because that's
    // inefficient -- currently 1.9Mb and growing; then you need a change
    // control mechanism). Lots of hassle.
    // The best thing is probably to use the online docs.
    // If the user has registered wih a server, we could point them to their
    // own server, but perhaps a canonical set of docs is simplest. It's
    // certainly better if we need to update something quickly.
    m_items = {
        MenuItem(tr("Online CamCOPS documentation"),
                 UrlMenuItem(urlconst::CAMCOPS_DOCS_URL),
                 fname_infoicon),
        MenuItem(tr("Visit") + " " + urlconst::CAMCOPS_URL,
                 UrlMenuItem(urlconst:: CAMCOPS_URL),
                 fname_camcopsicon),
        MAKE_TASK_MENU_ITEM(DemoQuestionnaire::DEMOQUESTIONNAIRE_TABLENAME, app),
        MenuItem(tr("Show software versions"),
                 std::bind(&HelpMenu::softwareVersions, this)),
        MenuItem(tr("About Qt"),
                 std::bind(&HelpMenu::aboutQt, this)),
        MenuItem(tr("View device (installation) ID and database details"),
                 std::bind(&HelpMenu::showDeviceIdAndDbDetails, this)),
        MenuItem(tr("Licence details"),
                 UrlMenuItem(urlconst::CAMCOPS_LICENCES_URL)),
        MenuItem(tr("View terms and conditions of use"),
                 std::bind(&HelpMenu::viewTermsConditions, this)),
    };
}


void HelpMenu::softwareVersions() const
{
    QStringList versions;
    QString newline = "";

    // ------------------------------------------------------------------------
    // CamCOPS
    // ------------------------------------------------------------------------
    versions.append(QString("<b>CamCOPS tablet version:</b> %1").arg(
                        camcopsversion::CAMCOPS_VERSION.toString()));
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
    DatabaseManager& db = m_app.sysdb();
    QString sqlite_version = db.fetchFirstValue("SELECT sqlite_version()").toString();
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
#ifdef USE_SQLCIPHER
    QString sqlcipher_version = db.fetchFirstValue("PRAGMA cipher_version").toString();
    QString cipher_provider = db.fetchFirstValue("PRAGMA cipher_provider").toString();
    QString cipher_provider_version = db.fetchFirstValue("PRAGMA cipher_provider_version").toString();
    versions.append(QString("<b>SQLCipher version:</b> %1 (cipher provider: "
                            "%2, version: %3)")
                    .arg(sqlcipher_version,
                         cipher_provider,
                         cipher_provider_version));
#endif
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
    // ... all available within QtNetwork/private/qssql*.h, but not exposed.
    // However, we have this:
    versions.append(QString("<b>Compile-time OpenSSL version:</b> %1").arg(
        QSslSocket::sslLibraryBuildVersionString()));
    versions.append(QString("<b>Run-time OpenSSL version:</b> %1").arg(
        QSslSocket::sslLibraryVersionString()));

    uifunc::alert(versions.join("<br>"), tr("Software versions"));
}


void HelpMenu::aboutQt()
{
    QMessageBox::aboutQt(this);
}


void HelpMenu::showDeviceIdAndDbDetails() const
{
    QStringList lines{
        QString("<b>Device ID:</b> %1").arg(m_app.deviceId()),
        QString("<b>Dots per inch (DPI):</b> %1").arg(m_app.dotsPerInch()),
        QString("<b>Main database:</b> %1").arg(
            m_app.dbFullPath(dbfunc::DATA_DATABASE_FILENAME)),
        QString("<b>System database:</b> %1").arg(
            m_app.dbFullPath(dbfunc::SYSTEM_DATABASE_FILENAME)),
    };
    uifunc::alert(stringfunc::joinHtmlLines(lines),
                  tr("Device/installation ID; databases"));
}


void HelpMenu::viewTermsConditions()
{
    QString title = QString("You agreed to these terms and conditions at: %1")
            .arg(datetime::shortDateTime(m_app.agreedTermsAt()));
    ScrollMessageBox::information(this, title, textconst::TERMS_CONDITIONS);
}
