/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

// #define DANGER_DEBUG_PASSWORD_DECRYPTION
// #define DANGER_DEBUG_WIPE_PASSWORDS
// #define DEBUG_EMIT
// #define TEST_CONVERSIONS

#include "camcopsapp.h"
#include <QApplication>
#include <QDateTime>
#include <QDebug>
#include <QIcon>
#include <QMainWindow>
#include <QMessageBox>
#include <QSqlDatabase>
#include <QSqlDriverCreator>
#include <QStackedWidget>
#include <QUuid>
#include "common/appstrings.h"
#include "common/camcopsversion.h"
#include "common/dbconstants.h"  // for NONEXISTENT_PK
#include "common/textconst.h"
#include "common/varconst.h"
#include "common/version.h"
#include "crypto/cryptofunc.h"
#include "db/dbfunc.h"
#include "db/dbnestabletransaction.h"
#include "db/dbtransaction.h"
#include "db/dumpsql.h"
#include "db/whichdb.h"
#include "dbobjects/blob.h"
#include "dbobjects/extrastring.h"
#include "dbobjects/patientsorter.h"
#include "dbobjects/storedvar.h"
#include "lib/convert.h"
#include "lib/datetime.h"
#include "lib/filefunc.h"
#include "lib/idpolicy.h"
#include "lib/networkmanager.h"
#include "lib/slowguiguard.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "menu/mainmenu.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "tasklib/inittasks.h"

#ifdef USE_SQLCIPHER
#include "db/sqlcipherdriver.h"
#endif

const QString APPSTRING_TASKNAME("camcops");  // task name used for generic but downloaded tablet strings
const QString CONNECTION_DATA("data");
const QString CONNECTION_SYS("sys");


CamcopsApp::CamcopsApp(int& argc, char *argv[]) :
    QApplication(argc, argv),
    m_p_task_factory(nullptr),
    m_lockstate(LockState::Locked),  // default unless we get in via encryption password
    m_whisker_connected(false),
    m_p_main_window(nullptr),
    m_p_window_stack(nullptr),
    m_patient(nullptr),
    m_netmgr(nullptr)
{
}


CamcopsApp::~CamcopsApp()
{
    // http://doc.qt.io/qt-5.7/objecttrees.html
    // Only delete things that haven't been assigned a parent
    delete m_p_main_window;
}


int CamcopsApp::run()
{
    announceStartup();
    seedRng();
    convert::registerQVectorTypesForQVariant();
#ifdef TEST_CONVERSIONS
    convert::testConversions();
#endif
    initGuiOne();
    registerDatabaseDrivers();
    openOrCreateDatabases();
    QString new_user_password;
    bool user_cancelled_please_quit;
    bool changed_user_password = connectDatabaseEncryption(
                new_user_password, user_cancelled_please_quit);
    if (user_cancelled_please_quit) {
        qCritical() << "User cancelled attempt";
        return 0;  // will quit
    }
    makeStoredVarTable();
    createStoredVars();

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

    upgradeDatabase();
    makeOtherSystemTables();
    registerTasks();  // AFTER storedvar creation, so tasks can read them
    makeTaskTables();
    initGuiTwo();  // AFTER storedvar creation
    openMainWindow();
    if (!hasAgreedTerms()) {
        offerTerms();
    }
    qInfo() << "Starting Qt event processor...";
    return exec();  // Main Qt event loop
}


// ============================================================================
// Initialization
// ============================================================================

void CamcopsApp::announceStartup()
{
    // ------------------------------------------------------------------------
    // Announce startup
    // ------------------------------------------------------------------------
    QDateTime dt = datetime::now();
    qInfo() << "CamCOPS starting at:"
            << qUtf8Printable(datetime::datetimeToIsoMs(dt))
            << "=" << qUtf8Printable(datetime::datetimeToIsoMsUtc(dt));
    qInfo() << "CamCOPS version:" << camcopsversion::CAMCOPS_VERSION;
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


void CamcopsApp::openOrCreateDatabases()
{
    // ------------------------------------------------------------------------
    // Create databases
    // ------------------------------------------------------------------------
    // We can't do things like opening the database until we have
    // created the app. So don't open the database in the initializer list!
    // Database lifetime:
    // http://stackoverflow.com/questions/7669987/what-is-the-correct-way-of-qsqldatabase-qsqlquery

    m_datadb = QSqlDatabase::addDatabase(whichdb::DBTYPE, CONNECTION_DATA);
    dbfunc::openDatabaseOrDie(m_datadb, dbfunc::DATA_DATABASE_FILENAME);

    m_sysdb = QSqlDatabase::addDatabase(whichdb::DBTYPE, CONNECTION_SYS);
    dbfunc::openDatabaseOrDie(m_sysdb, dbfunc::SYSTEM_DATABASE_FILENAME);
}


void CamcopsApp::closeDatabases()
{
    // http://stackoverflow.com/questions/9519736/warning-remove-database
    // http://www.qtcentre.org/archive/index.php/t-40358.html
    m_sysdb.close();
    m_sysdb = QSqlDatabase();
    QSqlDatabase::removeDatabase(CONNECTION_SYS);

    m_datadb.close();
    m_datadb = QSqlDatabase();
    QSqlDatabase::removeDatabase(CONNECTION_DATA);
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

    bool encryption_happy = false;
    bool changed_user_password = false;
    QString new_pw_text(tr("Enter a new password for the CamCOPS application"));
    QString new_pw_title(tr("Set CamCOPS password"));
    QString enter_pw_text(tr("Enter the password to unlock CamCOPS"));
    QString enter_pw_title(tr("Enter CamCOPS password"));

    while (!encryption_happy) {
        changed_user_password = false;
        bool no_password_sys = dbfunc::canReadDatabase(m_sysdb);
        bool no_password_data = dbfunc::canReadDatabase(m_datadb);

        if (no_password_sys != no_password_data) {
            QString msg = QString(
                        "CamCOPS uses a system and a data database; one has a "
                        "password and one doesn't; this is an incongruent state "
                        "that has probably arisen from user error, and CamCOPS "
                        "will not continue until this is fixed (no_password_sys = "
                        "%1, no_password_data = %2")
                    .arg(no_password_sys)
                    .arg(no_password_data);
            QString title = "Inconsistent database state";
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
            if (!dbfunc::databaseIsEmpty(m_sysdb) || !dbfunc::databaseIsEmpty(m_datadb)) {
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
                    dbfunc::pragmaKey(m_sysdb, new_user_password) &&
                    dbfunc::pragmaKey(m_datadb, new_user_password) &&
                    dbfunc::canReadDatabase(m_sysdb) &&
                    dbfunc::canReadDatabase(m_datadb);
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
                    dbfunc::pragmaKey(m_sysdb, user_password) &&
                    dbfunc::pragmaKey(m_datadb, user_password) &&
                    dbfunc::canReadDatabase(m_sysdb) &&
                    dbfunc::canReadDatabase(m_datadb);
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
    QString sys_main = dbfunc::dbFullPath(dbfunc::SYSTEM_DATABASE_FILENAME);
    QString sys_temp = dbfunc::dbFullPath(dbfunc::SYSTEM_DATABASE_FILENAME +
                                          dbfunc::DATABASE_FILENAME_TEMP_SUFFIX);
    QString data_main = dbfunc::dbFullPath(dbfunc::DATA_DATABASE_FILENAME);
    QString data_temp = dbfunc::dbFullPath(dbfunc::DATA_DATABASE_FILENAME +
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

    StoredVar storedvar_specimen(*this, m_sysdb);
    storedvar_specimen.makeTable();
    storedvar_specimen.makeIndexes();
}


void CamcopsApp::createStoredVars()
{
    // ------------------------------------------------------------------------
    // Create stored variables: name, type, default
    // ------------------------------------------------------------------------
    DbTransaction trans(m_sysdb);  // https://www.sqlite.org/faq.html#q19

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
    createVar(varconst::SEND_ANALYTICS, QVariant::Bool, true);

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

    // Patient-related device-wide settings
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        QString desc = dbconst::IDDESC_FIELD_FORMAT.arg(n);
        QString shortdesc = dbconst::IDSHORTDESC_FIELD_FORMAT.arg(n);
        createVar(desc, QVariant::String);
        createVar(shortdesc, QVariant::String);
    }

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


void CamcopsApp::upgradeDatabase()
{
    // ------------------------------------------------------------------------
    // Any database upgrade required?
    // ------------------------------------------------------------------------

    Version old_version(varString(varconst::CAMCOPS_TABLET_VERSION_AS_STRING));
    Version new_version = camcopsversion::CAMCOPS_VERSION;
    upgradeDatabase(old_version, new_version);
    if (new_version != old_version) {
        setVar(varconst::CAMCOPS_TABLET_VERSION_AS_STRING, new_version.toString());
    }
}


void CamcopsApp::upgradeDatabase(const Version& old_version,
                                 const Version& new_version)
{
    if (old_version == new_version) {
        qInfo() << "Database is current; no special upgrade steps required";
        return;
    }
    qInfo() << "Considering special database upgrade steps from version"
            << old_version << "to version" << new_version;

    // Do things: (a) system-wide

    // Do things: (b) individual tasks
    m_p_task_factory->upgradeDatabase(old_version, new_version);

    qInfo() << "Special database upgrade steps complete";
    return;
}


void CamcopsApp::makeOtherSystemTables()
{
    // ------------------------------------------------------------------------
    // Make other tables
    // ------------------------------------------------------------------------

    // Make special tables: system database
    ExtraString extrastring_specimen(*this, m_sysdb);
    extrastring_specimen.makeTable();
    extrastring_specimen.makeIndexes();

    // Make special tables: main database
    Blob blob_specimen(*this, m_datadb);
    blob_specimen.makeTable();
    blob_specimen.makeIndexes();

    Patient patient_specimen(*this, m_datadb);
    patient_specimen.makeTable();
}


void CamcopsApp::registerTasks()
{
    // ------------------------------------------------------------------------
    // Register tasks (AFTER storedvar creation, so tasks can read them)
    // ------------------------------------------------------------------------
    m_p_task_factory = TaskFactoryPtr(new TaskFactory(*this));
    InitTasks(*m_p_task_factory);  // ensures all tasks are registered
    m_p_task_factory->finishRegistration();
    qInfo() << "Registered tasks:" << m_p_task_factory->tablenames();

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
}


void CamcopsApp::initGuiTwo()
{
    // Qt stuff: after storedvars accessible
    setStyleSheet(getSubstitutedCss(uiconst::CSS_CAMCOPS_MAIN));
}


void CamcopsApp::openMainWindow()
{
    m_p_main_window = new QMainWindow();
    m_p_main_window->showMaximized();
    m_p_window_stack = new QStackedWidget(m_p_main_window);
    m_p_main_window->setCentralWidget(m_p_window_stack);

    m_netmgr = QSharedPointer<NetworkManager>(
                new NetworkManager(*this, m_datadb, m_p_task_factory,
                                   m_p_main_window.data()));

    MainMenu* menu = new MainMenu(*this);
    open(menu);
}

// ============================================================================
// Core
// ============================================================================

QSqlDatabase& CamcopsApp::db()
{
    return m_datadb;
}


QSqlDatabase& CamcopsApp::sysdb()
{
    return m_sysdb;
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
                                         int minimum_duration_ms)
{
    return SlowGuiGuard(*this, m_p_main_window, title, text,
                        minimum_duration_ms);
}


void CamcopsApp::open(OpenableWidget* widget, TaskPtr task,
                      bool may_alter_task, PatientPtr patient)
{
    if (!widget) {
        qCritical() << Q_FUNC_INFO << "- attempt to open nullptr";
        return;
    }

    SlowGuiGuard guard = getSlowGuiGuard();

    Qt::WindowStates prev_window_state = m_p_main_window->windowState();
    QPointer<OpenableWidget> guarded_widget = widget;

    qDebug() << Q_FUNC_INFO << "Pushing screen";
    int index = m_p_window_stack->addWidget(widget);  // will show the widget
    // The stack takes over ownership.
    // qDebug() << Q_FUNC_INFO << "About to build";
    widget->build();
    // qDebug() << Q_FUNC_INFO << "Build complete, about to show";
    m_p_window_stack->setCurrentIndex(index);
    if (widget->wantsFullscreen()) {
        enterFullscreen();
    }

    // 3. Signals
    connect(widget, &OpenableWidget::enterFullscreen,
            this, &CamcopsApp::enterFullscreen);
    connect(widget, &OpenableWidget::leaveFullscreen,
            this, &CamcopsApp::leaveFullscreen);
    connect(widget, &OpenableWidget::finished,
            this, &CamcopsApp::close);

    m_info_stack.push(OpenableInfo(guarded_widget, task, prev_window_state,
                                   may_alter_task, patient));
    // This stores a QSharedPointer to the task (if supplied), so keeping that
    // keeps the task "alive" whilst its widget is doing things.
    // Similarly with any patient required for patient editing.
}


void CamcopsApp::close()
{
    if (m_info_stack.isEmpty()) {
        uifunc::stopApp("CamcopsApp::close: No more windows; closing");
    }
    OpenableInfo info = m_info_stack.pop();
    // on function exit, will delete the task if it's the last pointer to it
    // (... and similarly any patient)

    QWidget* top = m_p_window_stack->currentWidget();
    qDebug() << Q_FUNC_INFO << "Popping screen";
    m_p_window_stack->removeWidget(top);
    // Ownership is returned to the application, so...
    top->deleteLater();  // later, in case it was this object that called us

    m_p_main_window->setWindowState(info.prev_window_state);

    if (info.may_alter_task) {
#ifdef DEBUG_EMIT
        qDebug() << Q_FUNC_INFO << "Emitting taskAlterationFinished";
#endif

        emit taskAlterationFinished(info.task);

        if (varBool(varconst::OFFER_UPLOAD_AFTER_EDIT) &&
                varBool(varconst::NEEDS_UPLOAD)) {
            QMessageBox msgbox(
                QMessageBox::Question,  // icon
                tr("Upload?"),  // title
                tr("Task finished. Upload data to server now?"),  // text
                QMessageBox::Yes | QMessageBox::No,  // buttons
                m_p_main_window);  // parent
            msgbox.setButtonText(QMessageBox::Yes, tr("Yes, upload"));
            msgbox.setButtonText(QMessageBox::No, tr("No, cancel"));
            int reply = msgbox.exec();
            if (reply == QMessageBox::Yes) {
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


void CamcopsApp::setLockState(LockState lockstate)
{
    bool changed = lockstate != m_lockstate;
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
    QString hashed_password = varString(hashed_password_varname);
    if (hashed_password.isEmpty()) {
        // If there's no password, we just allow the operation.
        return true;
    }
    QString password;
    bool ok = uifunc::getPassword(text, title, password, m_p_main_window);
    if (!ok) {
        return false;
    }
    bool correct = cryptofunc::matchesHash(password, hashed_password);
    if (!correct) {
        uifunc::alert(tr("Wrong password"), title);
    }
    return correct;
}


void CamcopsApp::changeAppPassword()
{
    QString title(tr("Change app password"));
#ifdef SQLCIPHER_ENCRYPTION_ON
    // We also use this password for database encryption, so we need to know
    // it briefly (in plaintext format) to reset the database encryption key.
    QString new_password;
    bool changed = changePassword(varconst::USER_PASSWORD_HASH, title,
                                  nullptr, &new_password);
    if (changed) {
        SlowGuiGuard guard = getSlowGuiGuard(tr("Re-encrypting databases..."));
        qInfo() << "Re-encrypting system database...";
        dbfunc::pragmaRekey(m_sysdb, new_password);
        qInfo() << "Re-encrypting data database...";
        dbfunc::pragmaRekey(m_datadb, new_password);
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
    QString old_password_hash = varString(hashed_password_varname);
    bool old_password_exists = !old_password_hash.isEmpty();
    QString old_password_from_user;
    QString new_password;
    bool ok = uifunc::getOldNewPasswords(text, text, old_password_exists,
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
    DbNestableTransaction trans(m_sysdb);
    resetEncryptionKeyIfRequired();
    QString iv_b64(cryptofunc::generateIVBase64());  // new one each time
    setVar(varconst::OBSCURING_IV, iv_b64);
    SecureQString key_b64(varString(varconst::OBSCURING_KEY));
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
    SecureQString key_b64(varString(varconst::OBSCURING_KEY));
    QString iv_b64(varString(varconst::OBSCURING_IV));
    if (!cryptofunc::isValidAesKey(key_b64)) {
        qWarning() << "Unable to decrypt password; key is bad";
        return "";
    }
    if (!cryptofunc::isValidAesIV(iv_b64)) {
        qWarning() << "Unable to decrypt password; IV is bad";
        return "";
    }
    QString plaintext(cryptofunc::decryptFromBase64(encrypted_b64, key_b64, iv_b64));
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


void CamcopsApp::setNeedsUpload(bool needs_upload)
{
    bool changed = setVar(varconst::NEEDS_UPLOAD, needs_upload);
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


void CamcopsApp::setWhiskerConnected(bool connected)
{
    bool changed = connected != m_whisker_connected;
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


void CamcopsApp::setSelectedPatient(int patient_id)
{
    // We do this by ID so there's no confusion about who owns it; we own
    // our own private copy here.
    bool changed = patient_id != selectedPatientId();
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


void CamcopsApp::reloadPatient(int patient_id)
{
    if (patient_id == dbconst::NONEXISTENT_PK) {
        m_patient.clear();
    } else {
        m_patient.reset(new Patient(*this, m_datadb, patient_id));
    }
}


void CamcopsApp::patientHasBeenEdited(int patient_id)
{
    int current_patient_id = selectedPatientId();
    if (patient_id == current_patient_id) {
        reloadPatient(patient_id);
#ifdef DEBUG_EMIT
        qDebug() << Q_FUNC_INFO << "Emitting selectedPatientDetailsChanged "
                                   "for patient ID" << patient_id;
#endif
        emit selectedPatientDetailsChanged(m_patient.data());
    }
}


const Patient* CamcopsApp::selectedPatient() const
{
    return m_patient.data();
}


int CamcopsApp::selectedPatientId() const
{
    return m_patient ? m_patient->id() : dbconst::NONEXISTENT_PK;
}


PatientPtrList CamcopsApp::getAllPatients(bool sorted)
{
    PatientPtrList patients;
    Patient specimen(*this, m_datadb, dbconst::NONEXISTENT_PK);  // this is why function can't be const
    WhereConditions where;  // but we don't specify any
    SqlArgs sqlargs = specimen.fetchQuerySql(where);
    QSqlQuery query(m_datadb);
    bool success = dbfunc::execQuery(query, sqlargs);
    if (success) {  // success check may be redundant (cf. while clause)
        while (query.next()) {
            PatientPtr p(new Patient(*this, m_datadb, dbconst::NONEXISTENT_PK));
            p->setFromQuery(query, true);
            patients.append(p);
        }
    }
    if (sorted) {
        qSort(patients.begin(), patients.end(), PatientSorter());
    }
    return patients;
}


QString CamcopsApp::idDescription(int which_idnum) const
{
    if (!dbconst::isValidWhichIdnum(which_idnum)) {
        return dbconst::BAD_IDNUM_DESC;
    }
    QString field = dbconst::IDDESC_FIELD_FORMAT.arg(which_idnum);
    QString desc_str = varString(field);
    if (desc_str.isEmpty()) {
        return dbconst::UNKNOWN_IDNUM_DESC.arg(which_idnum);
    }
    return desc_str;
}


QString CamcopsApp::idShortDescription(int which_idnum) const
{
    if (!dbconst::isValidWhichIdnum(which_idnum)) {
        return dbconst::BAD_IDNUM_DESC;
    }
    QString field = dbconst::IDSHORTDESC_FIELD_FORMAT.arg(which_idnum);
    QString desc_str = varString(field);
    if (desc_str.isEmpty()) {
        return dbconst::UNKNOWN_IDNUM_DESC.arg(which_idnum);
    }
    return desc_str;
}


IdPolicy CamcopsApp::uploadPolicy() const
{
    return IdPolicy(varString(varconst::ID_POLICY_UPLOAD));
}


IdPolicy CamcopsApp::finalizePolicy() const
{
    return IdPolicy(varString(varconst::ID_POLICY_FINALIZE));
}


// ============================================================================
// CSS convenience; fonts etc.
// ============================================================================

QString CamcopsApp::getSubstitutedCss(const QString& filename) const
{
    return (
        filefunc::textfileContents(filename)
            .arg(fontSizePt(uiconst::FontSize::Normal))     // %1
            .arg(fontSizePt(uiconst::FontSize::Big))        // %2
            .arg(fontSizePt(uiconst::FontSize::Heading))    // %3
            .arg(fontSizePt(uiconst::FontSize::Title))      // %4
            .arg(fontSizePt(uiconst::FontSize::Menus))      // %5
    );
}


int CamcopsApp::fontSizePt(uiconst::FontSize fontsize,
                           double factor_pct) const
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
// Extra strings (downloaded from server)
// ============================================================================

QString CamcopsApp::xstringDirect(const QString& taskname,
                                  const QString& stringname,
                                  const QString& default_str)
{
    ExtraString extrastring(*this, m_sysdb, taskname, stringname);
    bool found = extrastring.exists();
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
    QPair<QString, QString> key(taskname, stringname);
    if (!m_extrastring_cache.contains(key)) {
        m_extrastring_cache[key] = xstringDirect(taskname, stringname,
                                                 default_str);
    }
    return m_extrastring_cache[key];
}


bool CamcopsApp::hasExtraStrings(const QString& taskname)
{
    ExtraString extrastring_specimen(*this, m_sysdb);
    return extrastring_specimen.anyExist(taskname);
}


void CamcopsApp::clearExtraStringCache()
{
    m_extrastring_cache.clear();
}


void CamcopsApp::deleteAllExtraStrings()
{
    ExtraString extrastring_specimen(*this, m_sysdb);
    extrastring_specimen.deleteAllExtraStrings();
    clearExtraStringCache();
}


void CamcopsApp::setAllExtraStrings(const RecordList& recordlist)
{
    DbTransaction trans(m_sysdb);
    deleteAllExtraStrings();
    for (auto record : recordlist) {
        if (!record.contains(ExtraString::EXTRASTRINGS_TASK_FIELD) ||
                !record.contains(ExtraString::EXTRASTRINGS_NAME_FIELD) ||
                !record.contains(ExtraString::EXTRASTRINGS_VALUE_FIELD)) {
            qWarning() << Q_FUNC_INFO << "Failing: recordlist has bad format";
            trans.fail();
            return;
        }
        QString task = record[ExtraString::EXTRASTRINGS_TASK_FIELD].toString();
        QString name = record[ExtraString::EXTRASTRINGS_NAME_FIELD].toString();
        QString value = record[ExtraString::EXTRASTRINGS_VALUE_FIELD].toString();
        if (task.isEmpty() || name.isEmpty()) {
            qWarning() << Q_FUNC_INFO
                       << "Failing: extra string has blank task or name";
            trans.fail();
            return;
        }
        ExtraString es(*this, m_sysdb, task, name, value);
        es.save();
    }
}


QString CamcopsApp::appstring(const QString& stringname,
                              const QString& default_str)
{
    return xstring(APPSTRING_TASKNAME, stringname, default_str);
}

// ============================================================================
// Stored variables: generic
// ============================================================================

void CamcopsApp::createVar(const QString &name, QVariant::Type type,
                                 const QVariant &default_value)
{
    if (name.isEmpty()) {
        uifunc::stopApp("Empty name to createVar");
    }
    if (m_storedvars.contains(name)) {  // Already exists
        return;
    }
    m_storedvars[name] = StoredVarPtr(
        new StoredVar(*this, m_sysdb, name, type, default_value));
}


bool CamcopsApp::setVar(const QString& name, const QVariant& value,
                        bool save_to_db)
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


FieldRefPtr CamcopsApp::storedVarFieldRef(const QString& name, bool mandatory,
                                          bool cached)
{
    return FieldRefPtr(new FieldRef(this, name, mandatory, cached));
}


void CamcopsApp::clearCachedVars()
{
    m_cachedvars.clear();
}


void CamcopsApp::saveCachedVars()
{
    DbNestableTransaction trans(m_sysdb);
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
    bool changed = value != m_cachedvars[name];
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
    QMessageBox msgbox(QMessageBox::Question,  // icon
                       tr("View terms and conditions of use"),  // title
                       textconst::TERMS_CONDITIONS,  // text
                       QMessageBox::Yes | QMessageBox::No,  // buttons
                       m_p_main_window);  // parent
    msgbox.setButtonText(QMessageBox::Yes,
                         tr("I AGREE to these terms and conditions"));
    msgbox.setButtonText(QMessageBox::No,
                         tr("I DO NOT AGREE to these terms and conditions"));
    // It's hard work to remove the Close button from the dialog, but that is
    // interpreted as rejection, so that's OK.
    // - http://www.qtcentre.org/threads/41269-disable-close-button-in-QMessageBox

    int reply = msgbox.exec();
    if (reply == QMessageBox::Yes) {
        // Agreed terms
        setVar(varconst::AGREED_TERMS_AT, QDateTime::currentDateTime());
    } else {
        // Refused terms
        uifunc::stopApp(tr("OK. Goodbye."), tr("You refused the conditions."));
    }
}


// ============================================================================
// SQL dumping
// ============================================================================

void CamcopsApp::dumpDataDatabase(QTextStream& os)
{
    dumpsql::dumpDatabase(os, m_datadb);
}


void CamcopsApp::dumpSystemDatabase(QTextStream& os)
{
    dumpsql::dumpDatabase(os, m_sysdb);
}


// ============================================================================
// Uploading
// ============================================================================

void CamcopsApp::upload()
{
    QMessageBox::StandardButtons buttons = (QMessageBox::Yes |
                                            QMessageBox::No |
                                            QMessageBox::Ok |
                                            QMessageBox::Cancel);
    QString text =
            "Copy data to server, or move it to server?\n"
            "\n"
            "COPY: copies unfinished patients, moves finished patients.\n"
            "MOVE: moves all patients and their data.\n"
            "MOVE, KEEPING PATIENTS: moves all task data, keeps only basic "
            "patient details for unfinished patients.\n"
            "\n"
            "Please MOVE whenever possible; this reduces the amount of "
            "patient-identifiable information stored on this device.";
    QMessageBox msgbox(QMessageBox::Question,  // icon
                       tr("Upload to server"),  // title
                       text,  // text
                       buttons,  // buttons
                       m_p_main_window);  // parent
    msgbox.setButtonText(QMessageBox::Yes, tr("Copy"));
    msgbox.setButtonText(QMessageBox::No, tr("Move, keeping patients"));
    msgbox.setButtonText(QMessageBox::Ok, tr("Move"));
    msgbox.setButtonText(QMessageBox::Cancel, tr("Cancel"));
    int reply = msgbox.exec();
    NetworkManager::UploadMethod method;
    switch (reply) {
    case QMessageBox::Yes:  // copy
        method = NetworkManager::UploadMethod::Copy;
        break;
    case QMessageBox::No:  // move, keeping patients
        method = NetworkManager::UploadMethod::MoveKeepingPatients;
        break;
    case QMessageBox::Ok:  // move
        method = NetworkManager::UploadMethod::Move;
        break;
    case QMessageBox::Cancel:  // cancel
    default:
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
