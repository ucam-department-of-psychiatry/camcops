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

// #define DEBUG_DROP_TABLES_NOT_EXPLICITLY_CREATED

// #define DANGER_DEBUG_PASSWORD_DECRYPTION
// #define DANGER_DEBUG_WIPE_PASSWORDS

// #define DEBUG_CSS_SIZES
// #define DEBUG_EMIT
// #define DEBUG_SCREEN_STACK
// #define DEBUG_ALL_APPLICATION_EVENTS

#include "camcopsapp.h"
#include <QApplication>
#include <QCommandLineOption>
#include <QCommandLineParser>
#include <QDateTime>
#include <QDebug>
#include <QDir>
#include <QIcon>
#include <QMainWindow>
#include <QProcessEnvironment>
#include <QPushButton>
#include <QScreen>
#include <QSqlDatabase>
#include <QSqlDriverCreator>
#include <QStackedWidget>
#include <QStandardPaths>
#include <QTextStream>
#include <QUuid>
#include "common/appstrings.h"
#include "common/dbconst.h"  // for NONEXISTENT_PK
#include "common/design_defines.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "common/varconst.h"
#include "core/networkmanager.h"
#include "crypto/cryptofunc.h"
#include "db/ancillaryfunc.h"
#include "db/databasemanager.h"
#include "db/dbfunc.h"
#include "db/dbnestabletransaction.h"
#include "db/whereconditions.h"
#include "db/whichdb.h"
#include "dbobjects/allowedservertable.h"
#include "dbobjects/blob.h"
#include "dbobjects/extrastring.h"
#include "dbobjects/idnumdescription.h"
#include "dbobjects/patientidnum.h"
#include "dbobjects/patientsorter.h"
#include "dbobjects/storedvar.h"
#include "dialogs/scrollmessagebox.h"
#include "layouts/layouts.h"
#include "lib/convert.h"
#include "lib/datetime.h"
#include "lib/filefunc.h"
#include "lib/idpolicy.h"
#include "lib/slowguiguard.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "menu/mainmenu.h"
#include "qobjects/debugeventwatcher.h"
#include "qobjects/slownonguifunctioncaller.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "tasklib/inittasks.h"
#include "version/camcopsversion.h"

#ifdef USE_SQLCIPHER
#include "db/sqlcipherdriver.h"
#endif

const QString APPSTRING_TASKNAME("camcops");  // task name used for generic but downloaded tablet strings
const QString APP_NAME("camcops");  // e.g. subdirectory of ~/.local/share; DO NOT ALTER
const QString APP_PRETTY_NAME("CamCOPS");
const QString ARG_DB_DIR("--dbdir");
const QString CONNECTION_DATA("data");
const QString CONNECTION_SYS("sys");
const QString ENVVAR_DB_DIR("CAMCOPS_DATABASE_DIRECTORY");


CamcopsApp::CamcopsApp(int& argc, char* argv[]) :
    QApplication(argc, argv),
    m_p_task_factory(nullptr),
    m_lockstate(LockState::Locked),  // default unless we get in via encryption password
    m_whisker_connected(false),
    m_p_main_window(nullptr),
    m_p_window_stack(nullptr),
    m_p_hidden_stack(nullptr),
    m_patient(nullptr),
    m_netmgr(nullptr),
    m_dpi(uiconst::DEFAULT_DPI)
{
    setApplicationName(APP_NAME);
    setApplicationDisplayName(APP_PRETTY_NAME);
    setApplicationVersion(camcopsversion::CAMCOPS_VERSION.toString());
#ifdef DEBUG_ALL_APPLICATION_EVENTS
    new DebugEventWatcher(this, DebugEventWatcher::All);
#endif
}


CamcopsApp::~CamcopsApp()
{
    // http://doc.qt.io/qt-5.7/objecttrees.html
    // Only delete things that haven't been assigned a parent
    delete m_p_main_window;
}


int CamcopsApp::run()
{
    // We do the minimum possible; then we fire up the GUI; then we run
    // everything that we can in a different thread through backgroundStartup.
    // This makes the GUI startup more responsive.

    // Command-line arguments
    int retcode = 0;
    if (!processCommandLineArguments(retcode)) {  // may exit directly if syntax error
        return retcode;  // exit with failure/success
    }

    // Say hello to the console
    announceStartup();

    // Baseline C++ things
    seedRng();
    convert::registerTypesForQVariant();

    // Set window icon
    initGuiOne();

    // Connect to our database
    registerDatabaseDrivers();
    openOrCreateDatabases();
    QString new_user_password;
    bool user_cancelled_please_quit = false;
    const bool changed_user_password = connectDatabaseEncryption(
                new_user_password, user_cancelled_please_quit);
    if (user_cancelled_please_quit) {
        qCritical() << "User cancelled attempt";
        return 0;  // will quit
    }

    // Make storedvar table (used by menus for font size etc.)
    makeStoredVarTable();
    createStoredVars();

    // Set the tablet internal password to match the database password, if
    // we've just changed it. Uses a storedvar.
#ifdef DANGER_DEBUG_WIPE_PASSWORDS
#ifndef SQLCIPHER_ENCRYPTION_ON
    // Can't mess around with the user password when it's also the database p/w
    qDebug() << "DANGER: wiping user-mode password";
    setHashedPassword(varconst::USER_PASSWORD_HASH, "");
#endif
    qDebug() << "DANGER: wiping privileged-mode password";
    setHashedPassword(varconst::PRIV_PASSWORD_HASH, "");
#endif
#ifdef SQLCIPHER_ENCRYPTION_ON
    if (changed_user_password) {
        setHashedPassword(varconst::USER_PASSWORD_HASH, new_user_password);
    }
#else
    Q_UNUSED(changed_user_password);
#endif

    // Set the stylesheet.
    initGuiTwoStylesheet();  // AFTER storedvar creation

    // Do the rest of the database configuration, task registration, etc.,
    // with a "please wait" dialog.
    SlowNonGuiFunctionCaller(
        std::bind(&CamcopsApp::backgroundStartup, this),
        m_p_main_window,
        "Configuring internal database",
        "Please wait");

    openMainWindow();  // uses HelpMenu etc. and so must be AFTER TASK REGISTRATION
    makeNetManager();  // needs to be after main window created, and on GUI thread
#ifdef ALLOW_SEND_ANALYTICS
    networkManager()->sendAnalytics();
#endif

    if (!hasAgreedTerms()) {
        offerTerms();
    }
    qInfo() << "Starting Qt event processor...";
    return exec();  // Main Qt event loop
}


void CamcopsApp::backgroundStartup()
{
    // WORKER THREAD. BEWARE.
    const Version& old_version = upgradeDatabaseBeforeTablesMade();
    makeOtherSystemTables();
    registerTasks();  // AFTER storedvar creation, so tasks can read them
    upgradeDatabaseAfterTasksRegistered(old_version);  // AFTER tasks registered
    makeTaskTables();
    // Should we drop tables we're unaware of? Clearly we should never do this
    // on the server. Doing so on the client prevents the client trying to
    // upload duff tables to the server (giving an error that will confuse the
    // user). How could we get superfluous tables? Two situations are: (a)
    // users fiddling, and (b) me adding a task, running the client, disabling
    // the task... Consider also the situation of a DOWNGRADE in client; should
    // we destroy "newer" data we're ignorant of? Probably not.
#ifdef DEBUG_DROP_TABLES_NOT_EXPLICITLY_CREATED
    m_datadb->dropTablesNotExplicitlyCreatedByUs();
    m_sysdb->dropTablesNotExplicitlyCreatedByUs();
#endif
}


// ============================================================================
// Initialization
// ============================================================================

QString CamcopsApp::defaultDatabaseDir() const
{
    return QStandardPaths::standardLocations(QStandardPaths::AppDataLocation).first();
    // Under Linux: ~/.local/share/camcops/; the last part of this path is
    // determined by the call to QCoreApplication::setApplicationName(), or if
    // that hasn't been set, the executable name.
}


bool CamcopsApp::processCommandLineArguments(int& retcode)
{
    // https://stackoverflow.com/questions/3886105/how-to-print-to-console-when-using-qt
    // QTextStream out(stdout);
    // QTextStream err(stderr);

    // const int retcode_fail = 1;
    const int retcode_success = 0;

    retcode = retcode_success;  // default failure code

    // Build parser
    QCommandLineParser parser;
    parser.addHelpOption();
    parser.addVersionOption();
    QCommandLineOption dbDirOption(
        "dbdir",
        QString(
            "Specify the database directory, in which the databases %1 and %2 "
            "are used or created. Order of precedence (highest to lowest) "
            "is (1) this argument, (2) the %3 environment variable, and (3) "
            "the default of %4."
        ).arg(
            convert::stringToCppLiteral(dbfunc::DATA_DATABASE_FILENAME),
            convert::stringToCppLiteral(dbfunc::SYSTEM_DATABASE_FILENAME),
            ENVVAR_DB_DIR,
            convert::stringToCppLiteral(defaultDatabaseDir())
        )
    );
    dbDirOption.setValueName("DBDIR");
    parser.addOption(dbDirOption);

    // Process the arguments
    parser.process(*this);  // will exit directly upon failure
    // ... could also use parser.process(arguments()), or parser.parse(...)

    // Defaults
    QProcessEnvironment env = QProcessEnvironment::systemEnvironment();
    m_database_path = env.value(ENVVAR_DB_DIR, defaultDatabaseDir());

    // Apply parsed arguments
    QString db_dir = parser.value(dbDirOption);
    if (!db_dir.isEmpty()) {
        m_database_path = db_dir;
    }

    return true;  // happy
}


void CamcopsApp::announceStartup()
{
    // ------------------------------------------------------------------------
    // Announce startup
    // ------------------------------------------------------------------------
    const QDateTime dt = datetime::now();
    qInfo() << "CamCOPS starting at local time:"
            << qUtf8Printable(datetime::datetimeToIsoMs(dt));
    qInfo() << "CamCOPS starting at UTC time:"
            << qUtf8Printable(datetime::datetimeToIsoMsUtc(dt));
    qInfo() << "CamCOPS version:" << camcopsversion::CAMCOPS_VERSION;
#if defined __GNUC__
    qDebug().nospace()
            << "Compiled with GNU C++ compiler version "
            << __GNUC__ << "." << __GNUC_MINOR__ << "." << __GNUC_PATCHLEVEL__;
#elif defined _MSC_VER
    qDebug().nospace()
            << "Compiled with Microsoft Visual C++ version " << _MSC_FULL_VER;
#else
    qDebug() << "Compiler type/version unknown";
#endif
    qDebug() << "Compiled at" << __DATE__ << __TIME__;
}


void CamcopsApp::registerDatabaseDrivers()
{
#ifdef USE_SQLCIPHER
    QSqlDatabase::registerSqlDriver(whichdb::SQLCIPHER,
                                    new QSqlDriverCreator<SQLCipherDriver>);
    qInfo() << "Using SQLCipher database";
#else
    qInfo() << "Using SQLite database";
#endif
}


QString CamcopsApp::dbFullPath(const QString& filename)
{
    filefunc::ensureDirectoryExistsOrDie(m_database_path);
    // http://stackoverflow.com/questions/3541529/is-there-qpathcombine-in-qt4
    return QDir::cleanPath(m_database_path + "/" + filename);
}


void CamcopsApp::openOrCreateDatabases()
{
    // ------------------------------------------------------------------------
    // Create databases
    // ------------------------------------------------------------------------
    // We can't do things like opening the database until we have
    // created the app. So don't open the database in the initializer list!
    // Database lifetime:
    // http://stackoverflow.com/questions/7669987/what-is-the-correct-way-of-qsqldatabase-qsqlquery

    const QString data_filename = dbFullPath(dbfunc::DATA_DATABASE_FILENAME);
    const QString sys_filename = dbFullPath(dbfunc::SYSTEM_DATABASE_FILENAME);
    m_datadb = DatabaseManagerPtr(new DatabaseManager(data_filename, CONNECTION_DATA));
    m_sysdb = DatabaseManagerPtr(new DatabaseManager(sys_filename, CONNECTION_SYS));
}


void CamcopsApp::closeDatabases()
{
    m_datadb = nullptr;
    m_sysdb = nullptr;
}


bool CamcopsApp::connectDatabaseEncryption(QString& new_user_password,
                                           bool& user_cancelled_please_quit)
{
    // Returns: was the user password set (changed)?

#ifdef SQLCIPHER_ENCRYPTION_ON
    // ------------------------------------------------------------------------
    // Encryption on!
    // ------------------------------------------------------------------------
    // The encryption concept is simple:
    // - We know a database is "fresh" if we can execute some basic SQL such as
    //   "SELECT COUNT(*) FROM sqlite_master;" before applying any key.
    // - If the database is fresh:
    //   * We ask the user for a password (with a double-check).
    //   * We encrypt the database using "PRAGMA key = 'passphrase';"
    //   * We store a hashed copy of this password as the user password
    //     (because we don't want too many, and we need one for the lock/unlock
    //     facility anyway).
    // - Otherwise:
    //   * We ask the user for the password.
    //   * We apply it with "PRAGMA key = 'passphrase';"
    //   * We check with "SELECT COUNT(*) FROM sqlite_master;"
    //   * If that works, we proceed. Otherwise, we ask for the password again.
    //
    // We have two databases, and we'll constrain them to have the same
    // password. Failure to align is an error.
    //
    // https://www.zetetic.net/sqlcipher/sqlcipher-api/

    user_cancelled_please_quit = false;
    bool encryption_happy = false;
    bool changed_user_password = false;
    const QString new_pw_text(tr("Enter a new password for the CamCOPS application"));
    const QString new_pw_title(tr("Set CamCOPS password"));
    const QString enter_pw_text(tr("Enter the password to unlock CamCOPS"));
    const QString enter_pw_title(tr("Enter CamCOPS password"));

    while (!encryption_happy) {
        changed_user_password = false;
        const bool no_password_sys = m_sysdb->canReadDatabase();
        const bool no_password_data = m_datadb->canReadDatabase();

        if (no_password_sys != no_password_data) {
            const QString msg = QString(
                        "CamCOPS uses a system and a data database; one has a "
                        "password and one doesn't (no_password_sys = %1, "
                        "no_password_data = %2); this is an incongruent state "
                        "that has probably arisen from user error, and "
                        "CamCOPS will not continue until this is fixed.")
                    .arg(no_password_sys)
                    .arg(no_password_data);
            const QString title = "Inconsistent database state";
            uifunc::stopApp(msg, title);
        }

        if (no_password_sys) {

            qInfo() << "Databases have no password yet, and need one.";
            QString dummy_old_password;
            if (!uifunc::getOldNewPasswords(
                        new_pw_text, new_pw_title, false,
                        dummy_old_password, new_user_password, nullptr)) {
                user_cancelled_please_quit = true;
                return false;
            }
            qInfo() << "Encrypting databases for the first time...";
            if (!m_sysdb->databaseIsEmpty() || !m_datadb->databaseIsEmpty()) {
                qInfo() << "... by rewriting the databases...";
                encryption_happy = encryptExistingPlaintextDatabases(new_user_password);
            } else {
                qInfo() << "... by encrypting empty databases...";
                encryption_happy = true;
            }
            changed_user_password = true;
            // Whether we've encrypted an existing database (then reopened it)
            // or just opened a fresh one, we need to apply the key now.
            encryption_happy = encryption_happy &&
                    m_sysdb->pragmaKey(new_user_password) &&
                    m_datadb->pragmaKey(new_user_password) &&
                    m_sysdb->canReadDatabase() &&
                    m_datadb->canReadDatabase();
            if (encryption_happy) {
                qInfo() << "... successfully encrypted the databases.";
            } else {
                qInfo() << "... failed to encrypt; trying again.";
            }

        } else {

            qInfo() << "Databases are encrypted. Requesting password from user.";
            QString user_password;
            if (!uifunc::getPassword(enter_pw_text, enter_pw_title,
                                     user_password, nullptr)) {
                user_cancelled_please_quit = true;
                return false;
            }
            qInfo() << "Attempting to decrypt databases...";
            encryption_happy =
                    m_sysdb->pragmaKey(user_password) &&
                    m_datadb->pragmaKey(user_password) &&
                    m_sysdb->canReadDatabase() &&
                    m_datadb->canReadDatabase();
            if (encryption_happy) {
                qInfo() << "... successfully accessed encrypted databases.";
            } else {
                qInfo() << "... failed to decrypt; asking for password again.";
            }

        }
    }
    // When we get here, the user has either encrypted the databases for the
    // first time, or decrypted an existing pair; either entitles them to
    // unlock the app.
    m_lockstate = LockState::Unlocked;
    return changed_user_password;
#else
    if (!dbfunc::canReadDatabase(m_sysdb)) {
        stopApp(tr("Can't read system database; corrupted? encrypted? (This "
                   "version of CamCOPS has had its encryption facilities "
                   "disabled."));
    }
    if (!dbfunc::canReadDatabase(m_datadb)) {
        stopApp(tr("Can't read data database; corrupted? encrypted? (This "
                   "version of CamCOPS has had its encryption facilities "
                   "disabled."));
    }
    return false;  // user password not changed
#endif
}


bool CamcopsApp::encryptExistingPlaintextDatabases(const QString& passphrase)
{
    using filefunc::fileExists;
    qInfo() << "... closing databases";
    closeDatabases();
    const QString sys_main = dbFullPath(dbfunc::SYSTEM_DATABASE_FILENAME);
    const QString sys_temp = dbFullPath(dbfunc::SYSTEM_DATABASE_FILENAME +
                                        dbfunc::DATABASE_FILENAME_TEMP_SUFFIX);
    const QString data_main = dbFullPath(dbfunc::DATA_DATABASE_FILENAME);
    const QString data_temp = dbFullPath(dbfunc::DATA_DATABASE_FILENAME +
                                         dbfunc::DATABASE_FILENAME_TEMP_SUFFIX);
    qInfo() << "... encrypting";
    dbfunc::encryptPlainDatabaseInPlace(sys_main, sys_temp, passphrase);
    dbfunc::encryptPlainDatabaseInPlace(data_main, data_temp, passphrase);
    qInfo() << "... re-opening databases";
    openOrCreateDatabases();
    return true;
}


void CamcopsApp::seedRng()
{
    // ------------------------------------------------------------------------
    // Seed Qt's build-in RNG, which we may use for QUuid generation
    // ------------------------------------------------------------------------
    // QUuid may, if /dev/urandom does not exist, use qrand(). It won't use
    // OpenSSL or anything else. So we'd better make sure it's seeded first:
    qsrand(QDateTime::currentMSecsSinceEpoch() & 0xffffffff);
    // QDateTime::currentMSecsSinceEpoch() -> qint64
    // qsrand wants uint (= uint32)
}


void CamcopsApp::makeStoredVarTable()
{
    // ------------------------------------------------------------------------
    // Make storedvar table
    // ------------------------------------------------------------------------

    StoredVar storedvar_specimen(*this, *m_sysdb);
    storedvar_specimen.makeTable();
    storedvar_specimen.makeIndexes();
}


void CamcopsApp::createStoredVars()
{
    // ------------------------------------------------------------------------
    // Create stored variables: name, type, default
    // ------------------------------------------------------------------------
    DbNestableTransaction trans(*m_sysdb);  // https://www.sqlite.org/faq.html#q19

    // Version
    createVar(varconst::CAMCOPS_TABLET_VERSION_AS_STRING, QVariant::String,
              camcopsversion::CAMCOPS_VERSION.toString());

    // Questionnaire
    createVar(varconst::QUESTIONNAIRE_SIZE_PERCENT, QVariant::Int, 100);

    // Server
    createVar(varconst::SERVER_ADDRESS, QVariant::String, "");
    createVar(varconst::SERVER_PORT, QVariant::Int, 443);  // 443 = HTTPS
    createVar(varconst::SERVER_PATH, QVariant::String, "camcops/database");
    createVar(varconst::SERVER_TIMEOUT_MS, QVariant::Int, 50000);
    createVar(varconst::VALIDATE_SSL_CERTIFICATES, QVariant::Bool, true);
    createVar(varconst::SSL_PROTOCOL, QVariant::String,
              convert::SSLPROTODESC_SECUREPROTOCOLS);
    createVar(varconst::DEBUG_USE_HTTPS_TO_SERVER, QVariant::Bool, true);
    createVar(varconst::STORE_SERVER_PASSWORD, QVariant::Bool, true);
#ifdef ALLOW_SEND_ANALYTICS
    createVar(varconst::SEND_ANALYTICS, QVariant::Bool, true);
#endif

    // Uploading "dirty" flag
    createVar(varconst::NEEDS_UPLOAD, QVariant::Bool, false);

    // Whisker
    createVar(varconst::WHISKER_HOST, QVariant::String, "localhost");
    createVar(varconst::WHISKER_PORT, QVariant::Int, 3233);  // 3233 = Whisker
    createVar(varconst::WHISKER_TIMEOUT_MS, QVariant::Int, 5000);

    // Terms and conditions
    createVar(varconst::AGREED_TERMS_AT, QVariant::DateTime);

    // Intellectual property
    createVar(varconst::IP_USE_CLINICAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
    createVar(varconst::IP_USE_COMMERCIAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
    createVar(varconst::IP_USE_EDUCATIONAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
    createVar(varconst::IP_USE_RESEARCH, QVariant::Int, CommonOptions::UNKNOWN_INT);

    // Patients and policies
    createVar(varconst::ID_POLICY_UPLOAD, QVariant::String, "");
    createVar(varconst::ID_POLICY_FINALIZE, QVariant::String, "");

    // Other information from server
    createVar(varconst::SERVER_DATABASE_TITLE, QVariant::String, "");
    createVar(varconst::SERVER_CAMCOPS_VERSION, QVariant::String, "");
    createVar(varconst::LAST_SERVER_REGISTRATION, QVariant::DateTime);
    createVar(varconst::LAST_SUCCESSFUL_UPLOAD, QVariant::DateTime);

    // User
    // ... server interaction
    createVar(varconst::DEVICE_FRIENDLY_NAME, QVariant::String, "");
    createVar(varconst::SERVER_USERNAME, QVariant::String, "");
    createVar(varconst::SERVER_USERPASSWORD_OBSCURED, QVariant::String, "");
    createVar(varconst::OFFER_UPLOAD_AFTER_EDIT, QVariant::Bool, false);
    // ... default clinician details
    createVar(varconst::DEFAULT_CLINICIAN_SPECIALTY, QVariant::String, "");
    createVar(varconst::DEFAULT_CLINICIAN_NAME, QVariant::String, "");
    createVar(varconst::DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION, QVariant::String, "");
    createVar(varconst::DEFAULT_CLINICIAN_POST, QVariant::String, "");
    createVar(varconst::DEFAULT_CLINICIAN_SERVICE, QVariant::String, "");
    createVar(varconst::DEFAULT_CLINICIAN_CONTACT_DETAILS, QVariant::String, "");

    // Cryptography
    createVar(varconst::OBSCURING_KEY, QVariant::String, "");
    createVar(varconst::OBSCURING_IV, QVariant::String, "");
    // setEncryptedServerPassword("hello I am a password");
    // qDebug() << getPlaintextServerPassword();
    createVar(varconst::USER_PASSWORD_HASH, QVariant::String, "");
    createVar(varconst::PRIV_PASSWORD_HASH, QVariant::String, "");

    // Device ID
    createVar(varconst::DEVICE_ID, QVariant::Uuid);
    if (var(varconst::DEVICE_ID).isNull()) {
        regenerateDeviceId();
    }
}


Version CamcopsApp::upgradeDatabaseBeforeTablesMade()
{
    const Version old_version(varString(varconst::CAMCOPS_TABLET_VERSION_AS_STRING));
    const Version new_version = camcopsversion::CAMCOPS_VERSION;
    if (old_version == new_version) {
        qInfo() << "Database is current; no special upgrade steps required";
        return old_version;
    }
    qInfo() << "Considering system-wide special database upgrade steps from "
               "version" << old_version << "to version" << new_version;

    // ------------------------------------------------------------------------
    // System-wide database upgrade steps go here
    // ------------------------------------------------------------------------

    // ------------------------------------------------------------------------
    // ... done
    // ------------------------------------------------------------------------

    qInfo() << "System-wide database upgrade steps complete";
    if (new_version != old_version) {
        setVar(varconst::CAMCOPS_TABLET_VERSION_AS_STRING, new_version.toString());
    }
    return old_version;
}


void CamcopsApp::upgradeDatabaseAfterTasksRegistered(const Version& old_version)
{
    // ------------------------------------------------------------------------
    // Any database upgrade required? STEP 2: INDIVIDUAL TASKS.
    // ------------------------------------------------------------------------
    const Version new_version = camcopsversion::CAMCOPS_VERSION;
    if (old_version == new_version) {
        // User message will have appeared above.
        return;
    }

    Q_ASSERT(m_p_task_factory);
    m_p_task_factory->upgradeDatabase(old_version, new_version);
}


void CamcopsApp::makeOtherSystemTables()
{
    // ------------------------------------------------------------------------
    // Make other tables
    // ------------------------------------------------------------------------

    // Make special tables: system database

    ExtraString extrastring_specimen(*this, *m_sysdb);
    extrastring_specimen.makeTable();
    extrastring_specimen.makeIndexes();

    AllowedServerTable allowedtable_specimen(*this, *m_sysdb);
    allowedtable_specimen.makeTable();
    allowedtable_specimen.makeIndexes();

    IdNumDescription idnumdesc_specimen(*this, *m_sysdb);
    idnumdesc_specimen.makeTable();
    idnumdesc_specimen.makeIndexes();

    // Make special tables: main database
    // - See also QStringList CamcopsApp::nonTaskTables()

    Blob blob_specimen(*this, *m_datadb);
    blob_specimen.makeTable();
    blob_specimen.makeIndexes();

    Patient patient_specimen(*this, *m_datadb);
    patient_specimen.makeTable();

    PatientIdNum patient_idnum_specimen(*this, *m_datadb);
    patient_idnum_specimen.makeTable();
}


void CamcopsApp::registerTasks()
{
    // ------------------------------------------------------------------------
    // Register tasks (AFTER storedvar creation, so tasks can read them)
    // ------------------------------------------------------------------------
    m_p_task_factory = TaskFactoryPtr(new TaskFactory(*this));
    InitTasks(*m_p_task_factory);  // ensures all tasks are registered
    m_p_task_factory->finishRegistration();
    const QStringList tablenames = m_p_task_factory->tablenames();
    qInfo().nospace() << "Registered tasks (n = " << tablenames.length()
                      << "): " << tablenames;
}


void CamcopsApp::makeTaskTables()
{
    // Make task tables
    m_p_task_factory->makeAllTables();
}


void CamcopsApp::initGuiOne()
{
    // Qt stuff: before storedvars accessible

    // Special for top-level window:
    setWindowIcon(QIcon(uifunc::iconFilename(uiconst::ICON_CAMCOPS)));

    const QList<QScreen*> all_screens = screens();
    if (all_screens.isEmpty()) {
        m_dpi = uiconst::DEFAULT_DPI;
    } else {
        const QScreen* screen = all_screens.at(0);
        m_dpi = screen->logicalDotsPerInch();
    }

    // This is slightly nasty, but it saves a great deal of things referring
    // to the CamcopsApp that otherwise wouldn't need to.
    qInfo() << "Resizing icons for" << m_dpi << "dpi display";
    uiconst::DPI = m_dpi;

    auto cvSize = [this](const QSize& size) -> QSize {
        return convert::convertSizeByDpi(size, m_dpi, uiconst::DEFAULT_DPI);
    };
    auto cvLength = [this](int length) -> int {
        return convert::convertLengthByDpi(length, m_dpi, uiconst::DEFAULT_DPI);
    };

    uiconst::ICONSIZE = cvSize(uiconst::ICONSIZE_FOR_DEFAULT_DPI);
    uiconst::SMALL_ICONSIZE = cvSize(uiconst::SMALL_ICONSIZE_FOR_DEFAULT_DPI);
    uiconst::MIN_SPINBOX_HEIGHT = cvLength(uiconst::MIN_SPINBOX_HEIGHT_FOR_DEFAULT_DPI);
    uiconst::SLIDER_HANDLE_SIZE_PX = cvLength(uiconst::SLIDER_HANDLE_SIZE_PX_FOR_DEFAULT_DPI);
    uiconst::DIAL_DIAMETER_PX = cvLength(uiconst::DIAL_DIAMETER_PX_FOR_DEFAULT_DPI);
}


qreal CamcopsApp::dotsPerInch() const
{
    return m_dpi;
}


void CamcopsApp::initGuiTwoStylesheet()
{
    // Qt stuff: after storedvars accessible
    setStyleSheet(getSubstitutedCss(uiconst::CSS_CAMCOPS_MAIN));
}


void CamcopsApp::openMainWindow()
{
    m_p_main_window = new QMainWindow();
    m_p_main_window->showMaximized();
    m_p_window_stack = new QStackedWidget(m_p_main_window);
    m_p_hidden_stack = QSharedPointer<QStackedWidget>(new QStackedWidget());
#if 0  // doesn't work
    // We want to stay height-for-width all the way to the top:
    VBoxLayout* master_layout = new VBoxLayout();
    m_p_main_window->setLayout(master_layout);
    master_layout->addWidget(m_p_window_stack);
#else
    m_p_main_window->setCentralWidget(m_p_window_stack);
#endif

    MainMenu* menu = new MainMenu(*this);
    open(menu);
}


void CamcopsApp::makeNetManager()
{
    Q_ASSERT(m_p_main_window.data());
    m_netmgr = QSharedPointer<NetworkManager>(
                new NetworkManager(*this, *m_datadb, m_p_task_factory,
                                   m_p_main_window.data()));
}


// ============================================================================
// Core
// ============================================================================

DatabaseManager& CamcopsApp::db()
{
    return *m_datadb;
}


DatabaseManager& CamcopsApp::sysdb()
{
    return *m_sysdb;
}


TaskFactory* CamcopsApp::taskFactory()
{
    return m_p_task_factory.data();
}


// ============================================================================
// Opening/closing windows
// ============================================================================

SlowGuiGuard CamcopsApp::getSlowGuiGuard(const QString& text,
                                         const QString& title,
                                         const int minimum_duration_ms)
{
    return SlowGuiGuard(*this, m_p_main_window, title, text,
                        minimum_duration_ms);
}


void CamcopsApp::open(OpenableWidget* widget, TaskPtr task,
                      const bool may_alter_task, PatientPtr patient)
{
    if (!widget) {
        qCritical() << Q_FUNC_INFO << "- attempt to open nullptr";
        return;
    }

    SlowGuiGuard guard = getSlowGuiGuard();

    Qt::WindowStates prev_window_state = m_p_main_window->windowState();
    QPointer<OpenableWidget> guarded_widget = widget;

#ifdef DEBUG_SCREEN_STACK
    qDebug() << Q_FUNC_INFO << "Pushing screen";
#endif

    // ------------------------------------------------------------------------
    // Transfer any visible items (should be 0 or 1!) to hidden stack
    // ------------------------------------------------------------------------
    while (m_p_window_stack->count() > 0) {
        QWidget* w = m_p_window_stack->widget(m_p_window_stack->count() - 1);
        if (w) {
            m_p_window_stack->removeWidget(w);  // m_p_window_stack still owns w
            m_p_hidden_stack->addWidget(w);  // m_p_hidden_stack now owns w
        }
    }


    // ------------------------------------------------------------------------
    // Add new thing to visible (one-item) "stack"
    // ------------------------------------------------------------------------
    int index = m_p_window_stack->addWidget(widget);  // will show the widget
    // The stack takes over ownership.

    // ------------------------------------------------------------------------
    // Build, if the OpenableWidget wants to be built
    // ------------------------------------------------------------------------
    // qDebug() << Q_FUNC_INFO << "About to build";
    widget->build();
    // qDebug() << Q_FUNC_INFO << "Build complete, about to show";

    // ------------------------------------------------------------------------
    // Make it visible; set the fullscreen state
    // ------------------------------------------------------------------------
    m_p_window_stack->setCurrentIndex(index);
    if (widget->wantsFullscreen()) {
        enterFullscreen();
    }

    // ------------------------------------------------------------------------
    // Signals
    // ------------------------------------------------------------------------
    connect(widget, &OpenableWidget::enterFullscreen,
            this, &CamcopsApp::enterFullscreen);
    connect(widget, &OpenableWidget::leaveFullscreen,
            this, &CamcopsApp::leaveFullscreen);
    connect(widget, &OpenableWidget::finished,
            this, &CamcopsApp::close);

    // ------------------------------------------------------------------------
    // Save information and manage ownership of associated things
    // ------------------------------------------------------------------------
    m_info_stack.push(OpenableInfo(guarded_widget, task, prev_window_state,
                                   may_alter_task, patient));
    // This stores a QSharedPointer to the task (if supplied), so keeping that
    // keeps the task "alive" whilst its widget is doing things.
    // Similarly with any patient required for patient editing.
}


void CamcopsApp::close()
{
    // ------------------------------------------------------------------------
    // All done?
    // ------------------------------------------------------------------------
    if (m_info_stack.isEmpty()) {
        uifunc::stopApp("CamcopsApp::close: No more windows; closing");
    }

    // ------------------------------------------------------------------------
    // Get saved info (and, at the end of this function, release ownerships)
    // ------------------------------------------------------------------------
    OpenableInfo info = m_info_stack.pop();
    // on function exit, will delete the task if it's the last pointer to it
    // (... and similarly any patient)

    // ------------------------------------------------------------------------
    // Get rid of the widget that's closing from the visible stack
    // ------------------------------------------------------------------------
    QWidget* top = m_p_window_stack->currentWidget();
#ifdef DEBUG_SCREEN_STACK
    qDebug() << Q_FUNC_INFO << "Popping screen";
#endif
    m_p_window_stack->removeWidget(top);
    // Ownership is returned to the application, so...
    // - AH, NO. OWNERSHIP IS CONFUSING AND THE DOCS ARE DIFFERENT IN QT 4.8
    //   AND 5.9
    // - From http://doc.qt.io/qt-4.8/qstackedwidget.html#removeWidget :
    //      Removes widget from the QStackedWidget. i.e., widget is not deleted
    //      but simply removed from the stacked layout, causing it to be hidden.
    //      Note: Ownership of widget reverts to the application.
    // - From http://doc.qt.io/qt-5/qstackedwidget.html#removeWidget :
    //      Removes widget from the QStackedWidget. i.e., widget is not deleted
    //      but simply removed from the stacked layout, causing it to be hidden.
    //      Note: Parent object and parent widget of widget will remain the
    //      QStackedWidget. If the application wants to reuse the removed
    //      widget, then it is recommended to re-parent it.
    // - Also:
    //   https://stackoverflow.com/questions/2506625/how-to-delete-a-widget-from-a-stacked-widget-in-qt
    // But this should work regardless:
    top->deleteLater();  // later, in case it was this object that called us

    // ------------------------------------------------------------------------
    // Restore the widget from the top of the hidden stack
    // ------------------------------------------------------------------------
    Q_ASSERT(m_p_hidden_stack->count() > 0);  // the m_info_stack.isEmpty() check should exclude this
    QWidget* w = m_p_hidden_stack->widget(m_p_hidden_stack->count() - 1);
    m_p_hidden_stack->removeWidget(w);  // m_p_hidden_stack still owns w
    int index = m_p_window_stack->addWidget(w);  // m_p_window_stack now owns w
    m_p_window_stack->setCurrentIndex(index);

    // ------------------------------------------------------------------------
    // Restore fullscreen state
    // ------------------------------------------------------------------------
    m_p_main_window->setWindowState(info.prev_window_state);

    // ------------------------------------------------------------------------
    // Update objects that care as to changes that may have been wrought
    // ------------------------------------------------------------------------
    if (info.may_alter_task) {
#ifdef DEBUG_EMIT
        qDebug() << Q_FUNC_INFO << "Emitting taskAlterationFinished";
#endif
        emit taskAlterationFinished(info.task);

        if (varBool(varconst::OFFER_UPLOAD_AFTER_EDIT) &&
                varBool(varconst::NEEDS_UPLOAD)) {
            ScrollMessageBox msgbox(
                        QMessageBox::Question,
                        tr("Upload?"),
                        tr("Task finished. Upload data to server now?"),
                        m_p_main_window);  // parent
            QAbstractButton* yes = msgbox.addButton(tr("Yes, upload"),
                                                    QMessageBox::YesRole);
            msgbox.addButton(tr("No, cancel"), QMessageBox::NoRole);
            msgbox.exec();
            if (msgbox.clickedButton() == yes) {
                upload();
            }
        }
    }
    if (info.patient) {
        // This happens if we've been editing a patient, so the patient details
        // may have changed.
        // Moreover, we do not have a guarantee that the copy of the patient
        // used by the task is the same as that we're holding. So we must
        // reload.
        int patient_id = info.patient->id();
        reloadPatient(patient_id);
#ifdef DEBUG_EMIT
        qDebug() << Q_FUNC_INFO
                 << "Emitting selectedPatientDetailsChanged for patient ID"
                 << patient_id;
#endif
        emit selectedPatientDetailsChanged(m_patient.data());
    }
}


void CamcopsApp::enterFullscreen()
{
    m_p_main_window->showFullScreen();
}


void CamcopsApp::leaveFullscreen()
{
    m_p_main_window->showNormal();
}


// ============================================================================
// Security
// ============================================================================

bool CamcopsApp::privileged() const
{
    return m_lockstate == LockState::Privileged;
}


bool CamcopsApp::locked() const
{
    return m_lockstate == LockState::Locked;
}


CamcopsApp::LockState CamcopsApp::lockstate() const
{
    return m_lockstate;
}


void CamcopsApp::setLockState(const LockState lockstate)
{
    const bool changed = lockstate != m_lockstate;
    m_lockstate = lockstate;
    if (changed) {
#ifdef DEBUG_EMIT
        qDebug() << "Emitting lockStateChanged";
#endif
        emit lockStateChanged(lockstate);
    }
}


void CamcopsApp::unlock()
{
    if (lockstate() == LockState::Privileged ||
            checkPassword(varconst::USER_PASSWORD_HASH,
                          tr("Enter app password"),
                          tr("Unlock"))) {
        setLockState(LockState::Unlocked);
    }
}


void CamcopsApp::lock()
{
    setLockState(LockState::Locked);
}


void CamcopsApp::grantPrivilege()
{
    if (checkPassword(varconst::PRIV_PASSWORD_HASH,
                      tr("Enter privileged-mode password"),
                      tr("Set privileged mode"))) {
        setLockState(LockState::Privileged);
    }
}


bool CamcopsApp::checkPassword(const QString& hashed_password_varname,
                               const QString& text, const QString& title)
{
    const QString hashed_password = varString(hashed_password_varname);
    if (hashed_password.isEmpty()) {
        // If there's no password, we just allow the operation.
        return true;
    }
    QString password;
    const bool ok = uifunc::getPassword(text, title, password, m_p_main_window);
    if (!ok) {
        return false;
    }
    const bool correct = cryptofunc::matchesHash(password, hashed_password);
    if (!correct) {
        uifunc::alert(tr("Wrong password"), title);
    }
    return correct;
}


void CamcopsApp::changeAppPassword()
{
    const QString title(tr("Change app password"));
#ifdef SQLCIPHER_ENCRYPTION_ON
    // We also use this password for database encryption, so we need to know
    // it briefly (in plaintext format) to reset the database encryption key.
    QString new_password;
    const bool changed = changePassword(varconst::USER_PASSWORD_HASH, title,
                                        nullptr, &new_password);
    if (changed) {
        SlowGuiGuard guard = getSlowGuiGuard(tr("Re-encrypting databases..."));
        qInfo() << "Re-encrypting system database...";
        m_sysdb->pragmaRekey(new_password);
        qInfo() << "Re-encrypting data database...";
        m_datadb->pragmaRekey(new_password);
        qInfo() << "Re-encryption finished.";
    }
#else
    changePassword(varconst::USER_PASSWORD_HASH, title);
#endif
}


void CamcopsApp::changePrivPassword()
{
    changePassword(varconst::PRIV_PASSWORD_HASH,
                   tr("Change privileged-mode password"));
}


bool CamcopsApp::changePassword(const QString& hashed_password_varname,
                                const QString& text,
                                QString* p_old_password,
                                QString* p_new_password)
{
    // Returns: changed?
    const QString old_password_hash = varString(hashed_password_varname);
    const bool old_password_exists = !old_password_hash.isEmpty();
    QString old_password_from_user;
    QString new_password;
    const bool ok = uifunc::getOldNewPasswords(
                text, text, old_password_exists,
                old_password_from_user, new_password,
                m_p_main_window);
    if (!ok) {
        return false;  // user cancelled
    }
    if (old_password_exists && !cryptofunc::matchesHash(old_password_from_user,
                                                        old_password_hash)) {
        uifunc::alert("Incorrect old password");
        return false;
    }
    if (p_old_password) {
        *p_old_password = old_password_from_user;
    }
    if (p_new_password) {
        *p_new_password = new_password;
    }
    setHashedPassword(hashed_password_varname, new_password);
    return true;
}


void CamcopsApp::setHashedPassword(const QString& hashed_password_varname,
                                   const QString& password)
{
    if (password.isEmpty()) {
        qWarning() << "Erasing password:" << hashed_password_varname;
        setVar(hashed_password_varname, "");
    } else {
        setVar(hashed_password_varname, cryptofunc::hash(password));
    }
}


bool CamcopsApp::storingServerPassword() const
{
    return varBool(varconst::STORE_SERVER_PASSWORD);
}


void CamcopsApp::setEncryptedServerPassword(const QString& password)
{
    qDebug() << Q_FUNC_INFO;
    DbNestableTransaction trans(*m_sysdb);
    resetEncryptionKeyIfRequired();
    const QString iv_b64(cryptofunc::generateIVBase64());  // new one each time
    setVar(varconst::OBSCURING_IV, iv_b64);
    const SecureQString key_b64(varString(varconst::OBSCURING_KEY));
    setVar(varconst::SERVER_USERPASSWORD_OBSCURED,
           cryptofunc::encryptToBase64(password, key_b64, iv_b64));
}


void CamcopsApp::resetEncryptionKeyIfRequired()
{
    qDebug() << Q_FUNC_INFO;
    SecureQString key(varString(varconst::OBSCURING_KEY));
    if (cryptofunc::isValidAesKey(key)) {
        return;
    }
    qInfo() << "Resetting internal encryption key (and wiping stored password)";
    setVar(varconst::OBSCURING_KEY, cryptofunc::generateObscuringKeyBase64());
    setVar(varconst::OBSCURING_IV, "");  // will be set by setEncryptedServerPassword
    setVar(varconst::SERVER_USERPASSWORD_OBSCURED, "");
}


SecureQString CamcopsApp::getPlaintextServerPassword() const
{
    QString encrypted_b64(varString(varconst::SERVER_USERPASSWORD_OBSCURED));
    if (encrypted_b64.isEmpty()) {
        return "";
    }
    const SecureQString key_b64(varString(varconst::OBSCURING_KEY));
    const QString iv_b64(varString(varconst::OBSCURING_IV));
    if (!cryptofunc::isValidAesKey(key_b64)) {
        qWarning() << "Unable to decrypt password; key is bad";
        return "";
    }
    if (!cryptofunc::isValidAesIV(iv_b64)) {
        qWarning() << "Unable to decrypt password; IV is bad";
        return "";
    }
    const QString plaintext(cryptofunc::decryptFromBase64(
                                encrypted_b64, key_b64, iv_b64));
#ifdef DANGER_DEBUG_PASSWORD_DECRYPTION
    qDebug() << Q_FUNC_INFO << "plaintext:" << plaintext;
#endif
    return plaintext;
}


QString CamcopsApp::deviceId() const
{
    return varString(varconst::DEVICE_ID);
}


void CamcopsApp::regenerateDeviceId()
{
    setVar(varconst::DEVICE_ID, QUuid::createUuid());
    // This is the RANDOM variant of a UUID, not a "hashed something" variant.
    // - http://doc.qt.io/qt-5/quuid.html#createUuid
    // - https://en.wikipedia.org/wiki/Universally_unique_identifier#Variants_and_versions
    // Note that we seeded Qt's own RNG in CamcopsApp::CamcopsApp.
}


// ============================================================================
// Network
// ============================================================================

NetworkManager* CamcopsApp::networkManager() const
{
    return m_netmgr.data();
}


bool CamcopsApp::needsUpload() const
{
    return varBool(varconst::NEEDS_UPLOAD);
}


void CamcopsApp::setNeedsUpload(const bool needs_upload)
{
    const bool changed = setVar(varconst::NEEDS_UPLOAD, needs_upload);
    if (changed) {
#ifdef DEBUG_EMIT
        qDebug() << "Emitting needsUploadChanged";
#endif
        emit needsUploadChanged(needs_upload);
    }
}


// ============================================================================
// Whisker
// ============================================================================

bool CamcopsApp::whiskerConnected() const
{
    return m_whisker_connected;
}


void CamcopsApp::setWhiskerConnected(const bool connected)
{
    const bool changed = connected != m_whisker_connected;
    m_whisker_connected = connected;
    if (changed) {
#ifdef DEBUG_EMIT
        qDebug() << "Emitting whiskerConnectionStateChanged";
#endif
        emit whiskerConnectionStateChanged(connected);
    }
}


// ============================================================================
// Patient
// ============================================================================

bool CamcopsApp::isPatientSelected() const
{
    return m_patient != nullptr;
}


void CamcopsApp::setSelectedPatient(const int patient_id)
{
    // We do this by ID so there's no confusion about who owns it; we own
    // our own private copy here.
    const bool changed = patient_id != selectedPatientId();
    if (changed) {
        reloadPatient(patient_id);
#ifdef DEBUG_EMIT
        qDebug() << Q_FUNC_INFO << "emitting selectedPatientChanged "
                                   "for patient_id" << patient_id;
#endif
        emit selectedPatientChanged(m_patient.data());
    }
}


void CamcopsApp::deselectPatient()
{
    setSelectedPatient(dbconst::NONEXISTENT_PK);
}


void CamcopsApp::reloadPatient(const int patient_id)
{
    if (patient_id == dbconst::NONEXISTENT_PK) {
        m_patient.clear();
    } else {
        m_patient.reset(new Patient(*this, *m_datadb, patient_id));
    }
}


void CamcopsApp::patientHasBeenEdited(const int patient_id)
{
    const int current_patient_id = selectedPatientId();
    if (patient_id == current_patient_id) {
        reloadPatient(patient_id);
#ifdef DEBUG_EMIT
        qDebug() << Q_FUNC_INFO << "Emitting selectedPatientDetailsChanged "
                                   "for patient ID" << patient_id;
#endif
        emit selectedPatientDetailsChanged(m_patient.data());
    }
}


Patient* CamcopsApp::selectedPatient() const
{
    return m_patient.data();
}


int CamcopsApp::selectedPatientId() const
{
    return m_patient ? m_patient->id() : dbconst::NONEXISTENT_PK;
}


PatientPtrList CamcopsApp::getAllPatients(const bool sorted)
{
    PatientPtrList patients;
    Patient specimen(*this, *m_datadb, dbconst::NONEXISTENT_PK);  // this is why function can't be const
    const WhereConditions where;  // but we don't specify any
    const SqlArgs sqlargs = specimen.fetchQuerySql(where);
    const QueryResult result = m_datadb->query(sqlargs);
    const int nrows = result.nRows();
    for (int row = 0; row < nrows; ++row) {
        PatientPtr p(new Patient(*this, *m_datadb, dbconst::NONEXISTENT_PK));
        p->setFromQuery(result, row, true);
        patients.append(p);
    }
    if (sorted) {
        qSort(patients.begin(), patients.end(), PatientSorter());
    }
    return patients;
}


// ============================================================================
// CSS convenience; fonts etc.
// ============================================================================

QString CamcopsApp::getSubstitutedCss(const QString& filename) const
{
    const int p1_normal_font_size_pt = fontSizePt(uiconst::FontSize::Normal);
    const int p2_big_font_size_pt = fontSizePt(uiconst::FontSize::Big);
    const int p3_heading_font_size_pt = fontSizePt(uiconst::FontSize::Heading);
    const int p4_title_font_size_pt = fontSizePt(uiconst::FontSize::Title);
    const int p5_menu_font_size_pt = fontSizePt(uiconst::FontSize::Menus);
    const int p6_slider_groove_size_px = uiconst::SLIDER_HANDLE_SIZE_PX / 2;
    const int p7_slider_handle_size_px = uiconst::SLIDER_HANDLE_SIZE_PX;

#ifdef DEBUG_CSS_SIZES
    qDebug().nospace()
            << "CSS substituted sizes (for filename=" << filename
            << ", DPI=" << m_dpi << "): "
            << "p1_normal_font_size_pt = " << p1_normal_font_size_pt
            << ", p2_big_font_size_pt = " << p2_big_font_size_pt
            << ", p3_heading_font_size_pt = " << p3_heading_font_size_pt
            << ", p4_title_font_size_pt = " << p4_title_font_size_pt
            << ", p5_menu_font_size_pt = " << p5_menu_font_size_pt
            << ", p6_slider_groove_size_px = " << p6_slider_groove_size_px
            << ", p7_slider_handle_size_px = " << p7_slider_handle_size_px;
#endif

    return (
        filefunc::textfileContents(filename)
            .arg(p1_normal_font_size_pt)     // %1
            .arg(p2_big_font_size_pt)        // %2
            .arg(p3_heading_font_size_pt)    // %3
            .arg(p4_title_font_size_pt)      // %4
            .arg(p5_menu_font_size_pt)       // %5
            .arg(p6_slider_groove_size_px)   // %6: groove
            .arg(p7_slider_handle_size_px)   // %7: handle
    );
}


int CamcopsApp::fontSizePt(uiconst::FontSize fontsize,
                           const double factor_pct) const
{
    double factor;
    if (factor_pct <= 0) {
        factor = var(varconst::QUESTIONNAIRE_SIZE_PERCENT).toDouble() / 100;
    } else {
        // Custom percentage passed in; use that
        factor = double(factor_pct) / 100;
    }

    switch (fontsize) {
    case uiconst::FontSize::Normal:
        return factor * 12;
    case uiconst::FontSize::Big:
        return factor * 14;
    case uiconst::FontSize::Heading:
        return factor * 16;
    case uiconst::FontSize::Title:
        return factor * 16;
    case uiconst::FontSize::Menus:
    default:
        return factor * 12;
    }
}


// ============================================================================
// Server info
// ============================================================================

Version CamcopsApp::serverVersion() const
{
    return Version(varString(varconst::SERVER_CAMCOPS_VERSION));
}


IdPolicy CamcopsApp::uploadPolicy() const
{
    return IdPolicy(varString(varconst::ID_POLICY_UPLOAD));
}


IdPolicy CamcopsApp::finalizePolicy() const
{
    return IdPolicy(varString(varconst::ID_POLICY_FINALIZE));
}


QPair<QString, QString> CamcopsApp::idDescriptionDirect(const int which_idnum)  // desc, shortdesc
{
    IdNumDescription idnumdesc(*this, *m_sysdb, which_idnum);
    if (!idnumdesc.exists()) {
        QString failure = dbconst::UNKNOWN_IDNUM_DESC.arg(which_idnum);
        return QPair<QString, QString>(failure, failure);
    }
    return QPair<QString, QString>(idnumdesc.description(),
                                   idnumdesc.shortDescription());
}


QPair<QString, QString> CamcopsApp::idDescShortDesc(const int which_idnum)
{
    if (!m_iddescription_cache.contains(which_idnum)) {
        m_iddescription_cache[which_idnum] = idDescriptionDirect(which_idnum);
    }
    return m_iddescription_cache[which_idnum];
}


QString CamcopsApp::idDescription(const int which_idnum)
{
    const QPair<QString, QString> desc_shortdesc = idDescShortDesc(which_idnum);
    return desc_shortdesc.first;
}


QString CamcopsApp::idShortDescription(const int which_idnum)
{
    const QPair<QString, QString> desc_shortdesc = idDescShortDesc(which_idnum);
    return desc_shortdesc.second;
}


void CamcopsApp::clearIdDescriptionCache()
{
    m_iddescription_cache.clear();
}


void CamcopsApp::deleteAllIdDescriptions()
{
    IdNumDescription idnumdesc_specimen(*this, *m_sysdb);
    idnumdesc_specimen.deleteAllDescriptions();
    clearIdDescriptionCache();
}


bool CamcopsApp::setIdDescription(const int which_idnum, const QString& desc,
                                  const QString& shortdesc)
{
//    qDebug().nospace()
//            << "Setting ID descriptions for which_idnum==" << which_idnum
//            << " to " << desc << ", " << shortdesc;
    IdNumDescription idnumdesc(*this, *m_sysdb, which_idnum);
    const bool success = idnumdesc.setDescriptions(desc, shortdesc);
    if (success) {
        idnumdesc.save();
    }
    clearIdDescriptionCache();
    return success;
}


QVector<IdNumDescriptionPtr> CamcopsApp::getAllIdDescriptions()
{
    const OrderBy order_by{{IdNumDescription::FN_IDNUM, true}};
    QVector<IdNumDescriptionPtr> descriptions;
    ancillaryfunc::loadAllRecords<IdNumDescription, IdNumDescriptionPtr>
            (descriptions, *this, *m_sysdb, order_by);
    return descriptions;
}


QVector<int> CamcopsApp::whichIdNumsAvailable()
{
    QVector<int> which_available;
    for (IdNumDescriptionPtr iddesc : getAllIdDescriptions()) {
        which_available.append(iddesc->whichIdNum());
    }
    return which_available;
}


// ============================================================================
// Extra strings (downloaded from server)
// ============================================================================

QString CamcopsApp::xstringDirect(const QString& taskname,
                                  const QString& stringname,
                                  const QString& default_str)
{
    ExtraString extrastring(*this, *m_sysdb, taskname, stringname);
    const bool found = extrastring.exists();
    if (found) {
        QString result = extrastring.value();
        stringfunc::toHtmlLinebreaks(result);
        return result;
    } else {
        if (default_str.isEmpty()) {
            return QString("[string not downloaded: %1/%2]")
                    .arg(taskname, stringname);
        } else {
            return default_str;
        }
    }
}


QString CamcopsApp::xstring(const QString& taskname,
                            const QString& stringname,
                            const QString& default_str)
{
    const QPair<QString, QString> key(taskname, stringname);
    if (!m_extrastring_cache.contains(key)) {
        m_extrastring_cache[key] = xstringDirect(taskname, stringname,
                                                 default_str);
    }
    return m_extrastring_cache[key];
}


bool CamcopsApp::hasExtraStrings(const QString& taskname)
{
    ExtraString extrastring_specimen(*this, *m_sysdb);
    return extrastring_specimen.anyExist(taskname);
}


void CamcopsApp::clearExtraStringCache()
{
    m_extrastring_cache.clear();
}


void CamcopsApp::deleteAllExtraStrings()
{
    ExtraString extrastring_specimen(*this, *m_sysdb);
    extrastring_specimen.deleteAllExtraStrings();
    clearExtraStringCache();
}


void CamcopsApp::setAllExtraStrings(const RecordList& recordlist)
{
    DbNestableTransaction trans(*m_sysdb);
    deleteAllExtraStrings();
    for (auto record : recordlist) {
        if (!record.contains(ExtraString::TASK_FIELD) ||
                !record.contains(ExtraString::NAME_FIELD) ||
                !record.contains(ExtraString::VALUE_FIELD)) {
            qWarning() << Q_FUNC_INFO << "Failing: recordlist has bad format";
            trans.fail();
            return;
        }
        const QString task = record[ExtraString::TASK_FIELD].toString();
        const QString name = record[ExtraString::NAME_FIELD].toString();
        const QString value = record[ExtraString::VALUE_FIELD].toString();
        if (task.isEmpty() || name.isEmpty()) {
            qWarning() << Q_FUNC_INFO
                       << "Failing: extra string has blank task or name";
            trans.fail();
            return;
        }
        ExtraString extrastring(*this, *m_sysdb, task, name, value);
        // ... special constructor that doesn't attempt to load
        extrastring.saveWithoutKeepingPk();
    }
    // Took e.g. a shade under 10 s to save whilst keeping PK, down to ~1s
    // using a save-blindly-in-background method like this.
}


QString CamcopsApp::appstring(const QString& stringname,
                              const QString& default_str)
{
    return xstring(APPSTRING_TASKNAME, stringname, default_str);
}


// ============================================================================
// Allowed tables on the server
// ============================================================================

void CamcopsApp::deleteAllowedServerTables()
{
    AllowedServerTable allowedtable_specimen(*this, *m_sysdb);
    allowedtable_specimen.deleteAllAllowedServerTables();
}


void CamcopsApp::setAllowedServerTables(const RecordList& recordlist)
{
    DbNestableTransaction trans(*m_sysdb);
    deleteAllowedServerTables();
    for (auto record : recordlist) {
        if (!record.contains(AllowedServerTable::TABLENAME_FIELD) ||
                !record.contains(AllowedServerTable::VERSION_FIELD)) {
            qWarning() << Q_FUNC_INFO << "Failing: recordlist has bad format";
            trans.fail();
            return;
        }
        const QString tablename = record[AllowedServerTable::TABLENAME_FIELD].toString();
        const Version min_client_version = Version::fromString(
                    record[AllowedServerTable::VERSION_FIELD].toString());
        if (tablename.isEmpty()) {
            qWarning() << Q_FUNC_INFO
                       << "Failing: allowed table has blank tablename";
            trans.fail();
            return;
        }
        AllowedServerTable allowedtable(*this, *m_sysdb,
                                        tablename, min_client_version);
        // ... special constructor that doesn't attempt to load
        allowedtable.saveWithoutKeepingPk();
    }
}


bool CamcopsApp::mayUploadTable(const QString& tablename,
                                const Version& server_version,
                                bool& server_has_table,
                                Version& min_client_version,
                                Version& min_server_version)
{
    // We always write all three return-by-reference values.
    min_server_version = minServerVersionForTable(tablename);
    AllowedServerTable allowedtable(*this, *m_sysdb, tablename);
    server_has_table = allowedtable.exists();
    if (!server_has_table) {
        min_client_version = Version::makeInvalidVersion();
        return false;
    } else {
        min_client_version = allowedtable.minClientVersion();
    }
    return camcopsversion::CAMCOPS_VERSION >= min_client_version &&
            server_version >= min_server_version;
}


QStringList CamcopsApp::nonTaskTables() const
{
    // See also CamcopsApp::makeOtherSystemTables()
    return QStringList{
        Blob::TABLENAME,
        Patient::TABLENAME,
        PatientIdNum::PATIENT_IDNUM_TABLENAME
    };
}


Version CamcopsApp::minServerVersionForTable(const QString& tablename)
{
    const QStringList non_task_tables = nonTaskTables();
    if (non_task_tables.contains(tablename)) {
        return camcopsversion::MINIMUM_SERVER_VERSION;
        // generic minimum version
    }
    TaskFactory* factory = taskFactory();
    return factory->minimumServerVersion(tablename);
}



// ============================================================================
// Stored variables: generic
// ============================================================================

void CamcopsApp::createVar(const QString &name, QVariant::Type type,
                           const QVariant& default_value)
{
    if (name.isEmpty()) {
        uifunc::stopApp("Empty name to createVar");
    }
    if (m_storedvars.contains(name)) {  // Already exists
        return;
    }
    m_storedvars[name] = StoredVarPtr(
        new StoredVar(*this, *m_sysdb, name, type, default_value));
}


bool CamcopsApp::setVar(const QString& name, const QVariant& value,
                        const bool save_to_db)
{
    // returns: changed?
    if (!m_storedvars.contains(name)) {
        uifunc::stopApp(QString("CamcopsApp::setVar: Attempt to set "
                                "nonexistent storedvar: %1").arg(name));
    }
    return m_storedvars[name]->setValue(value, save_to_db);
}


QVariant CamcopsApp::var(const QString& name) const
{
    if (!m_storedvars.contains(name)) {
        uifunc::stopApp(QString("CamcopsApp::var: Attempt to get nonexistent "
                                "storedvar: %1").arg(name));
    }
    return m_storedvars[name]->value();
}


QString CamcopsApp::varString(const QString &name) const
{
    return var(name).toString();
}


bool CamcopsApp::varBool(const QString &name) const
{
    return var(name).toBool();
}


int CamcopsApp::varInt(const QString &name) const
{
    return var(name).toInt();
}


bool CamcopsApp::hasVar(const QString &name) const
{
    return m_storedvars.contains(name);
}


FieldRefPtr CamcopsApp::storedVarFieldRef(const QString& name,
                                          const bool mandatory,
                                          const bool cached)
{
    return FieldRefPtr(new FieldRef(this, name, mandatory, cached));
}


void CamcopsApp::clearCachedVars()
{
    m_cachedvars.clear();
}


void CamcopsApp::saveCachedVars()
{
    DbNestableTransaction trans(*m_sysdb);
    QMapIterator<QString, QVariant> i(m_cachedvars);
    while (i.hasNext()) {
        i.next();
        QString varname = i.key();
        QVariant value = i.value();
        (void) setVar(varname, value);  // ignores return value (changed)
    }
    clearCachedVars();
}


QVariant CamcopsApp::getCachedVar(const QString& name) const
{
    if (!m_cachedvars.contains(name)) {
        m_cachedvars[name] = var(name);
    }
    return m_cachedvars[name];
}


bool CamcopsApp::setCachedVar(const QString& name, const QVariant& value)
{
    if (!m_cachedvars.contains(name)) {
        m_cachedvars[name] = var(name);
    }
    const bool changed = value != m_cachedvars[name];
    m_cachedvars[name] = value;
    return changed;
}


bool CamcopsApp::cachedVarChanged(const QString& name) const
{
    if (!m_cachedvars.contains(name)) {
        return false;
    }
    return m_cachedvars[name] != var(name);
}


// ============================================================================
// Terms and conditions
// ============================================================================

bool CamcopsApp::hasAgreedTerms() const
{
    return !var(varconst::AGREED_TERMS_AT).isNull();
}


QDateTime CamcopsApp::agreedTermsAt() const
{
    return var(varconst::AGREED_TERMS_AT).toDateTime();
}


void CamcopsApp::offerTerms()
{
    ScrollMessageBox msgbox(QMessageBox::Question,
                            tr("Terms and conditions of use"),
                            textconst::TERMS_CONDITIONS,
                            m_p_main_window);
    // Keep agree/disagree message short, for phones:
    QAbstractButton* yes = msgbox.addButton(tr("I AGREE"), QMessageBox::YesRole);
    msgbox.addButton(tr("I DO NOT AGREE"), QMessageBox::NoRole);
    // It's hard work to remove the Close button from the dialog, but that is
    // interpreted as rejection, so that's OK.
    // - http://www.qtcentre.org/threads/41269-disable-close-button-in-QMessageBox

    msgbox.exec();
    if (msgbox.clickedButton() == yes) {
        // Agreed terms
        setVar(varconst::AGREED_TERMS_AT, QDateTime::currentDateTime());
    } else {
        // Refused terms
        uifunc::stopApp(tr("OK. Goodbye."), tr("You refused the conditions."));
    }
}


// ============================================================================
// Uploading
// ============================================================================

void CamcopsApp::upload()
{
    QString text =
            "Copy data to server, or move it to server?\n"
            "\n"
            "COPY: copies unfinished patients, moves finished patients.\n"
            "MOVE: moves all patients and their data.\n"
            "KEEP PATIENTS AND MOVE: moves all task data, keeps only basic "
            "patient details (for adding more tasks later).\n"
            "\n"
            "Please MOVE whenever possible; this reduces the amount of "
            "patient-identifiable information stored on this device.";
    ScrollMessageBox msgbox(QMessageBox::Question,
                            tr("Upload to server"),
                            text,
                            m_p_main_window);
    QAbstractButton* copy = msgbox.addButton(tr("Copy"), QMessageBox::YesRole);
    QAbstractButton* move_keep = msgbox.addButton(tr("Keep patients and move"), QMessageBox::NoRole);
    QAbstractButton* move = msgbox.addButton(tr("Move"), QMessageBox::AcceptRole);  // e.g. OK
    msgbox.addButton(tr("Cancel"), QMessageBox::RejectRole);  // e.g. Cancel
    msgbox.exec();
    NetworkManager::UploadMethod method;
    QAbstractButton* reply = msgbox.clickedButton();
    if (reply == copy) {
        method = NetworkManager::UploadMethod::Copy;
    } else if (reply == move_keep) {
        method = NetworkManager::UploadMethod::MoveKeepingPatients;
    } else if (reply == move) {
        method = NetworkManager::UploadMethod::Move;
    } else {
        return;
    }
    NetworkManager* netmgr = networkManager();
    netmgr->upload(method);
}


// ============================================================================
// App strings, or derived
// ============================================================================

NameValueOptions CamcopsApp::nhsPersonMaritalStatusCodeOptions()
{
    return NameValueOptions{
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_S), "S"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_M), "M"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_D), "D"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_W), "W"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_P), "P"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_N), "N"}
    };
}


NameValueOptions CamcopsApp::nhsEthnicCategoryCodeOptions()
{
    return NameValueOptions{
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_A), "A"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_B), "B"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_C), "C"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_D), "D"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_E), "E"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_F), "F"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_G), "G"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_H), "H"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_J), "J"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_K), "K"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_L), "L"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_M), "M"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_N), "N"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_P), "P"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_R), "R"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_S), "S"},
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_Z), "Z"}
    };
}
