/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
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
#include <QLibraryInfo>
#include <QMainWindow>
#include <QMetaType>
#include <QNetworkReply>
#include <QProcessEnvironment>
#include <QPushButton>
#include <QScreen>
#include <QSqlDatabase>
#include <QSqlDriverCreator>
#include <QStackedWidget>
#include <QStandardPaths>
#include <QTextStream>
#include <QTranslator>
#include <QUrl>
#include <QUuid>

#include "common/appstrings.h"
#include "common/dbconst.h"  // for NONEXISTENT_PK
#include "common/languages.h"
#include "common/platform.h"
#include "common/preprocessor_aid.h"  // IWYU pragma: keep
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
#include "diagnosis/icd10.h"
#include "diagnosis/icd9cm.h"
#include "dialogs/modedialog.h"
#include "dialogs/patientregistrationdialog.h"
#include "dialogs/scrollmessagebox.h"
#include "dialogs/useragentdialog.h"
// #include "layouts/layouts.h"
#include "lib/convert.h"
#include "lib/customtypes.h"
#include "lib/datetime.h"
#include "lib/filefunc.h"
#include "lib/slowguiguard.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "menu/mainmenu.h"
#include "menu/singleusermenu.h"
#include "qobjects/slownonguifunctioncaller.h"
#include "qobjects/urlhandler.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "tasklib/inittasks.h"
#include "tasklib/taskschedule.h"
#include "tasklib/taskscheduleitem.h"
#include "version/camcopsversion.h"
#include "whisker/whiskertypes.h"

#ifdef DEBUG_ALL_APPLICATION_EVENTS
    #include "qobjects/debugeventwatcher.h"
#endif

#ifdef USE_SQLCIPHER
    #include "db/sqlcipherdriver.h"
#endif

const QString APPSTRING_TASKNAME("camcops");
// ... task name used for generic but downloaded tablet strings
const QString APP_NAME("camcops");
// ... e.g. subdirectory of ~/.local/share; DO NOT ALTER
const QString APP_PRETTY_NAME("CamCOPS");
// ... main window title and suffix on dialog window titles
const QString CONNECTION_DATA("data");
const QString CONNECTION_SYS("sys");
const int DEFAULT_SERVER_PORT = 443;  // HTTPS
const QString ENVVAR_DB_DIR("CAMCOPS_DATABASE_DIRECTORY");
const int UPLOAD_INTERVAL_SECONDS = 10 * 60;  // 10 minutes

CamcopsApp::CamcopsApp(int& argc, char* argv[]) :
    QApplication(argc, argv),
    m_p_task_factory(nullptr),
    m_lockstate(LockState::Locked),
    // ... default unless we get in via encryption password
    m_p_main_window(nullptr),
    m_p_window_stack(nullptr),
    m_p_hidden_stack(nullptr),
    m_maximized_before_fullscreen(true),
    // ... true because openMainWindow() goes maximized
    m_patient(nullptr),
    m_storedvars_available(false),
    m_netmgr(nullptr),
    m_qt_logical_dpi(uiconst::DEFAULT_DPI),
    m_qt_physical_dpi(uiconst::DEFAULT_DPI),
    m_network_gui_guard(nullptr)
{
    setLanguage(QLocale::system().name());  // try languages::DANISH
    setApplicationName(APP_NAME);
    setApplicationDisplayName(APP_PRETTY_NAME);
    setApplicationVersion(camcopsversion::CAMCOPS_CLIENT_VERSION.toString());
#ifdef DEBUG_ALL_APPLICATION_EVENTS
    new DebugEventWatcher(this, DebugEventWatcher::All);
#endif

    m_last_automatic_upload_time = QDateTime();  // initially invalid
}

CamcopsApp::~CamcopsApp()
{
    // https://doc.qt.io/qt-6.5/objecttrees.html
    // Only delete things that haven't been assigned a parent
    delete m_network_gui_guard;
    delete m_p_main_window;
}

// ============================================================================
// Operating mode
// ============================================================================

bool CamcopsApp::isSingleUserMode() const
{
    return getMode() == varconst::MODE_SINGLE_USER;
}

bool CamcopsApp::isClinicianMode() const
{
    return getMode() == varconst::MODE_CLINICIAN;
}

int CamcopsApp::getMode() const
{
    return varInt(varconst::MODE);
}

void CamcopsApp::setMode(const int mode)
{
    const int old_mode = getMode();
    const bool mode_changed = mode != old_mode;
    const bool single_user_mode = mode == varconst::MODE_SINGLE_USER;

    // Things we might do even if the new mode is the same as the old mode
    // (e.g. at startup):
    if (single_user_mode) {
        disableNetworkLogging();
        setVar(varconst::OFFER_UPLOAD_AFTER_EDIT, true);
    } else {
        enableNetworkLogging();
    }

    // Things we only do if the mode has actually changed:
    if (mode_changed) {
        setVar(varconst::MODE, mode);

        if (single_user_mode) {
            setDefaultPatient();
        }

        if (m_p_main_window) {
            // If the mode has been set on startup, we won't have a main window
            // yet to attach the menu to, so we create it later.
            recreateMainMenu();
        }

        emit modeChanged(mode);
    }
}

void CamcopsApp::setModeFromUser()
{
    if (modeChangeForbidden()) {  // alerts the user as to why, if not allowed
        return;
    }

    const int old_mode = getMode();
    int new_mode;

    // Single user mode specified on the command line or if the app was
    // launched via a deep link on Android (starting
    // https://ucam-department-of-psychiatry.github.io/camcops/register/)
    if (old_mode == varconst::MODE_NOT_SET && m_default_single_user_mode) {
        new_mode = varconst::MODE_SINGLE_USER;
    } else {
        new_mode = getModeFromUser();
        if (new_mode == old_mode) {
            // No change, nothing to do
            return;
        }
    }

    if (!agreeTerms(new_mode)) {
        // User changed mode but didn't agree to terms. Will exit the app if
        // called on startup, otherwise stick with the old mode

        if (!hasAgreedTerms()) {
            uifunc::stopApp(
                tr("OK. Goodbye."), tr("You refused the conditions.")
            );
        }

        // had agreed to terms for the old mode, so don't change

        return;
    }

    wipeDataForModeChange();
    setMode(new_mode);
    if (new_mode == varconst::MODE_SINGLE_USER) {
        registerPatientWithServer();
    }
}

int CamcopsApp::getModeFromUser()
{
    const int old_mode = getMode();
    ModeDialog dialog(old_mode);
    const int reply = dialog.exec();
    if (reply != QDialog::Accepted) {
        // Dialog cancelled
        if (old_mode == varconst::MODE_NOT_SET) {
            // Exit the app if called on startup
            uifunc::stopApp(
                tr("You did not select how you would like to use CamCOPS")
            );
        }
    }

    return dialog.mode();
}

bool CamcopsApp::modeChangeForbidden() const
{
    if (isClinicianMode()) {
        // Switch from clinician mode to single-user mode
        if (patientRecordsPresent()) {
            uifunc::alert(tr(
                "You cannot change mode when there are patient records present"
            ));
            return true;
        }
    }
    if (taskRecordsPresent()) {
        // Switch in either direction
        uifunc::alert(tr(
            "You cannot change mode when there are tasks still to be uploaded"
        ));
        return true;
    }

    return false;
}

bool CamcopsApp::taskRecordsPresent() const
{
    return m_p_task_factory->anyTasksPresent();
}

void CamcopsApp::wipeDataForModeChange()
{
    // When we switch from clinician mode to single-user mode:
    // - We should have no patients (*).
    // - We should have no tasks (*).
    // - We must wipe network security details.
    // - [We will also want the user to register using the single-user-mode
    //   registration interface.]
    // - We should wipe task schedules.
    //
    // When we switch from single-user mode to clinician mode:
    // - There will be one patient, but that's OK. We will delete the record.
    // - We should have no tasks (*).
    // - We must wipe network security details -- the "single-user" accounts
    //   are not necessarily trusted to create data for new patients.
    //   (Otherwise the theoretical vulnerability is that a registered user
    //   obtains their username, cracks their obscured password, and enters
    //   them into the clinician mode, allowing upload of data for arbitrary
    //   patients.)
    //
    //  At present the client verifies this, but ideally we should verify that
    //  server-side, too; see todo.rst.
    //
    // - We can wipe task schedules.
    //
    // (*) Pre-checked by modeChangeForbidden().

    // Deselect any selected patient
    deselectPatient();

    // Server security details
    setVar(varconst::SERVER_USERNAME, "");
    setVar(varconst::SERVER_USERPASSWORD_OBSCURED, "");
    setVar(varconst::SINGLE_PATIENT_PROQUINT, "");
    setVar(varconst::SINGLE_PATIENT_ID, dbconst::NONEXISTENT_PK);

    // Task schedules
    m_sysdb->deleteFrom(TaskScheduleItem::TABLENAME);
    m_sysdb->deleteFrom(TaskSchedule::TABLENAME);

    // Delete patient records (given the pre-checks, as above, this will only
    // delete a single-user-mode patient record with no associated tasks).
    m_datadb->deleteFrom(PatientIdNum::PATIENT_IDNUM_TABLENAME);
    m_datadb->deleteFrom(Patient::TABLENAME);
}

bool CamcopsApp::patientRecordsPresent() const
{
    return nPatients() > 0;
}

int CamcopsApp::getSinglePatientId() const
{
    return var(varconst::SINGLE_PATIENT_ID).toInt();
}

void CamcopsApp::setSinglePatientId(const int id)
{
    setVar(varconst::SINGLE_PATIENT_ID, id);
}

bool CamcopsApp::registerPatientWithServer()
{
    if (isPatientSelected()) {
        if (!confirmDeletePatient()) {
            return false;
        }

        deleteSelectedPatient();
        deleteTaskSchedules();
        recreateMainMenu();
    }

    // The values we will attempt to register with:
    QUrl new_server_url;
    QString new_patient_proquint;

    if (!m_default_server_url.isEmpty()
        && !m_default_patient_proquint.isEmpty()) {
        // These defaults may have been passed in as command-line options;
        // see processCommandLineArguments().
        new_server_url = m_default_server_url;
        new_patient_proquint = m_default_patient_proquint;
    } else {
        // Start with a blank URL, or a URL from a previous failed attempt, to
        // assist in reducing data entry following network/registration
        // failure.
        QUrl old_server_url = QUrl();
        const QString old_patient_proquint
            = varString(varconst::SINGLE_PATIENT_PROQUINT);
        if (!old_patient_proquint.isEmpty()) {
            old_server_url.setScheme("https");
            old_server_url.setHost(varString(varconst::SERVER_ADDRESS));
            old_server_url.setPort(varInt(varconst::SERVER_PORT));
            old_server_url.setPath(varString(varconst::SERVER_PATH));
        }

        PatientRegistrationDialog dialog(
            nullptr, old_server_url, old_patient_proquint
        );
        // Work around https://bugreports.qt.io/browse/QTBUG-125337
        dialog.setFocus();

        const int reply = dialog.exec();
        if (reply != QDialog::Accepted) {
            return false;
        }

        new_server_url = dialog.serverUrl();
        new_patient_proquint = dialog.patientProquint();
    }

    setVar(varconst::SERVER_ADDRESS, new_server_url.host());

    const int default_port = DEFAULT_SERVER_PORT;
    setVar(varconst::SERVER_PORT, new_server_url.port(default_port));
    setVar(varconst::SERVER_PATH, new_server_url.path());
    setVar(varconst::SINGLE_PATIENT_PROQUINT, new_patient_proquint);
    setVar(
        varconst::DEVICE_FRIENDLY_NAME,
        QString("Single user device %1").arg(deviceId())
    );
    // Currently defaults to no validation, though the user can enable through
    // the advanced settings if they so wish.
    setVar(
        varconst::VALIDATE_SSL_CERTIFICATES,
        varconst::VALIDATE_SSL_CERTIFICATES_IN_SINGLE_USER_MODE
    );

    reconnectNetManager(
        &CamcopsApp::patientRegistrationFailed,
        &CamcopsApp::patientRegistrationFinished
    );

    showNetworkGuiGuard(tr("Registering patient..."));
    networkManager()->registerPatient();

    return true;
}

bool CamcopsApp::confirmDeletePatient() const
{
    ScrollMessageBox msgbox(
        QMessageBox::Warning,
        tr("Delete patient"),
        tr("Registering a new patient will delete the current patient and "
           "any associated data. Are you sure you want to do this?"
        ) + "\n\n",
        m_p_main_window
    );
    QAbstractButton* delete_button
        = msgbox.addButton(tr("Yes, delete"), QMessageBox::YesRole);
    msgbox.addButton(tr("No, cancel"), QMessageBox::NoRole);
    msgbox.exec();
    if (msgbox.clickedButton() != delete_button) {
        return false;
    }

    return true;
}

void CamcopsApp::deleteSelectedPatient()
{
    m_patient->deleteFromDatabase();

    setSinglePatientId(dbconst::NONEXISTENT_PK);
    setDefaultPatient();
}

void CamcopsApp::deleteTaskSchedules()
{
    TaskSchedulePtrList schedules = getTaskSchedules();

    for (const TaskSchedulePtr& schedule : schedules) {
        schedule->deleteFromDatabase();
    }
}

void CamcopsApp::updateTaskSchedules(const bool alert_unfinished_tasks)
{
    if (tasksInProgress()) {
        if (alert_unfinished_tasks) {
            uifunc::alert(
                tr("You cannot update your task schedules when there are "
                   "unfinished tasks")
            );
        }

        return;
    }

    showNetworkGuiGuard(tr("Updating task schedules..."));

    reconnectNetManager(
        &CamcopsApp::updateTaskSchedulesFailed,
        &CamcopsApp::updateTaskSchedulesFinished
    );
    networkManager()->updateTaskSchedulesAndPatientDetails();
}

void CamcopsApp::patientRegistrationFailed(
    const NetworkManager::ErrorCode error_code, const QString& error_string
)
{
    deleteNetworkGuiGuard();

    const QString base_message
        = tr("There was a problem with your registration.");

    QString additional_message = "";

    switch (error_code) {

        case NetworkManager::ServerError:
        case NetworkManager::JsonParseError:
            additional_message = error_string;
            break;

        case NetworkManager::IncorrectReplyFormat:
            additional_message
                = tr("Did you enter the correct CamCOPS server location?");
            break;

        case NetworkManager::GenericNetworkError:
            additional_message
                = tr("%1\n\n"
                     "Are you connected to the internet?\n\n"
                     "Did you enter the correct CamCOPS server location?")
                      .arg(error_string);
            break;

        default:
            // Shouldn't get here
            break;
    }

    maybeRetryNetworkOperation(
        base_message, additional_message, NetworkOperation::RegisterPatient
    );
}

void CamcopsApp::patientRegistrationFinished()
{
    // Clear these after initial registration
    m_default_server_url = QString();
    m_default_patient_proquint = QString();

    deleteNetworkGuiGuard();

    // Creating the single patient from the server details will trigger
    // "needs upload" and the upload icon will be displayed. We don't want
    // to see the icon because we will wait until there are tasks to upload
    // before uploading the patient
    setNeedsUpload(false);

    recreateMainMenu();
}

void CamcopsApp::updateTaskSchedulesFailed(
    const NetworkManager::ErrorCode error_code, const QString& error_string
)
{
    deleteNetworkGuiGuard();
    handleNetworkFailure(
        error_code,
        error_string,
        tr("There was a problem updating your task schedules."),
        NetworkOperation::UpdateTaskSchedules
    );
}

void CamcopsApp::updateTaskSchedulesFinished()
{
    deleteNetworkGuiGuard();

    // Updating the single patient from the server details will trigger
    // "needs upload" and the upload icon will be displayed. We don't want
    // to see the icon because we will wait until there are tasks to upload
    // before uploading the patient
    setNeedsUpload(false);

    recreateMainMenu();
}

void CamcopsApp::uploadFailed(
    const NetworkManager::ErrorCode error_code, const QString& error_string
)
{
    deleteNetworkGuiGuard();
    handleNetworkFailure(
        error_code,
        error_string,
        tr("There was a problem sending your completed tasks to the server."),
        NetworkOperation::Upload
    );
}

void CamcopsApp::uploadFinished()
{
    deleteNetworkGuiGuard();
    const bool alert_unfinished_tasks = false;
    updateTaskSchedules(alert_unfinished_tasks);

    recreateMainMenu();
}

void CamcopsApp::showNetworkGuiGuard(const QString& text)
{
    if (!isLoggingNetwork()) {
        m_network_gui_guard = new SlowGuiGuard(*this, m_p_main_window, text);
    }
}

void CamcopsApp::deleteNetworkGuiGuard()
{
    if (m_network_gui_guard) {
        delete m_network_gui_guard;
        m_network_gui_guard = nullptr;
    }
}

void CamcopsApp::retryUpload()
{
    const bool needs_upload = needsUpload();

    qDebug() << Q_FUNC_INFO << "Last automatic upload time"
             << m_last_automatic_upload_time << "needsUpload()"
             << needs_upload;

    if (needs_upload) {
        const auto now = QDateTime::currentDateTimeUtc();

        if (!m_last_automatic_upload_time.isValid()
            || m_last_automatic_upload_time.secsTo(now)
                > UPLOAD_INTERVAL_SECONDS) {
            upload();
            m_last_automatic_upload_time = now;
        }
    }
}

void CamcopsApp::handleNetworkFailure(
    const NetworkManager::ErrorCode error_code,
    const QString& error_string,
    const QString& base_message,
    CamcopsApp::NetworkOperation operation
)
{
    QString additional_message = "";

    switch (error_code) {

        case NetworkManager::IncorrectReplyFormat:
            // If we've managed to register our patient and the server is
            // replying but in the wrong way then something bad has happened.
            additional_message
                = tr("Unexpectedly, your server settings have changed.");
            break;

        case NetworkManager::ServerError:
            additional_message = error_string;
            break;

        case NetworkManager::GenericNetworkError:
            additional_message = tr("%1\n\nAre you connected to the internet?")
                                     .arg(error_string);
            break;

        default:
            break;
    }

    maybeRetryNetworkOperation(base_message, additional_message, operation);
}

void CamcopsApp::maybeRetryNetworkOperation(
    const QString base_message,
    const QString additional_message,
    CamcopsApp::NetworkOperation operation
)
{
    const bool try_again_with_log = uifunc::confirm(
        QString("%1\n\n%2").arg(base_message, additional_message),
        tr("Error"),
        tr("Try again with error log"),
        TextConst::cancel()
    );

    if (!try_again_with_log) {
        recreateMainMenu();

        return;
    }

    enableNetworkLogging();

    switch (operation) {
        case NetworkOperation::RegisterPatient:
            registerPatientWithServer();
            break;

        case NetworkOperation::UpdateTaskSchedules:
            // it doesn't matter if we pass alert_unfinished_tasks as True or
            // False here. We wouldn't be here if there were unfinished tasks.
            updateTaskSchedules();
            break;

        case NetworkOperation::Upload:
            upload();
            break;

        default:
            // Shouldn't get here
            break;
    }
}

TaskSchedulePtrList CamcopsApp::getTaskSchedules()
{
    TaskSchedulePtrList task_schedules;
    TaskSchedule specimen(*this, *m_sysdb, dbconst::NONEXISTENT_PK);
    // ... this is why function can't be const
    const WhereConditions where;  // but we don't specify any
    const SqlArgs sqlargs = specimen.fetchQuerySql(where);
    const QueryResult result = m_sysdb->query(sqlargs);
    const int nrows = result.nRows();
    for (int row = 0; row < nrows; ++row) {
        TaskSchedulePtr t(
            new TaskSchedule(*this, *m_sysdb, dbconst::NONEXISTENT_PK)
        );
        t->setFromQuery(result, row, true);
        task_schedules.append(t);
    }

    return task_schedules;
}

void CamcopsApp::setLanguage(
    const QString& language_code, const bool store_to_database
)
{
    qInfo() << "Setting language to:" << language_code;

    // 1. Store the new code
    m_current_language = language_code;
    if (store_to_database && m_storedvars_available) {
        setVar(varconst::LANGUAGE, language_code);
    }

    // 2. Clear the string cache
    clearExtraStringCache();

    // There are polymorphic versions of QTranslator::load(). See
    // https://doc.qt.io/qt-6.5/qtranslator.html#load

    // 3. Qt translator
    if (m_qt_translator) {
        removeTranslator(m_qt_translator.data());
        m_qt_translator = nullptr;
    }
    const QString qt_filename = QString("qt_%1.qm").arg(language_code);
    const QString qt_directory
        = QLibraryInfo::path(QLibraryInfo::TranslationsPath);
    m_qt_translator = QSharedPointer<QTranslator>(new QTranslator());
    bool loaded = m_qt_translator->load(qt_filename, qt_directory);
    if (loaded) {
        installTranslator(m_qt_translator.data());
        qInfo() << "Loaded Qt translator" << qt_filename << "from"
                << qt_directory;
    } else {
        qWarning() << "Failed to load Qt translator" << qt_filename << "from"
                   << qt_directory;
    }

    // 4. App translator
    if (m_app_translator) {
        removeTranslator(m_app_translator.data());
        m_app_translator = nullptr;
    }
    if (language_code != languages::DEFAULT_LANGUAGE) {
        const QString cc_filename
            = QString("camcops_%1.qm").arg(language_code);
        const QString cc_directory(":/translations");
        m_app_translator = QSharedPointer<QTranslator>(new QTranslator());
        loaded = m_app_translator->load(cc_filename, cc_directory);
        if (loaded) {
            installTranslator(m_app_translator.data());
            qInfo() << "Loaded CamCOPS translator" << cc_filename << "from"
                    << cc_directory;
        } else {
            qWarning() << "Failed to load CamCOPS translator" << cc_filename
                       << "from" << cc_directory;
        }
    }

    // 5. Set the locale (so that e.g. calendar widgets use the right
    // language).
    QLocale::setDefault(QLocale(language_code));
}

QString CamcopsApp::getLanguage() const
{
    return m_current_language;
}

int CamcopsApp::run()
{
    // We do the minimum possible; then we fire up the GUI; then we run
    // everything that we can in a different thread through backgroundStartup.
    // This makes the GUI startup more responsive.

    // Baseline C++ things
    customtypes::registerTypesForQVariant();
    whiskertypes::registerTypesForQVariant();

    // Listen for application launch from URL
    auto url_handler = UrlHandler::getInstance();
    connect(
        url_handler,
        &UrlHandler::defaultSingleUserModeSet,
        this,
        &CamcopsApp::setDefaultSingleUserMode
    );
    connect(
        url_handler,
        &UrlHandler::defaultServerLocationSet,
        this,
        &CamcopsApp::setDefaultServerLocation
    );
    connect(
        url_handler,
        &UrlHandler::defaultAccessKeySet,
        this,
        &CamcopsApp::setDefaultAccessKey
    );

    // Command-line arguments
    int retcode = 0;
    if (!processCommandLineArguments(retcode)) {
        // processCommandLineArguments() may exit directly if there's a syntax
        // error, in which case we won't even get here
        return retcode;  // exit with failure/success
    }

    // Say hello to the console
    announceStartup();

    // Set window icon
    initGuiOne();

    // Connect to our database
    registerDatabaseDrivers();
    openOrCreateDatabases();
    QString new_user_password;
    bool user_cancelled_please_quit = false;
    const bool changed_user_password = connectDatabaseEncryption(
        new_user_password, user_cancelled_please_quit
    );
    if (user_cancelled_please_quit) {
        qCritical() << "User cancelled attempt";
        return 0;  // will quit
    }

    // Make storedvar table (used by menus for font size etc.)
    makeStoredVarTable();
    createStoredVars();

    // Since that might have changed our language, reset it.
    setLanguage(varString(varconst::LANGUAGE));

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
    Q_UNUSED(changed_user_password)
#endif

    // Set the stylesheet.
    initGuiTwoStylesheet();  // AFTER storedvar creation

    // Do the rest of the database configuration, task registration, etc.,
    // with a "please wait" dialog.
    {
        SlowNonGuiFunctionCaller slow_caller(
            std::bind(&CamcopsApp::backgroundStartup, this),
            nullptr,  // no m_p_main_window yet
            tr("Configuring internal database"),
            TextConst::pleaseWait()
        );
    }

    openMainWindow();
    // ... uses HelpMenu etc. and so must be AFTER TASK REGISTRATION
    makeNetManager();
    // ... needs to be after main window created, and on GUI thread

    if (varInt(varconst::MODE) == varconst::MODE_NOT_SET) {
        // e.g. fresh database; which mode to use?
        setModeFromUser();
    } else {
        // We know our mode from last time.
        // Ensure all mode-specific things are set:
        setModeFromSavedState();
    }

    return exec();  // Main Qt event loop
}

void CamcopsApp::setDefaultSingleUserMode(const QString& value)
{
    // Set from URL or command line so string not boolean
    m_default_single_user_mode = (value.toLower() == "true");
}

void CamcopsApp::setDefaultServerLocation(const QString& url)
{
    m_default_server_url = QUrl(url);
}

void CamcopsApp::setDefaultAccessKey(const QString& key)
{
    m_default_patient_proquint = key;
}

void CamcopsApp::setModeFromSavedState()
{
    setMode(varInt(varconst::MODE));
    maybeRegisterPatient();
}

void CamcopsApp::maybeRegisterPatient()
{
    if (needToRegisterSinglePatient()) {
        if (!registerPatientWithServer()) {
            // User cancelled patient registration dialog
            // They can try again with the "Register me" button
            // or switch to clinician mode ("More options")
            recreateMainMenu();
        }
    } else {
        if (isSingleUserMode()) {
            setDefaultPatient();
        }
    }
}

void CamcopsApp::backgroundStartup()
{
    // WORKER THREAD. BEWARE.
    const Version old_version = upgradeDatabaseBeforeTablesMade();
    makeOtherTables();
    registerTasks();  // AFTER storedvar creation, so tasks can read them
    upgradeDatabaseAfterTasksRegistered(old_version);
    // ... AFTER tasks registered
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
    return QStandardPaths::standardLocations(QStandardPaths::AppDataLocation)
        .first();
    // Under Linux: ~/.local/share/camcops/; the last part of this path is
    // determined by the call to QCoreApplication::setApplicationName(), or if
    // that hasn't been set, the executable name.
}

bool CamcopsApp::processCommandLineArguments(int& retcode)
{
    const QProcessEnvironment env = QProcessEnvironment::systemEnvironment();

    // https://stackoverflow.com/questions/3886105/how-to-print-to-console-when-using-qt
    QTextStream out(stdout);
    // QTextStream err(stderr);

    // const int retcode_fail = 1;
    const int retcode_success = 0;

    retcode = retcode_success;  // default failure code

    // ------------------------------------------------------------------------
    // Build parser
    // ------------------------------------------------------------------------
    QCommandLineParser parser;

    // -h, --help
    parser.addHelpOption();

    // -v, --version
    parser.addVersionOption();

    // --dbdir <DBDIR>
    QString default_database_dir = defaultDatabaseDir();

    if (env.contains("GENERATING_CAMCOPS_DOCS")) {
        default_database_dir = "/path/to/client/database/dir";
    }

    QCommandLineOption dbDirOption(
        "dbdir",  // makes "--dbdir" option
        QString(
            "Specify the database directory, in which the databases %1 and %2 "
            "are used or created. Order of precedence (highest to lowest) "
            "is (1) this argument, (2) the %3 environment variable, and (3) "
            "the default, on this particular system, of %4."
        )
            .arg(
                convert::stringToCppLiteral(dbfunc::DATA_DATABASE_FILENAME),
                convert::stringToCppLiteral(dbfunc::SYSTEM_DATABASE_FILENAME),
                ENVVAR_DB_DIR,
                convert::stringToCppLiteral(default_database_dir)
            )
    );
    dbDirOption.setValueName("DBDIR");  // makes it take a parameter
    parser.addOption(dbDirOption);

    // --default_single_user_mode
    QCommandLineOption defaultSingleUserModeOption(
        "default_single_user_mode",
        QString(
            "If no mode has previously been selected, do not display the mode "
            "selection dialog and default to single user mode."
        ),
        "DEFAULT_SINGLE_USER_MODE",
        "false"
    );
    defaultSingleUserModeOption.setValueName("MODE");  // shorter text
    parser.addOption(defaultSingleUserModeOption);

    // --default_server_location
    QCommandLineOption defaultServerLocationOption(
        "default_server_location",
        QString("If no server has been registered, default to this URL "
                "e.g. https://server.example.com/camcops/api"),
        "DEFAULT_SERVER_LOCATION"
    );
    defaultServerLocationOption.setValueName("URL");
    parser.addOption(defaultServerLocationOption);

    // --default_access_key
    QCommandLineOption defaultAccessKeyOption(
        "default_access_key",
        QString(
            "If no patient has been registered, default to this access key "
            "e.g. abcde-fghij-klmno-pqrst-uvwxy-zabcd-efghi-jklmn-o"
        ),
        "DEFAULT_ACCESS_KEY"
    );
    defaultAccessKeyOption.setValueName("KEY");
    parser.addOption(defaultAccessKeyOption);

    // --print_icd9_codes
    QCommandLineOption printIcd9Option(
        "print_icd9_codes",
        "Print ICD-9-CM (DSM-IV) codes used by CamCOPS, and quit."
    );
    // We don't use setValueName(), so it behaves like a flag.
    parser.addOption(printIcd9Option);

    // --print_icd10_codes
    const QCommandLineOption printIcd10Option(
        "print_icd10_codes", "Print ICD-10 codes used by CamCOPS, and quit."
    );
    // We don't use setValueName(), so it behaves like a flag.
    parser.addOption(printIcd10Option);

    // --print_tasks
    const QCommandLineOption printTasks(
        "print_tasks",
        "Print tasks supported in this version of CamCOPS, and quit."
    );
    // We don't use setValueName(), so it behaves like a flag.
    parser.addOption(printTasks);

    // --print_terms_conditions
    const QCommandLineOption printTermsConditions(
        "print_terms_conditions",
        "Print terms and conditions applicable to CamCOPS, and quit."
    );
    // We don't use setValueName(), so it behaves like a flag.
    parser.addOption(printTermsConditions);

    // ------------------------------------------------------------------------
    // Process the arguments
    // ------------------------------------------------------------------------
    parser.process(*this);  // will exit directly upon failure
    // ... could also use parser.process(arguments()), or parser.parse(...)

    // ------------------------------------------------------------------------
    // Defaults from the environment
    // ------------------------------------------------------------------------
    m_database_path = env.value(ENVVAR_DB_DIR, defaultDatabaseDir());

    // ------------------------------------------------------------------------
    // Apply parsed arguments (may override environment variable)
    // ------------------------------------------------------------------------
    const QString db_dir = parser.value(dbDirOption);
    if (!db_dir.isEmpty()) {
        m_database_path = db_dir;
    }

    setDefaultSingleUserMode(parser.value(defaultSingleUserModeOption));
    setDefaultServerLocation(parser.value(defaultServerLocationOption));
    setDefaultAccessKey(parser.value(defaultAccessKeyOption));

    // ------------------------------------------------------------------------
    // Actions that make us do something and quit
    // ------------------------------------------------------------------------
    // We need to be sure the diagnostic code sets do not use xstring() and
    // touch the database; hence the "dummy_creation_no_xstrings" parameter.
    const bool print_icd9 = parser.isSet(printIcd9Option);
    if (print_icd9) {
        const Icd9cm icd9(*this, nullptr, true);
        // qDebug() << icd9;
        out << icd9;
        return false;
    }

    const bool print_icd10 = parser.isSet(printIcd10Option);
    if (print_icd10) {
        const Icd10 icd10(*this, nullptr, true);
        // qDebug() << icd10;
        out << icd10;
        return false;
    }

    const bool print_tasks = parser.isSet(printTasks);
    if (print_tasks) {
        printTasksWithoutDatabase(out);
        return false;
    }

    const bool print_terms = parser.isSet(printTermsConditions);
    if (print_terms) {
        out << textconst.clinicianTermsConditions();
        out << textconst.singleUserTermsConditions();
        return false;
    }

    // ------------------------------------------------------------------------
    // Done; proceed to launch CamCOPS
    // ------------------------------------------------------------------------
    return true;  // happy
}

void CamcopsApp::announceStartup() const
{
    // ------------------------------------------------------------------------
    // Announce startup
    // ------------------------------------------------------------------------
    const QDateTime dt = datetime::now();
    qInfo() << "CamCOPS starting at local time:"
            << qUtf8Printable(datetime::datetimeToIsoMs(dt));
    qInfo() << "CamCOPS starting at UTC time:"
            << qUtf8Printable(datetime::datetimeToIsoMsUtc(dt));
    qInfo() << "CamCOPS version:" << camcopsversion::CAMCOPS_CLIENT_VERSION;
    qDebug().noquote() << "Compiler:" << platform::COMPILER_NAME_VERSION;
    qDebug().noquote() << "Compiled at:" << platform::COMPILED_WHEN;
}

void CamcopsApp::registerDatabaseDrivers()
{
#ifdef USE_SQLCIPHER
    QSqlDatabase::
        registerSqlDriver(whichdb::SQLCIPHER, new QSqlDriverCreator<SQLCipherDriver>);
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
    m_datadb = DatabaseManagerPtr(
        new DatabaseManager(data_filename, CONNECTION_DATA)
    );
    m_sysdb = DatabaseManagerPtr(new DatabaseManager(
        sys_filename,
        CONNECTION_SYS,
        whichdb::DBTYPE,
        true, /* threaded */
        true /* system_db */
    ));
}

void CamcopsApp::closeDatabases()
{
    m_datadb = nullptr;
    m_sysdb = nullptr;
}

bool CamcopsApp::connectDatabaseEncryption(
    QString& new_user_password, bool& user_cancelled_please_quit
)
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
    const QString new_pw_text(
        tr("Enter a new password for the CamCOPS application")
    );
    const QString new_pw_title(tr("Set CamCOPS password"));
    const QString enter_pw_text(tr("Enter the password to unlock CamCOPS"));
    const QString enter_pw_title(tr("Enter CamCOPS password"));

    while (!encryption_happy) {
        changed_user_password = false;
        const bool no_password_sys = m_sysdb->canReadDatabase();
        const bool no_password_data = m_datadb->canReadDatabase();

        if (no_password_sys != no_password_data) {
            const QString msg
                = QString(tr("CamCOPS uses a system and a data database; one "
                             "has a "
                             "password and one doesn't (no_password_sys = %1, "
                             "no_password_data = %2); this is an incongruent "
                             "state "
                             "that has probably arisen from user error, and "
                             "CamCOPS will not continue until this is fixed."))
                      .arg(no_password_sys)
                      .arg(no_password_data);
            const QString title(tr("Inconsistent database state"));
            uifunc::stopApp(msg, title);
        }

        if (no_password_sys) {

            qInfo() << "Databases have no password yet, and need one.";
            QString dummy_old_password;
            if (!uifunc::getOldNewPasswords(
                    new_pw_text,
                    new_pw_title,
                    false /* require_old_password */,
                    dummy_old_password,
                    new_user_password,
                    nullptr
                )) {

                // The user quit without setting a password.
                // If we don't delete the database here, the next attempt to
                // set up a password will fail (canReadDatabase() calls below
                // will return false) and the user will be forced to set up
                // another one.
                deleteDatabases();
                user_cancelled_please_quit = true;

                return false;
            }
            qInfo() << "Encrypting databases for the first time...";
            if (!m_sysdb->databaseIsEmpty() || !m_datadb->databaseIsEmpty()) {
                qInfo() << "... by rewriting the databases...";
                encryption_happy
                    = encryptExistingPlaintextDatabases(new_user_password);
            } else {
                qInfo() << "... by encrypting empty databases...";
                encryption_happy = true;
            }
            changed_user_password = true;
            // Whether we've encrypted an existing database (then reopened it)
            // or just opened a fresh one, we need to apply the key now.
            encryption_happy = encryption_happy
                && m_sysdb->pragmaKey(new_user_password)
                && m_datadb->pragmaKey(new_user_password)
                && m_sysdb->canReadDatabase() && m_datadb->canReadDatabase();
            if (encryption_happy) {
                qInfo() << "... successfully encrypted the databases.";
            } else {
                qInfo() << "... failed to encrypt; trying again.";
            }

        } else {

            qInfo(
            ) << "Databases are encrypted. Requesting password from user.";
            QString user_password;
            if (!uifunc::getPassword(
                    enter_pw_text, enter_pw_title, user_password, nullptr
                )) {
                user_cancelled_please_quit = true;
                return false;
            }
            qInfo() << "Attempting to decrypt databases...";
            // Migrate from old versions of SQLCipher if necessary
            {
                // Note that special things must be done to pass a reference
                // via std::bind; see
                // https://stackoverflow.com/questions/26187192/how-to-bind-function-to-an-object-by-reference.
                // Options include std::ref() and using pointers instead.
                SlowNonGuiFunctionCaller slow_caller(
                    std::bind(
                        &CamcopsApp::workerDecryptDatabases,
                        this,
                        user_password,
                        std::ref(encryption_happy)
                    ),
                    m_p_main_window,
                    tr("Decrypting databases..."),
                    TextConst::pleaseWait()
                );
                // ... writes to encryption_happy
            }
            if (encryption_happy) {
                qInfo() << "... successfully accessed encrypted databases.";
            } else {

                if (!userConfirmedRetryPassword()) {
                    if (userConfirmedDeleteDatabases()) {
                        qInfo() << "... deleting databases.";
                        const bool ok = deleteDatabases();
                        if (!ok) {
                            // For some reason the sqlite files couldn't be
                            // deleted. User has been prompted to delete the
                            // files manually.
                            user_cancelled_please_quit = true;
                            return false;
                        }
                        qInfo() << "... recreating databases.";
                        openOrCreateDatabases();
                    }
                }

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
        stopApp(
            tr("Can't read system database; corrupted? encrypted? (This "
               "version of CamCOPS has had its encryption facilities "
               "disabled.)")
        );
    }
    if (!dbfunc::canReadDatabase(m_datadb)) {
        stopApp(
            tr("Can't read data database; corrupted? encrypted? (This "
               "version of CamCOPS has had its encryption facilities "
               "disabled.)")
        );
    }
    return false;  // user password not changed
#endif
}

bool CamcopsApp::userConfirmedRetryPassword() const
{
    //: %1 and %2 are Yes and No respectively i.e. the dialog button labels
    return uifunc::confirm(
        tr("You entered an incorrect password. Try again?<br><br>"
           "Answer <b>%1</b> to enter your password again.<br>"
           "Answer <b>%2</b> if you can't remember your password.")
            .arg(TextConst::yes())
            .arg(TextConst::no()),
        tr("Retry password?"),
        TextConst::yes(),
        TextConst::no()
    );
}

bool CamcopsApp::userConfirmedDeleteDatabases() const
{
    return uifunc::confirmDangerousOperation(
        tr("The only way to reset your password is to delete all of the data "
           "from the database.\nAny records not uploaded to the server will "
           "be "
           "lost."),
        tr("Delete database?")
    );
}

bool CamcopsApp::deleteDatabases()
{
    QString data_error_string;
    QString sys_error_string;

    const bool data_ok
        = deleteDatabase(dbfunc::DATA_DATABASE_FILENAME, data_error_string);
    const bool sys_ok
        = deleteDatabase(dbfunc::SYSTEM_DATABASE_FILENAME, sys_error_string);

    if (data_ok && sys_ok) {
        return true;
    }

    QString error_string;

    if (!data_ok) {
        error_string = data_error_string;
    }

    if (!sys_ok) {
        error_string += "\n" + sys_error_string;
    }
    uifunc::alert(
        tr("CamCOPS could not delete its databases:\n\n"
           "%1\n"
           "Please try to delete these files manually and restart CamCOPS\n")
            .arg(error_string)
    );

    return false;
}

bool CamcopsApp::deleteDatabase(const QString& filename, QString& error_string)
{
    const QString fullpath = dbFullPath(filename);
    QFile file(fullpath);
    const bool ok = file.remove();

    if (!ok) {
        error_string = tr("Failed to delete file:\n"
                          "%1\n"
                          "because of this error:\n"
                          "%2\n")
                           .arg(fullpath, file.errorString());
    }

    return ok;
}

void CamcopsApp::workerDecryptDatabases(
    const QString& passphrase, bool& success
)
{
    success = m_sysdb->decrypt(passphrase) && m_datadb->decrypt(passphrase);
    qDebug() << Q_FUNC_INFO << success;
}

bool CamcopsApp::encryptExistingPlaintextDatabases(const QString& passphrase)
{
    using filefunc::fileExists;
    qInfo() << "... closing databases";
    closeDatabases();
    const QString sys_main = dbFullPath(dbfunc::SYSTEM_DATABASE_FILENAME);
    const QString sys_temp = dbFullPath(
        dbfunc::SYSTEM_DATABASE_FILENAME
        + dbfunc::DATABASE_FILENAME_TEMP_SUFFIX
    );
    const QString data_main = dbFullPath(dbfunc::DATA_DATABASE_FILENAME);
    const QString data_temp = dbFullPath(
        dbfunc::DATA_DATABASE_FILENAME + dbfunc::DATABASE_FILENAME_TEMP_SUFFIX
    );
    qInfo() << "... encrypting";
    dbfunc::encryptPlainDatabaseInPlace(sys_main, sys_temp, passphrase);
    dbfunc::encryptPlainDatabaseInPlace(data_main, data_temp, passphrase);
    qInfo() << "... re-opening databases";
    openOrCreateDatabases();
    return true;
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
    DbNestableTransaction trans(*m_sysdb
    );  // https://www.sqlite.org/faq.html#q19

    // Client mode
    createVar(
        varconst::MODE, QMetaType::fromType<int>(), varconst::MODE_NOT_SET
    );

    // If the mode is single user, store the one and only patient ID here
    createVar(
        varconst::SINGLE_PATIENT_ID,
        QMetaType::fromType<int>(),
        dbconst::NONEXISTENT_PK
    );
    createVar(
        varconst::SINGLE_PATIENT_PROQUINT, QMetaType::fromType<QString>(), ""
    );

    // Language
    createVar(
        varconst::LANGUAGE,
        QMetaType::fromType<QString>(),
        QLocale::system().name()
    );

    // Version
    createVar(
        varconst::CAMCOPS_TABLET_VERSION_AS_STRING,
        QMetaType::fromType<QString>(),
        camcopsversion::CAMCOPS_CLIENT_VERSION.toString()
    );

    // Questionnaire
    createVar(
        varconst::QUESTIONNAIRE_SIZE_PERCENT, QMetaType::fromType<int>(), 100
    );
    createVar(
        varconst::OVERRIDE_LOGICAL_DPI, QMetaType::fromType<bool>(), false
    );
    createVar(
        varconst::OVERRIDE_LOGICAL_DPI_X,
        QMetaType::fromType<double>(),
        uiconst::DEFAULT_DPI.x
    );
    createVar(
        varconst::OVERRIDE_LOGICAL_DPI_Y,
        QMetaType::fromType<double>(),
        uiconst::DEFAULT_DPI.y
    );
    createVar(
        varconst::OVERRIDE_PHYSICAL_DPI, QMetaType::fromType<bool>(), false
    );
    createVar(
        varconst::OVERRIDE_PHYSICAL_DPI_X,
        QMetaType::fromType<double>(),
        uiconst::DEFAULT_DPI.x
    );
    createVar(
        varconst::OVERRIDE_PHYSICAL_DPI_Y,
        QMetaType::fromType<double>(),
        uiconst::DEFAULT_DPI.y
    );

    // Server
    createVar(varconst::SERVER_ADDRESS, QMetaType::fromType<QString>(), "");
    createVar(
        varconst::SERVER_PORT, QMetaType::fromType<int>(), DEFAULT_SERVER_PORT
    );
    createVar(
        varconst::SERVER_PATH,
        QMetaType::fromType<QString>(),
        "camcops/database"
    );
    createVar(varconst::SERVER_TIMEOUT_MS, QMetaType::fromType<int>(), 50000);
    createVar(
        varconst::VALIDATE_SSL_CERTIFICATES, QMetaType::fromType<bool>(), true
    );
    createVar(
        varconst::SSL_PROTOCOL,
        QMetaType::fromType<QString>(),
        convert::SSLPROTODESC_SECUREPROTOCOLS
    );
    createVar(
        varconst::DEBUG_USE_HTTPS_TO_SERVER, QMetaType::fromType<bool>(), true
    );
    createVar(
        varconst::STORE_SERVER_PASSWORD, QMetaType::fromType<bool>(), true
    );
    createVar(
        varconst::UPLOAD_METHOD,
        QMetaType::fromType<int>(),
        varconst::DEFAULT_UPLOAD_METHOD
    );
    createVar(
        varconst::MAX_DBSIZE_FOR_ONESTEP_UPLOAD,
        QMetaType::fromType<qlonglong>(),
        varconst::DEFAULT_MAX_DBSIZE_FOR_ONESTEP_UPLOAD
    );

    // Uploading "dirty" flag
    createVar(varconst::NEEDS_UPLOAD, QMetaType::fromType<bool>(), false);

    // Terms and conditions
    createVar(varconst::AGREED_TERMS_AT, QMetaType::fromType<QDateTime>());

    // Intellectual property
    createVar(
        varconst::IP_USE_CLINICAL,
        QMetaType::fromType<int>(),
        CommonOptions::UNKNOWN_INT
    );
    createVar(
        varconst::IP_USE_COMMERCIAL,
        QMetaType::fromType<int>(),
        CommonOptions::UNKNOWN_INT
    );
    createVar(
        varconst::IP_USE_EDUCATIONAL,
        QMetaType::fromType<int>(),
        CommonOptions::UNKNOWN_INT
    );
    createVar(
        varconst::IP_USE_RESEARCH,
        QMetaType::fromType<int>(),
        CommonOptions::UNKNOWN_INT
    );

    // Patients and policies
    createVar(varconst::ID_POLICY_UPLOAD, QMetaType::fromType<QString>(), "");
    createVar(
        varconst::ID_POLICY_FINALIZE, QMetaType::fromType<QString>(), ""
    );

    // Other information from server
    createVar(
        varconst::SERVER_DATABASE_TITLE, QMetaType::fromType<QString>(), ""
    );
    createVar(
        varconst::SERVER_CAMCOPS_VERSION, QMetaType::fromType<QString>(), ""
    );
    createVar(
        varconst::LAST_SERVER_REGISTRATION, QMetaType::fromType<QDateTime>()
    );
    createVar(
        varconst::LAST_SUCCESSFUL_UPLOAD, QMetaType::fromType<QDateTime>()
    );

    // User
    // ... server interaction
    createVar(
        varconst::DEVICE_FRIENDLY_NAME, QMetaType::fromType<QString>(), ""
    );
    createVar(varconst::SERVER_USERNAME, QMetaType::fromType<QString>(), "");
    createVar(
        varconst::SERVER_USERPASSWORD_OBSCURED,
        QMetaType::fromType<QString>(),
        ""
    );
    createVar(
        varconst::OFFER_UPLOAD_AFTER_EDIT, QMetaType::fromType<bool>(), false
    );
    // ... default clinician details
    createVar(
        varconst::DEFAULT_CLINICIAN_SPECIALTY,
        QMetaType::fromType<QString>(),
        ""
    );
    createVar(
        varconst::DEFAULT_CLINICIAN_NAME, QMetaType::fromType<QString>(), ""
    );
    createVar(
        varconst::DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION,
        QMetaType::fromType<QString>(),
        ""
    );
    createVar(
        varconst::DEFAULT_CLINICIAN_POST, QMetaType::fromType<QString>(), ""
    );
    createVar(
        varconst::DEFAULT_CLINICIAN_SERVICE, QMetaType::fromType<QString>(), ""
    );
    createVar(
        varconst::DEFAULT_CLINICIAN_CONTACT_DETAILS,
        QMetaType::fromType<QString>(),
        ""
    );

    // Cryptography
    createVar(varconst::OBSCURING_KEY, QMetaType::fromType<QString>(), "");
    createVar(varconst::OBSCURING_IV, QMetaType::fromType<QString>(), "");
    // setEncryptedServerPassword("hello I am a password");
    // qDebug() << getPlaintextServerPassword();
    createVar(
        varconst::USER_PASSWORD_HASH, QMetaType::fromType<QString>(), ""
    );
    createVar(
        varconst::PRIV_PASSWORD_HASH, QMetaType::fromType<QString>(), ""
    );

    // Device ID
    createVar(varconst::DEVICE_ID, QMetaType::fromType<QUuid>());
    if (var(varconst::DEVICE_ID).isNull()) {
        regenerateDeviceId();
    }

    // User-Agent header
    createVar(
        varconst::USER_AGENT,
        QMetaType::fromType<QString>(),
        defaultUserAgent()
    );

    m_storedvars_available = true;
}

Version CamcopsApp::upgradeDatabaseBeforeTablesMade()
{
    const Version old_version(
        varString(varconst::CAMCOPS_TABLET_VERSION_AS_STRING)
    );
    const Version new_version = camcopsversion::CAMCOPS_CLIENT_VERSION;
    if (old_version == new_version) {
        qInfo() << "Database is current; no special upgrade steps required";
        return old_version;
    }
    qInfo() << "Considering system-wide special database upgrade steps from "
               "version"
            << old_version << "to version" << new_version;

    // ------------------------------------------------------------------------
    // System-wide database upgrade steps go here
    // ------------------------------------------------------------------------

    // ------------------------------------------------------------------------
    // ... done
    // ------------------------------------------------------------------------

    qInfo() << "System-wide database upgrade steps complete";
    setVar(varconst::CAMCOPS_TABLET_VERSION_AS_STRING, new_version.toString());
    return old_version;
}

void CamcopsApp::upgradeDatabaseAfterTasksRegistered(const Version& old_version
)
{
    // ------------------------------------------------------------------------
    // Any database upgrade required? STEP 2: INDIVIDUAL TASKS.
    // ------------------------------------------------------------------------
    const Version new_version = camcopsversion::CAMCOPS_CLIENT_VERSION;
    if (old_version == new_version) {
        // User message will have appeared above.
        return;
    }

    Q_ASSERT(m_p_task_factory);
    m_p_task_factory->upgradeDatabase(old_version, new_version);
}

void CamcopsApp::makeOtherTables()
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

    TaskSchedule task_schedule_specimen(*this, *m_sysdb);
    task_schedule_specimen.makeTable();

    TaskScheduleItem task_schedule_item_specimen(*this, *m_sysdb);
    task_schedule_item_specimen.makeTable();

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
    qInfo().nospace().noquote()
        << "Registered tasks (n = " << tablenames.length()
        << "): " << tablenames.join(", ");
}

void CamcopsApp::dangerCommandLineMinimalSetup()
{
    // Ugly code -- only used for command-line calls that need a fictional
    // database. There is NO PROPER DATABASE, but all our task code requires
    // specimen instances (not class-level code); in turn, that requires a
    // database framework. So create in-memory SQLite database.

    // ------------------------------------------------------------------------
    // Stuff usually done later in CamcopsApp::run()
    // ------------------------------------------------------------------------
    registerDatabaseDrivers();

    // Instead of openOrCreateDatabases():
    const QString in_memory_sqlite_db(":memory:");
    // https://www.sqlite.org/inmemorydb.html
    m_datadb = DatabaseManagerPtr(
        new DatabaseManager(in_memory_sqlite_db, CONNECTION_DATA)
    );
    m_sysdb = DatabaseManagerPtr(new DatabaseManager(
        in_memory_sqlite_db,
        CONNECTION_SYS,
        whichdb::DBTYPE,
        true, /* threaded */
        true /* system_db */
    ));

    makeStoredVarTable();
    createStoredVars();

    // ------------------------------------------------------------------------
    // Stuff usually done in backgroundStartup()
    // ------------------------------------------------------------------------
    makeOtherTables();
    registerTasks();
    makeTaskTables();
}

void CamcopsApp::printTasksWithoutDatabase(QTextStream& stream)
{
    dangerCommandLineMinimalSetup();
    stream << *m_p_task_factory;
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
        m_qt_logical_dpi = uiconst::DEFAULT_DPI;
        m_qt_physical_dpi = uiconst::DEFAULT_DPI;
    } else {
        const QScreen* screen = all_screens.at(0);
        m_qt_logical_dpi.x = screen->logicalDotsPerInchX();
        // ... can be e.g. 96.0126
        m_qt_logical_dpi.y = screen->logicalDotsPerInchY();
        // ... can be e.g. 96.0126
        // https://stackoverflow.com/questions/16561879/what-is-the-difference-between-logicaldpix-and-physicaldpix-in-qt
        m_qt_physical_dpi.x = screen->physicalDotsPerInchX();
        m_qt_physical_dpi.y = screen->physicalDotsPerInchY();
    }
    qInfo().nospace() << "System's first display has logical DPI "
                      << m_qt_logical_dpi.description() << " and physical DPI "
                      << m_qt_physical_dpi.description();
}

void CamcopsApp::setDPI()
{
    // We write to some global "not-quite-constants".
    // This is slightly nasty, but it saves a great deal of things referring
    // to the CamcopsApp that otherwise wouldn't need to.

    // The storedvars must be available.

    const bool override_logical = varBool(varconst::OVERRIDE_LOGICAL_DPI);
    const bool override_physical = varBool(varconst::OVERRIDE_PHYSICAL_DPI);

    if (override_logical) {
        // Override
        uiconst::g_logical_dpi = Dpi(
            varDouble(varconst::OVERRIDE_LOGICAL_DPI_X),
            varDouble(varconst::OVERRIDE_LOGICAL_DPI_Y)
        );
    } else {
        // Use Qt DPI directly.
        uiconst::g_logical_dpi = m_qt_logical_dpi;
    }

    if (override_physical) {
        // Override
        uiconst::g_physical_dpi = Dpi(
            varDouble(varconst::OVERRIDE_PHYSICAL_DPI_X),
            varDouble(varconst::OVERRIDE_PHYSICAL_DPI_Y)
        );
    } else {
        // Use Qt DPI directly.
        uiconst::g_physical_dpi = m_qt_physical_dpi;
    }

    auto cvSize = [](const QSize& size) -> QSize {
        return convert::convertSizeByLogicalDpi(size);
    };
    auto cvLengthX = [](int length) -> int {
        return convert::convertLengthByLogicalDpiX(length);
    };
    auto cvLengthY = [](int length) -> int {
        return convert::convertLengthByLogicalDpiY(length);
    };

    uiconst::g_iconsize = cvSize(uiconst::ICONSIZE_FOR_DEFAULT_DPI);
    uiconst::g_small_iconsize
        = cvSize(uiconst::SMALL_ICONSIZE_FOR_DEFAULT_DPI);
    uiconst::g_min_spinbox_height
        = cvLengthY(uiconst::MIN_SPINBOX_HEIGHT_FOR_DEFAULT_DPI);
    uiconst::g_slider_handle_size_px
        = cvLengthX(uiconst::SLIDER_HANDLE_SIZE_PX_FOR_DEFAULT_DPI);
    uiconst::g_dial_diameter_px
        = cvLengthX(uiconst::DIAL_DIAMETER_PX_FOR_DEFAULT_DPI);
}

Dpi CamcopsApp::qtLogicalDotsPerInch() const
{
    return m_qt_logical_dpi;
}

Dpi CamcopsApp::qtPhysicalDotsPerInch() const
{
    return m_qt_physical_dpi;
}

void CamcopsApp::initGuiTwoStylesheet()
{
    // Qt stuff: after storedvars accessible
    setDPI();
    setStyleSheet(getSubstitutedCss(uiconst::CSS_CAMCOPS_MAIN));
}

void CamcopsApp::openMainWindow()
{
#ifdef DEBUG_SCREEN_STACK
    qDebug() << Q_FUNC_INFO;
#endif
    m_p_main_window = new QMainWindow();
    m_p_window_stack = new QStackedWidget(m_p_main_window);
    m_p_hidden_stack = QSharedPointer<QStackedWidget>(new QStackedWidget());
#if 0  // doesn't work
    // We want to stay height-for-width all the way to the top:
    auto master_layout = new VBoxLayout();
    m_p_main_window->setLayout(master_layout);
    master_layout->addWidget(m_p_window_stack);
#else
    m_p_main_window->setCentralWidget(m_p_window_stack);
#endif

    if (!needToRegisterSinglePatient()) {
        recreateMainMenu();
    }

    m_p_main_window->showMaximized();
}

bool CamcopsApp::needToRegisterSinglePatient() const
{
    if (isSingleUserMode()) {
        return getSinglePatientId() == dbconst::NONEXISTENT_PK;
    }

    return false;
}

void CamcopsApp::recreateMainMenu()
{
    closeAnyOpenSubWindows();

    if (isClinicianMode()) {
        return openSubWindow(new MainMenu(*this));
    }

    return openSubWindow(new SingleUserMenu(*this));
}

void CamcopsApp::closeAnyOpenSubWindows()
{
    // Scope for optimisation here as we're tearing down everything
    bool last_window;

    do {
        last_window = m_info_stack.isEmpty();

        if (!last_window) {
            m_info_stack.pop();
        }

        QWidget* top = m_p_window_stack->currentWidget();
        if (top) {
            m_p_window_stack->removeWidget(top);
            top->deleteLater();

            if (m_p_hidden_stack->count() > 0) {
                QWidget* w
                    = m_p_hidden_stack->widget(m_p_hidden_stack->count() - 1);
                m_p_hidden_stack->removeWidget(w);
                const int index = m_p_window_stack->addWidget(w);
                m_p_window_stack->setCurrentIndex(index);
            }
        }
    } while (!last_window);
}

void CamcopsApp::makeNetManager()
{
    Q_ASSERT(m_p_main_window.data());
    m_netmgr = QSharedPointer<NetworkManager>(new NetworkManager(
        *this, *m_datadb, m_p_task_factory, m_p_main_window.data()
    ));
}

void CamcopsApp::reconnectNetManager(
    NetMgrCancelledCallback cancelled_callback,
    NetMgrFinishedCallback finished_callback
)
{
    if (!m_netmgr) {
        makeNetManager();
    }

    // Get the raw pointer, for signals work
    NetworkManager* netmgr = networkManager();

    // Disconnect everything connected to its signals:
    disconnect(netmgr, nullptr, nullptr, nullptr);

    // Reconnect:
    if (finished_callback) {
        connect(
            netmgr,
            &NetworkManager::finished,
            this,
            finished_callback,
            Qt::UniqueConnection
        );
    }
    if (cancelled_callback) {
        connect(
            netmgr,
            &NetworkManager::cancelled,
            this,
            cancelled_callback,
            Qt::UniqueConnection
        );
    }
}

void CamcopsApp::enableNetworkLogging()
{
    if (m_netmgr) {
        m_netmgr->enableLogging();
    }
}

void CamcopsApp::disableNetworkLogging()
{
    if (m_netmgr) {
        m_netmgr->disableLogging();
    }
}

bool CamcopsApp::isLoggingNetwork()
{
    if (m_netmgr) {
        return m_netmgr->isLogging();
    }

    return false;
}

QString CamcopsApp::defaultUserAgent() const
{
    const QString platform = QString("%1 %2").arg(
        platform::OS_CLASS, QSysInfo::currentCpuArchitecture()
    );
    const QString version = camcopsversion::CAMCOPS_CLIENT_VERSION.toString();

    const QString user_agent
        = QString("Mozilla/5.0 (%1) CamCOPS/%2").arg(platform, version);

    return user_agent;
}

void CamcopsApp::setUserAgentFromUser()
{
    UserAgentDialog dialog(defaultUserAgent(), userAgent());
    const int reply = dialog.exec();
    if (reply == QDialog::Accepted) {
        setUserAgent(dialog.userAgent());
    }
}

QString CamcopsApp::userAgent() const
{
    return varString(varconst::USER_AGENT);
}

void CamcopsApp::setUserAgent(const QString user_agent)
{
    setVar(varconst::USER_AGENT, user_agent);
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

SlowGuiGuard CamcopsApp::getSlowGuiGuard(
    const QString& text, const QString& title, const int minimum_duration_ms
)
{
    return SlowGuiGuard(
        *this, m_p_main_window, title, text, minimum_duration_ms
    );
}

void CamcopsApp::openSubWindow(
    OpenableWidget* widget,
    TaskPtr task,
    const bool may_alter_task,
    PatientPtr patient
)
{
    if (!widget) {
        qCritical() << Q_FUNC_INFO << "- attempt to open nullptr";
        return;
    }

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
            m_p_window_stack->removeWidget(w);
            // ... m_p_window_stack still owns w
            m_p_hidden_stack->addWidget(w);  // m_p_hidden_stack now owns w
        }
    }

    // ------------------------------------------------------------------------
    // Set the fullscreen state (before we build, for efficiency)
    // ------------------------------------------------------------------------
    bool wants_fullscreen = widget->wantsFullscreen();
    if (wants_fullscreen) {
        enterFullscreen();
    }

    // ------------------------------------------------------------------------
    // Add new thing to visible (one-item) "stack"
    // ------------------------------------------------------------------------
    int index = m_p_window_stack->addWidget(widget);  // will show the widget
    // The stack takes over ownership.

    // ------------------------------------------------------------------------
    // Build, if the OpenableWidget wants to be built
    // ------------------------------------------------------------------------
    {
        // BEWARE where you put getSlowGuiGuard(); under Windows it can
        // interfere with entry/exit from fullscreen mode (and screw up mouse
        // responsiveness afterwards); see compilation_windows.txt
        SlowGuiGuard guard = getSlowGuiGuard();

        // qDebug() << Q_FUNC_INFO << "About to build";
        widget->build();
        // qDebug() << Q_FUNC_INFO << "Build complete, about to show";
    }

    // ------------------------------------------------------------------------
    // Make it visible
    // ------------------------------------------------------------------------
    m_p_window_stack->setCurrentIndex(index);

    // ------------------------------------------------------------------------
    // Signals
    // ------------------------------------------------------------------------
    connect(
        widget,
        &OpenableWidget::enterFullscreen,
        this,
        &CamcopsApp::enterFullscreen
    );
    connect(
        widget,
        &OpenableWidget::leaveFullscreen,
        this,
        &CamcopsApp::leaveFullscreen
    );
    connect(
        widget, &OpenableWidget::finished, this, &CamcopsApp::closeSubWindow
    );

    // ------------------------------------------------------------------------
    // Save information and manage ownership of associated things
    // ------------------------------------------------------------------------
    m_info_stack.push(OpenableInfo(
        guarded_widget,
        task,
        prev_window_state,
        wants_fullscreen,
        may_alter_task,
        patient
    ));
    // This stores a QSharedPointer to the task (if supplied), so keeping that
    // keeps the task "alive" whilst its widget is doing things.
    // Similarly with any patient required for patient editing.
}

void CamcopsApp::closeSubWindow()
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
    // Determine next fullscreen state
    // ------------------------------------------------------------------------
    // If a window earlier in the stack has asked for fullscreen, we will
    // stay fullscreen.
    bool want_fullscreen = false;
    for (const OpenableInfo& info : m_info_stack) {
        if (info.wants_fullscreen) {
            want_fullscreen = true;
            break;
        }
    }

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
    // - From https://doc.qt.io/qt-6.5/qstackedwidget.html#removeWidget :
    //      Removes widget from the QStackedWidget. i.e., widget is not deleted
    //      but simply removed from the stacked layout, causing it to be
    //      hidden. Note: Ownership of widget reverts to the application.
    // - From https://doc.qt.io/qt-6.5/qstackedwidget.html#removeWidget :
    //      Removes widget from the QStackedWidget. i.e., widget is not deleted
    //      but simply removed from the stacked layout, causing it to be
    //      hidden. Note: Parent object and parent widget of widget will remain
    //      the QStackedWidget. If the application wants to reuse the removed
    //      widget, then it is recommended to re-parent it.
    //   ... same for Qt 5.11.
    // - Also:
    //   https://stackoverflow.com/questions/2506625/how-to-delete-a-widget-from-a-stacked-widget-in-qt
    // But this should work regardless:
    top->deleteLater();  // later, in case it was this object that called us

    // ------------------------------------------------------------------------
    // Restore the widget from the top of the hidden stack
    // ------------------------------------------------------------------------
    Q_ASSERT(m_p_hidden_stack->count() > 0);
    // ... the m_info_stack.isEmpty() check should exclude this
    QWidget* w = m_p_hidden_stack->widget(m_p_hidden_stack->count() - 1);
    m_p_hidden_stack->removeWidget(w);  // m_p_hidden_stack still owns w
    const int index = m_p_window_stack->addWidget(w);
    // ... m_p_window_stack now owns w
    m_p_window_stack->setCurrentIndex(index);

    // ------------------------------------------------------------------------
    // Set next fullscreen state
    // ------------------------------------------------------------------------
    if (!want_fullscreen) {
        leaveFullscreen();  // will do nothing if we're not fullscreen now
    }

    // ------------------------------------------------------------------------
    // Update objects that care as to changes that may have been wrought
    // ------------------------------------------------------------------------
    if (info.may_alter_task) {
#ifdef DEBUG_EMIT
        qDebug() << Q_FUNC_INFO << "Emitting taskAlterationFinished";
#endif
        emit taskAlterationFinished(info.task);

        if (shouldUploadNow()) {
            upload();
        }
    } else {
        if (isSingleUserMode() && m_info_stack.size() == 1) {
            // If the user went back to the main menu and hasn't just
            // finished a task, attempt to upload any pending tasks. This will
            // only be necessary when the device wasn't connected to the
            // network before.
            retryUpload();
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

    emit subWindowFinishedClosing();
}

bool CamcopsApp::shouldUploadNow() const
{
    if (varBool(varconst::OFFER_UPLOAD_AFTER_EDIT)
        && varBool(varconst::NEEDS_UPLOAD)) {

        if (isClinicianMode()) {
            return userConfirmedUpload();
        }

        return true;
    }

    return false;
}

bool CamcopsApp::userConfirmedUpload() const
{
    ScrollMessageBox msgbox(
        QMessageBox::Question,
        tr("Upload?"),
        tr("Task finished. Upload data to server now?"),
        m_p_main_window
    );  // parent
    QAbstractButton* yes
        = msgbox.addButton(tr("Yes, upload"), QMessageBox::YesRole);
    msgbox.addButton(tr("No, cancel"), QMessageBox::NoRole);
    msgbox.exec();

    return msgbox.clickedButton() == yes;
}

void CamcopsApp::enterFullscreen()
{
    // QWidget::showFullScreen does this:
    //
    // ensurePolished();
    // setWindowState(
    //      (windowState() & ~(Qt::WindowMinimized | Qt::WindowMaximized))
    //      | Qt::WindowFullScreen
    // );
    // setVisible(true);
    // activateWindow();

    // In other words, it clears the maximized flag. So we want this:
#ifdef DEBUG_SCREEN_STACK
    qDebug() << Q_FUNC_INFO
             << "old windowState():" << m_p_main_window->windowState();
#endif
    Qt::WindowStates old_state = m_p_main_window->windowState();
    if (old_state & Qt::WindowFullScreen) {
        return;  // already fullscreen
    }
    m_maximized_before_fullscreen = old_state & Qt::WindowMaximized;
#ifdef DEBUG_SCREEN_STACK
    qDebug() << Q_FUNC_INFO
             << "calling showFullScreen(); m_maximized_before_fullscreen ="
             << m_maximized_before_fullscreen;
#endif
    m_p_main_window->showFullScreen();
#ifdef DEBUG_SCREEN_STACK
    qDebug() << Q_FUNC_INFO
             << "new windowState():" << m_p_main_window->windowState();
#endif
}

void CamcopsApp::leaveFullscreen()
{
#ifdef DEBUG_SCREEN_STACK
    qDebug() << Q_FUNC_INFO
             << "old windowState():" << m_p_main_window->windowState();
#endif
    Qt::WindowStates old_state = m_p_main_window->windowState();
    if (!(old_state & Qt::WindowFullScreen)) {
        return;  // wasn't fullscreen
    }

    // m_p_main_window->showNormal();
    //
    // The docs say: "To return from full-screen mode, call showNormal()."
    // That's true, but incomplete. Both showFullscreen() and showNormal() turn
    // off any maximized state. QWidget::showNormal() does this:
    //
    // ensurePolished();
    // setWindowState(windowState() & ~(Qt::WindowMinimized
    //                                  | Qt::WindowMaximized
    //                                  | Qt::WindowFullScreen));
    // setVisible(true);

    // So, how to return to maximized mode from fullscreen?
    if (platform::PLATFORM_WINDOWS) {
        // Under Windows, this works:
        m_p_main_window->ensurePolished();
        Qt::WindowStates new_state
            = ((old_state &
                // Flags to turn off:
                ~(Qt::WindowMinimized | Qt::WindowMaximized
                  | Qt::WindowFullScreen))
               |
               // Flags to turn on:
               (m_maximized_before_fullscreen ? Qt::WindowMaximized
                                              : Qt::WindowNoState)
               // ... Qt::WindowNoState is zero, i.e. no flag
            );
#ifdef DEBUG_SCREEN_STACK
        qDebug() << Q_FUNC_INFO
                 << "calling setWindowState() with:" << new_state;
#endif
        m_p_main_window->setWindowState(new_state);
        m_p_main_window->setVisible(true);
    } else {
        // Under Linux, the method above doesn't; that takes it to normal mode.
        // Under Linux, showMaximized() also takes it to normal mode!
        // But under Linux, calling showNormal() then showMaximized()
        // immediately does work.
        if (m_maximized_before_fullscreen) {
#ifdef DEBUG_SCREEN_STACK
            qDebug() << Q_FUNC_INFO
                     << "calling showMaximized() then showMaximized()";
#endif
            // Under Linux, if you start with a fullscreen window and call
            // showMaximized(), it goes to normal mode. Also if you do this:
            // But this works:
            m_p_main_window->showNormal();
            m_p_main_window->showMaximized();
        } else {
#ifdef DEBUG_SCREEN_STACK
            qDebug() << Q_FUNC_INFO << "calling showNormal()";
#endif
            m_p_main_window->showNormal();
        }
    }

    // Done.
#ifdef DEBUG_SCREEN_STACK
    qDebug() << Q_FUNC_INFO
             << "new windowState():" << m_p_main_window->windowState();
#endif
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
    if (lockstate() == LockState::Privileged
        || checkPassword(
            varconst::USER_PASSWORD_HASH,
            tr("Enter app password"),
            tr("Unlock")
        )) {
        setLockState(LockState::Unlocked);
    }
}

void CamcopsApp::lock()
{
    setLockState(LockState::Locked);
}

void CamcopsApp::grantPrivilege()
{
    if (checkPassword(
            varconst::PRIV_PASSWORD_HASH,
            tr("Enter privileged-mode password"),
            tr("Set privileged mode")
        )) {
        setLockState(LockState::Privileged);
    }
}

bool CamcopsApp::checkPassword(
    const QString& hashed_password_varname,
    const QString& text,
    const QString& title
)
{
    const QString hashed_password = varString(hashed_password_varname);
    if (hashed_password.isEmpty()) {
        // If there's no password, we just allow the operation.
        return true;
    }
    QString password;
    const bool ok
        = uifunc::getPassword(text, title, password, m_p_main_window);
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
    const bool changed = changePassword(
        varconst::USER_PASSWORD_HASH, title, nullptr, &new_password
    );
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
    changePassword(
        varconst::PRIV_PASSWORD_HASH, tr("Change privileged-mode password")
    );
}

bool CamcopsApp::changePassword(
    const QString& hashed_password_varname,
    const QString& text,
    QString* p_old_password,
    QString* p_new_password
)
{
    // Returns: changed?
    const QString old_password_hash = varString(hashed_password_varname);
    const bool old_password_exists = !old_password_hash.isEmpty();
    QString old_password_from_user;
    QString new_password;
    const bool ok = uifunc::getOldNewPasswords(
        text,
        text,
        old_password_exists,
        old_password_from_user,
        new_password,
        m_p_main_window
    );
    if (!ok) {
        return false;  // user cancelled
    }
    if (old_password_exists
        && !cryptofunc::matchesHash(
            old_password_from_user, old_password_hash
        )) {
        uifunc::alert(tr("Incorrect old password"));
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

void CamcopsApp::setHashedPassword(
    const QString& hashed_password_varname, const QString& password
)
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
    setVar(
        varconst::SERVER_USERPASSWORD_OBSCURED,
        cryptofunc::encryptToBase64(password, key_b64, iv_b64)
    );
}

void CamcopsApp::resetEncryptionKeyIfRequired()
{
    qDebug() << Q_FUNC_INFO;
    SecureQString key(varString(varconst::OBSCURING_KEY));
    if (cryptofunc::isValidAesKey(key)) {
        return;
    }
    qInfo(
    ) << "Resetting internal encryption key (and wiping stored password)";
    setVar(varconst::OBSCURING_KEY, cryptofunc::generateObscuringKeyBase64());
    setVar(varconst::OBSCURING_IV, "");
    // ... will be set by setEncryptedServerPassword
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
    const QString plaintext(
        cryptofunc::decryptFromBase64(encrypted_b64, key_b64, iv_b64)
    );
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
    // - https://doc.qt.io/qt-6.5/quuid.html#createUuid
    // - https://en.wikipedia.org/wiki/Universally_unique_identifier#Variants_and_versions
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

bool CamcopsApp::validateSslCertificates() const
{
    return varBool(varconst::VALIDATE_SSL_CERTIFICATES);
}

// ============================================================================
// Patient
// ============================================================================

bool CamcopsApp::isPatientSelected() const
{
    return m_patient != nullptr;
}

void CamcopsApp::setSelectedPatient(
    const int patient_id, const bool force_refresh
)
{
    // We do this by ID so there's no confusion about who owns it; we own
    // our own private copy here.
    const bool changed = patient_id != selectedPatientId();
    if (changed || force_refresh) {
        reloadPatient(patient_id);
#ifdef DEBUG_EMIT
        qDebug() << Q_FUNC_INFO
                 << "emitting selectedPatientChanged "
                    "for patient_id"
                 << patient_id;
#endif
        emit selectedPatientChanged(m_patient.data());
    }
}

void CamcopsApp::deselectPatient(const bool force_refresh)
{
    setSelectedPatient(dbconst::NONEXISTENT_PK, force_refresh);
}

void CamcopsApp::setDefaultPatient(const bool force_refresh)
{
    int patient_id = dbconst::NONEXISTENT_PK;

    if (isSingleUserMode()) {
        patient_id = getSinglePatientId();
    }

    setSelectedPatient(patient_id, force_refresh);
}

void CamcopsApp::forceRefreshPatientList()
{
    emit refreshPatientList();
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
        qDebug() << Q_FUNC_INFO
                 << "Emitting selectedPatientDetailsChanged "
                    "for patient ID"
                 << patient_id;
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
    const QueryResult result = queryAllPatients();
    PatientPtrList patients;
    const int nrows = result.nRows();
    for (int row = 0; row < nrows; ++row) {
        PatientPtr p(new Patient(*this, *m_datadb, dbconst::NONEXISTENT_PK));
        p->setFromQuery(result, row, true);
        patients.append(p);
    }
    if (sorted) {
        std::sort(patients.begin(), patients.end(), PatientSorter());
    }
    return patients;
}

QueryResult CamcopsApp::queryAllPatients()
{
    Patient specimen(*this, *m_datadb, dbconst::NONEXISTENT_PK);
    // ... this is why function can't be const
    const WhereConditions where;  // but we don't specify any
    const SqlArgs sqlargs = specimen.fetchQuerySql(where);

    return m_datadb->query(sqlargs);
}

int CamcopsApp::nPatients() const
{
    return m_datadb->count(Patient::TABLENAME);
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
    const int p6_slider_groove_size_px = uiconst::g_slider_handle_size_px / 2;
    const int p7_slider_handle_size_px = uiconst::g_slider_handle_size_px;
    const int p8_slider_groove_margin_px = uiconst::SLIDER_GROOVE_MARGIN_PX;

#ifdef DEBUG_CSS_SIZES
    qDebug().nospace(
    ) << "CSS substituted sizes (for filename="
      << filename << ", DPI=" << m_dpi << "): "
      << "p1_normal_font_size_pt = " << p1_normal_font_size_pt
      << ", p2_big_font_size_pt = " << p2_big_font_size_pt
      << ", p3_heading_font_size_pt = " << p3_heading_font_size_pt
      << ", p4_title_font_size_pt = " << p4_title_font_size_pt
      << ", p5_menu_font_size_pt = " << p5_menu_font_size_pt
      << ", p6_slider_groove_size_px = " << p6_slider_groove_size_px
      << ", p7_slider_handle_size_px = " << p7_slider_handle_size_px
      << ", p8_slider_groove_margin_px = " << p8_slider_groove_margin_px;
#endif

    return filefunc::textfileContents(filename).arg(
        QString::number(p1_normal_font_size_pt),  // %1
        QString::number(p2_big_font_size_pt),  // %2
        QString::number(p3_heading_font_size_pt),  // %3
        QString::number(p4_title_font_size_pt),  // %4
        QString::number(p5_menu_font_size_pt),  // %5
        QString::number(p6_slider_groove_size_px),  // %6: groove width
        QString::number(p7_slider_handle_size_px),  // %7: handle
        QString::number(p8_slider_groove_margin_px)
    );  // %8: groove margin
    // QString::arg takes up to 9 strings.
    // After that, you can always add more arg() calls.
}

int CamcopsApp::fontSizePt(
    uiconst::FontSize fontsize, const double factor_pct
) const
{
    double factor;
    if (factor_pct <= 0) {
        factor = var(varconst::QUESTIONNAIRE_SIZE_PERCENT).toDouble() / 100;
    } else {
        // Custom percentage passed in; use that
        factor = double(factor_pct) / 100;
    }

    switch (fontsize) {
        case uiconst::FontSize::VerySmall:
            return static_cast<int>(factor * 8);
        case uiconst::FontSize::Small:
            return static_cast<int>(factor * 10);
        case uiconst::FontSize::Normal:
            return static_cast<int>(factor * 12);
        case uiconst::FontSize::Big:
            return static_cast<int>(factor * 14);
        case uiconst::FontSize::Heading:
            return static_cast<int>(factor * 16);
        case uiconst::FontSize::Title:
            return static_cast<int>(factor * 16);
        case uiconst::FontSize::Normal_x2:
            return static_cast<int>(factor * 24);
        case uiconst::FontSize::Menus:
#ifdef COMPILER_WANTS_DEFAULT_IN_EXHAUSTIVE_SWITCH
        default:
#endif
            return static_cast<int>(factor * 12);
    }
}

// ============================================================================
// Server info
// ============================================================================

Version CamcopsApp::serverVersion() const
{
    return {varString(varconst::SERVER_CAMCOPS_VERSION)};
}

IdPolicy CamcopsApp::uploadPolicy() const
{
    return IdPolicy(varString(varconst::ID_POLICY_UPLOAD));
}

IdPolicy CamcopsApp::finalizePolicy() const
{
    return IdPolicy(varString(varconst::ID_POLICY_FINALIZE));
}

IdNumDescriptionConstPtr CamcopsApp::getIdInfo(const int which_idnum)
{
    if (!m_iddescription_cache.contains(which_idnum)) {
        m_iddescription_cache[which_idnum] = IdNumDescriptionPtr(
            new IdNumDescription(*this, *m_sysdb, which_idnum)
        );
    }
    return m_iddescription_cache[which_idnum];
}

QString CamcopsApp::idDescription(const int which_idnum)
{
    IdNumDescriptionConstPtr idinfo = getIdInfo(which_idnum);
    return idinfo->description();
}

QString CamcopsApp::idShortDescription(const int which_idnum)
{
    IdNumDescriptionConstPtr idinfo = getIdInfo(which_idnum);
    return idinfo->shortDescription();
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

bool CamcopsApp::setIdDescription(
    const int which_idnum,
    const QString& desc,
    const QString& shortdesc,
    const QString& validation_method
)
{
    //    qDebug().nospace()
    //            << "Setting ID descriptions for which_idnum==" << which_idnum
    //            << " to " << desc << ", " << shortdesc;
    IdNumDescription idnumdesc(*this, *m_sysdb, which_idnum);
    const bool success
        = idnumdesc.setDescriptions(desc, shortdesc, validation_method);
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
    ancillaryfunc::loadAllRecords<IdNumDescription, IdNumDescriptionPtr>(
        descriptions, *this, *m_sysdb, order_by
    );
    return descriptions;
}

QVector<int> CamcopsApp::whichIdNumsAvailable()
{
    QVector<int> which_available;
    for (const IdNumDescriptionPtr& iddesc : getAllIdDescriptions()) {
        which_available.append(iddesc->whichIdNum());
    }
    return which_available;
}

// ============================================================================
// Extra strings (downloaded from server)
// ============================================================================

QString CamcopsApp::xstringDirect(
    const QString& taskname,
    const QString& stringname,
    const QString& default_str
)
{
    const QString language = getLanguage();
    // qDebug().nospace().noquote()
    //         << "xStringDirect: fetching " << taskname
    //         << "." << stringname << "[" << language << "]";
    ExtraString extrastring(*this, *m_sysdb, taskname, stringname, language);
    const bool found = extrastring.existsInDb();
    if (found) {
        QString result = extrastring.value();
        stringfunc::toHtmlLinebreaks(result);
        return result;
    }
    if (default_str.isEmpty()) {
        return QString("[string not downloaded: %1/%2]")
            .arg(taskname, stringname);
    }
    return default_str;
}

QString CamcopsApp::xstring(
    const QString& taskname,
    const QString& stringname,
    const QString& default_str
)
{
    const QPair<QString, QString> key(taskname, stringname);
    if (!m_extrastring_cache.contains(key)) {
        m_extrastring_cache[key]
            = xstringDirect(taskname, stringname, default_str);
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
    // Note that this function, updated in May 2019 to support multiple
    // languages, is perfectly happy if the language field is absent, since our
    // record representation is a fieldname-value dictionary.
    DbNestableTransaction trans(*m_sysdb);
    deleteAllExtraStrings();
    for (auto record : recordlist) {
        if (!record.contains(ExtraString::TASK_FIELD)
            || !record.contains(ExtraString::NAME_FIELD)
            || !record.contains(ExtraString::VALUE_FIELD)) {
            qWarning() << Q_FUNC_INFO << "Failing: recordlist has bad format";
            // The language field is optional (arriving with server 2.3.3)
            trans.fail();
            return;
        }
        const QString task = record[ExtraString::TASK_FIELD].toString();
        const QString name = record[ExtraString::NAME_FIELD].toString();
        const QString language
            = record[ExtraString::LANGUAGE_FIELD].toString();
        const QString value = record[ExtraString::VALUE_FIELD].toString();
        if (task.isEmpty() || name.isEmpty()) {
            qWarning() << Q_FUNC_INFO
                       << "Failing: extra string has blank task or name";
            trans.fail();
            return;
        }
        ExtraString extrastring(*this, *m_sysdb, task, name, language, value);
        // ... special constructor that doesn't attempt to load
        extrastring.saveWithoutKeepingPk();
    }
    // Took e.g. a shade under 10 s to save whilst keeping PK, down to ~1s
    // using a save-blindly-in-background method like this.
}

QString CamcopsApp::appstring(
    const QString& stringname, const QString& default_str
)
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
        if (!record.contains(AllowedServerTable::TABLENAME_FIELD)
            || !record.contains(AllowedServerTable::VERSION_FIELD)) {
            qWarning() << Q_FUNC_INFO << "Failing: recordlist has bad format";
            trans.fail();
            return;
        }
        const QString tablename
            = record[AllowedServerTable::TABLENAME_FIELD].toString();
        const Version min_client_version = Version::fromString(
            record[AllowedServerTable::VERSION_FIELD].toString()
        );
        if (tablename.isEmpty()) {
            qWarning() << Q_FUNC_INFO
                       << "Failing: allowed table has blank tablename";
            trans.fail();
            return;
        }
        AllowedServerTable allowedtable(
            *this, *m_sysdb, tablename, min_client_version
        );
        // ... special constructor that doesn't attempt to load
        allowedtable.saveWithoutKeepingPk();
    }
}

bool CamcopsApp::mayUploadTable(
    const QString& tablename,
    const Version& server_version,
    bool& server_has_table,
    Version& min_client_version,
    Version& min_server_version
)
{
    // We always write all three return-by-reference values.
    min_server_version = minServerVersionForTable(tablename);
    AllowedServerTable allowedtable(*this, *m_sysdb, tablename);
    server_has_table = allowedtable.existsInDb();
    if (!server_has_table) {
        min_client_version = Version::makeInvalidVersion();
        return false;
    }
    min_client_version = allowedtable.minClientVersion();
    return camcopsversion::CAMCOPS_CLIENT_VERSION >= min_client_version
        && server_version >= min_server_version;
}

QStringList CamcopsApp::nonTaskTables() const
{
    // See also CamcopsApp::makeOtherSystemTables()
    return QStringList{
        Blob::TABLENAME,
        Patient::TABLENAME,
        PatientIdNum::PATIENT_IDNUM_TABLENAME};
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

void CamcopsApp::createVar(
    const QString& name, QMetaType type, const QVariant& default_value
)
{
    if (name.isEmpty()) {
        uifunc::stopApp("Empty name to createVar");
    }
    if (m_storedvars.contains(name)) {  // Already exists
        return;
    }
    m_storedvars[name] = StoredVarPtr(
        new StoredVar(*this, *m_sysdb, name, type, default_value)
    );
}

bool CamcopsApp::setVar(
    const QString& name, const QVariant& value, const bool save_to_db
)
{
    // returns: changed?
    if (!m_storedvars.contains(name)) {
        uifunc::stopApp(QString("CamcopsApp::setVar: Attempt to set "
                                "nonexistent storedvar: %1")
                            .arg(name));
    }
    return m_storedvars[name]->setValue(value, save_to_db);
}

QVariant CamcopsApp::var(const QString& name) const
{
    if (!m_storedvars.contains(name)) {
        uifunc::stopApp(QString("CamcopsApp::var: Attempt to get nonexistent "
                                "storedvar: %1")
                            .arg(name));
    }
    return m_storedvars[name]->value();
}

QString CamcopsApp::varString(const QString& name) const
{
    return var(name).toString();
}

bool CamcopsApp::varBool(const QString& name) const
{
    return var(name).toBool();
}

int CamcopsApp::varInt(const QString& name) const
{
    return var(name).toInt();
}

qint64 CamcopsApp::varLongLong(const QString& name) const
{
    return var(name).toLongLong();
}

double CamcopsApp::varDouble(const QString& name) const
{
    return var(name).toDouble();
}

bool CamcopsApp::hasVar(const QString& name) const
{
    return m_storedvars.contains(name);
}

FieldRefPtr CamcopsApp::storedVarFieldRef(
    const QString& name, const bool mandatory, const bool cached
)
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
        (void)setVar(varname, value);  // ignores return value (changed)
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
    const QVariant agreed_at_var = var(varconst::AGREED_TERMS_AT);
    if (agreed_at_var.isNull()) {
        // Has not agreed yet.
        return false;
    }
    const QDate agreed_at_date = agreed_at_var.toDate();
    if (agreed_at_date < TextConst::TERMS_CONDITIONS_UPDATE_DATE) {
        // Terms have changed since the user last agreed.
        // They need to agree to the new terms.
        return false;
        // (There is an edge case here where the terms change on the same
        // day, but the cost/benefit balance for worrying about the hour of the
        // change seems not to be worth while!)
    }
    return true;
}

QDateTime CamcopsApp::agreedTermsAt() const
{
    return var(varconst::AGREED_TERMS_AT).toDateTime();
}

QString CamcopsApp::getCurrentTermsConditions()
{
    return getTermsConditionsForMode(getMode());
}

QString CamcopsApp::getTermsConditionsForMode(const int mode)
{
    if (mode == varconst::MODE_SINGLE_USER) {
        return TextConst::singleUserTermsConditions();
    }

    return TextConst::clinicianTermsConditions();
}

bool CamcopsApp::agreeTerms(const int new_mode)
{
    ScrollMessageBox msgbox(
        QMessageBox::Question,
        tr("Terms and conditions of use"),
        getTermsConditionsForMode(new_mode),
        m_p_main_window
    );
    // Keep agree/disagree message short, for phones:
    QAbstractButton* yes
        = msgbox.addButton(tr("I AGREE"), QMessageBox::YesRole);
    msgbox.addButton(tr("I DO NOT AGREE"), QMessageBox::NoRole);
    // It's hard work to remove the Close button from the dialog, but that is
    // interpreted as rejection, so that's OK.
    // - http://www.qtcentre.org/threads/41269-disable-close-button-in-QMessageBox

    msgbox.exec();
    if (msgbox.clickedButton() == yes) {
        // Agreed terms
        setVar(varconst::AGREED_TERMS_AT, QDateTime::currentDateTime());

        return true;
    } else {
        return false;
    }
}

// ============================================================================
// Uploading
// ============================================================================

void CamcopsApp::upload()
{
    if (m_lockstate == CamcopsApp::LockState::Locked) {
        uifunc::alertNotWhenLocked();
        return;
    }

    const auto method = getUploadMethod();
    if (method == NetworkManager::UploadMethod::Invalid) {
        return;
    }

    const bool logging_network = isLoggingNetwork();
    reconnectNetManager(
        logging_network ? nullptr : &CamcopsApp::uploadFailed,
        logging_network ? nullptr : &CamcopsApp::uploadFinished
    );
    // ... no failure handlers required when displaying the network log --
    // the NetworkManager will not be in silent mode, so will report the error
    // to the user directly. (And similarly, we didn't/don't need a "finished"
    // callback in with the logbox enabled.)

    showNetworkGuiGuard(tr("Uploading..."));
    networkManager()->upload(method);
}

NetworkManager::UploadMethod CamcopsApp::getUploadMethod()
{
    if (isSingleUserMode()) {
        return getSingleUserUploadMethod();
    }

    // Clinician mode
    return getUploadMethodFromUser();
}

NetworkManager::UploadMethod CamcopsApp::getSingleUserUploadMethod()
{
    if (tasksInProgress()) {
        return NetworkManager::UploadMethod::Copy;
    }

    return NetworkManager::UploadMethod::MoveKeepingPatients;
}

bool CamcopsApp::tasksInProgress()
{
    const TaskSchedulePtrList schedules = getTaskSchedules();

    for (const TaskSchedulePtr& schedule : schedules) {
        if (schedule->hasIncompleteCurrentTasks()) {
            return true;
        }
    }

    return false;
}

NetworkManager::UploadMethod CamcopsApp::getUploadMethodFromUser() const
{
    QString text(
        tr("Copy data to server, or move it to server?\n"
           "\n"
           "COPY: copies unfinished patients, moves finished patients.\n"
           "MOVE: moves all patients and their data.\n"
           "KEEP PATIENTS AND MOVE: moves all task data, keeps only basic "
           "patient details (for adding more tasks later).\n"
           "\n"
           "Please MOVE whenever possible; this reduces the amount of "
           "patient-identifiable information stored on this device.")
    );
    ScrollMessageBox msgbox(
        QMessageBox::Question, tr("Upload to server"), text, m_p_main_window
    );
    QAbstractButton* copy
        = msgbox.addButton(TextConst::copy(), QMessageBox::YesRole);
    QAbstractButton* move_keep
        = msgbox.addButton(tr("Keep patients and move"), QMessageBox::NoRole);
    QAbstractButton* move
        = msgbox.addButton(tr("Move"), QMessageBox::AcceptRole);
    // ... e.g. OK
    msgbox.addButton(TextConst::cancel(), QMessageBox::RejectRole);
    // ... e.g. Cancel
    msgbox.exec();
    QAbstractButton* reply = msgbox.clickedButton();
    if (reply == copy) {
        return NetworkManager::UploadMethod::Copy;
    }
    if (reply == move_keep) {
        return NetworkManager::UploadMethod::MoveKeepingPatients;
    }
    if (reply == move) {
        return NetworkManager::UploadMethod::Move;
    }

    return NetworkManager::UploadMethod::Invalid;
}

// ============================================================================
// App strings, or derived, or related user functions
// ============================================================================

NameValueOptions CamcopsApp::nhsPersonMaritalStatusCodeOptions()
{
    return NameValueOptions{
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_S), "S"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_M), "M"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_D), "D"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_W), "W"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_P), "P"},
        {appstring(appstrings::NHS_PERSON_MARITAL_STATUS_CODE_N), "N"}};
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
        {appstring(appstrings::NHS_ETHNIC_CATEGORY_CODE_Z), "Z"}};
}
