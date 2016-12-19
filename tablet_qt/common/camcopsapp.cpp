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

// #define DANGER_DEBUG_PASSWORD_DECRYPTION
#define DANGER_DEBUG_WIPE_PASSWORDS
#define DEBUG_EMIT

#include "camcopsapp.h"
#include <QApplication>
#include <QDateTime>
#include <QIcon>
#include <QMainWindow>
#include <QMessageBox>
#include <QSqlDatabase>
#include <QStackedWidget>
#include <QUuid>
#include "common/camcopsversion.h"
#include "common/dbconstants.h"  // for NONEXISTENT_PK
#include "common/uiconstants.h"
#include "common/varconst.h"
#include "common/version.h"
#include "crypto/cryptofunc.h"
#include "db/dbfunc.h"
#include "db/dbnestabletransaction.h"
#include "db/dbtransaction.h"
#include "db/dumpsql.h"
#include "dbobjects/blob.h"
#include "dbobjects/extrastring.h"
#include "dbobjects/patient.h"
#include "dbobjects/patientsorter.h"
#include "dbobjects/storedvar.h"
#include "lib/datetimefunc.h"
#include "lib/filefunc.h"
#include "lib/idpolicy.h"
#include "lib/networkmanager.h"
#include "lib/slowguiguard.h"
#include "lib/uifunc.h"
#include "menu/mainmenu.h"
#include "tasklib/inittasks.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"


CamcopsApp::CamcopsApp(int& argc, char *argv[]) :
    QApplication(argc, argv),
    m_p_task_factory(nullptr),
    m_lockstate(LockState::Locked),
    m_whisker_connected(false),
    m_p_main_window(nullptr),
    m_p_window_stack(nullptr),
    m_patient(nullptr),
    m_netmgr(nullptr)
{
    // ------------------------------------------------------------------------
    // Announce startup
    // ------------------------------------------------------------------------
    QDateTime dt = DateTime::now();
    qInfo() << "CamCOPS starting at:"
            << qUtf8Printable(DateTime::datetimeToIsoMs(dt))
            << "=" << qUtf8Printable(DateTime::datetimeToIsoMsUtc(dt));
    qInfo() << "CamCOPS version:" << CamcopsVersion::CAMCOPS_VERSION;

    // ------------------------------------------------------------------------
    // Create databases
    // ------------------------------------------------------------------------
    // We can't do things like opening the database until we have
    // created the app. So don't open the database in the initializer list!
    // Database lifetime:
    // http://stackoverflow.com/questions/7669987/what-is-the-correct-way-of-qsqldatabase-qsqlquery
    m_datadb = QSqlDatabase::addDatabase("QSQLITE", "data");
    m_sysdb = QSqlDatabase::addDatabase("QSQLITE", "sys");
    DbFunc::openDatabaseOrDie(m_datadb, DbFunc::DATA_DATABASE_FILENAME);
    DbFunc::openDatabaseOrDie(m_sysdb, DbFunc::SYSTEM_DATABASE_FILENAME);

    // ------------------------------------------------------------------------
    // Register tasks
    // ------------------------------------------------------------------------
    m_p_task_factory = TaskFactoryPtr(new TaskFactory(*this));
    InitTasks(*m_p_task_factory);  // ensures all tasks are registered
    m_p_task_factory->finishRegistration();
    qInfo() << "Registered tasks:" << m_p_task_factory->tablenames();

    // ------------------------------------------------------------------------
    // Make storedvar table
    // ------------------------------------------------------------------------

    StoredVar storedvar_specimen(*this, m_sysdb);
    storedvar_specimen.makeTable();

    // ------------------------------------------------------------------------
    // Seed Qt's build-in RNG, which we may use for QUuid generation
    // ------------------------------------------------------------------------
    // QUuid may, if /dev/urandom does not exist, use qrand(). It won't use
    // OpenSSL or anything else. So we'd better make sure it's seeded first:
    qsrand(QDateTime::currentMSecsSinceEpoch() & 0xffffffff);
    // QDateTime::currentMSecsSinceEpoch() -> qint64
    // qsrand wants uint (= uint32)

    // ------------------------------------------------------------------------
    // Create stored variables: name, type, default
    // ------------------------------------------------------------------------
    {
        DbTransaction trans(m_sysdb);  // https://www.sqlite.org/faq.html#q19

        // Version
        createVar(VarConst::CAMCOPS_VERSION_AS_STRING, QVariant::String,
                  CamcopsVersion::CAMCOPS_VERSION.toString());

        // Questionnaire
        createVar(VarConst::QUESTIONNAIRE_SIZE_PERCENT, QVariant::Int, 100);

        // Server
        createVar(VarConst::SERVER_ADDRESS, QVariant::String, "");
        createVar(VarConst::SERVER_PORT, QVariant::Int, 443);  // 443 = HTTPS
        createVar(VarConst::SERVER_PATH, QVariant::String, "camcops/database");
        createVar(VarConst::SERVER_TIMEOUT_MS, QVariant::Int, 50000);
        createVar(VarConst::VALIDATE_SSL_CERTIFICATES, QVariant::Bool, true);
        createVar(VarConst::STORE_SERVER_PASSWORD, QVariant::Bool, true);
        createVar(VarConst::SEND_ANALYTICS, QVariant::Bool, true);

        // Uploading "dirty" flag
        createVar(VarConst::NEEDS_UPLOAD, QVariant::Bool, false);

        // Whisker
        createVar(VarConst::WHISKER_HOST, QVariant::String, "localhost");
        createVar(VarConst::WHISKER_PORT, QVariant::Int, 3233);  // 3233 = Whisker
        createVar(VarConst::WHISKER_TIMEOUT_MS, QVariant::Int, 5000);

        // Terms and conditions
        createVar(VarConst::AGREED_TERMS_AT, QVariant::DateTime);

        // Intellectual property
        createVar(VarConst::IP_USE_CLINICAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
        createVar(VarConst::IP_USE_COMMERCIAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
        createVar(VarConst::IP_USE_EDUCATIONAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
        createVar(VarConst::IP_USE_RESEARCH, QVariant::Int, CommonOptions::UNKNOWN_INT);

        // Patients and policies
        createVar(VarConst::ID_POLICY_UPLOAD, QVariant::String, "");
        createVar(VarConst::ID_POLICY_FINALIZE, QVariant::String, "");

        // Patient-related device-wide settings
        for (int n = 1; n <= DbConst::NUMBER_OF_IDNUMS; ++n) {
            QString desc = DbConst::IDDESC_FIELD_FORMAT.arg(n);
            QString shortdesc = DbConst::IDSHORTDESC_FIELD_FORMAT.arg(n);
            createVar(desc, QVariant::String);
            createVar(shortdesc, QVariant::String);
        }

        // Other information from server
        createVar(VarConst::SERVER_DATABASE_TITLE, QVariant::String, "");
        createVar(VarConst::SERVER_CAMCOPS_VERSION, QVariant::String, "");
        createVar(VarConst::LAST_SERVER_REGISTRATION, QVariant::DateTime);
        createVar(VarConst::LAST_SUCCESSFUL_UPLOAD, QVariant::DateTime);

        // User
        // ... server interaction
        createVar(VarConst::DEVICE_FRIENDLY_NAME, QVariant::String, "");
        createVar(VarConst::SERVER_USERNAME, QVariant::String, "");
        createVar(VarConst::SERVER_USERPASSWORD_OBSCURED, QVariant::String, "");
        createVar(VarConst::OFFER_UPLOAD_AFTER_EDIT, QVariant::Bool, false);
        // ... default clinician details
        createVar(VarConst::DEFAULT_CLINICIAN_SPECIALTY, QVariant::String, "");
        createVar(VarConst::DEFAULT_CLINICIAN_NAME, QVariant::String, "");
        createVar(VarConst::DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION, QVariant::String, "");
        createVar(VarConst::DEFAULT_CLINICIAN_POST, QVariant::String, "");
        createVar(VarConst::DEFAULT_CLINICIAN_SERVICE, QVariant::String, "");
        createVar(VarConst::DEFAULT_CLINICIAN_CONTACT_DETAILS, QVariant::String, "");

        // Cryptography
        createVar(VarConst::OBSCURING_KEY, QVariant::String, "");
        createVar(VarConst::OBSCURING_IV, QVariant::String, "");
        // setEncryptedServerPassword("hello I am a password");
        // qDebug() << getPlaintextServerPassword();
        createVar(VarConst::USER_PASSWORD_HASH, QVariant::String, "");
        createVar(VarConst::PRIV_PASSWORD_HASH, QVariant::String, "");

        // Device ID
        createVar(VarConst::DEVICE_ID, QVariant::Uuid);
        if (var(VarConst::DEVICE_ID).isNull()) {
            regenerateDeviceId();
        }

#ifdef DANGER_DEBUG_WIPE_PASSWORDS
        qDebug() << "DANGER: wiping passwords";
        setHashedPassword(VarConst::USER_PASSWORD_HASH, "");
        setHashedPassword(VarConst::PRIV_PASSWORD_HASH, "");
#endif
    }

    // ------------------------------------------------------------------------
    // Any database upgrade required?
    // ------------------------------------------------------------------------

    Version old_version = Version::fromString(
                varString(VarConst::CAMCOPS_VERSION_AS_STRING));
    Version new_version = CamcopsVersion::CAMCOPS_VERSION;
    upgradeDatabase(old_version, new_version);
    if (new_version != old_version) {
        setVar(VarConst::CAMCOPS_VERSION_AS_STRING, new_version.toString());
    }

    // ------------------------------------------------------------------------
    // Make other tables
    // ------------------------------------------------------------------------

    // Make special tables: system database
    ExtraString extrastring_specimen(*this, m_sysdb);
    extrastring_specimen.makeTable();

    // Make special tables: main database
    Blob blob_specimen(*this, m_datadb);
    blob_specimen.makeTable();
    Patient patient_specimen(*this, m_datadb);
    patient_specimen.makeTable();

    // Make task tables
    m_p_task_factory->makeAllTables();

    // ------------------------------------------------------------------------
    // Qt stuff
    // ------------------------------------------------------------------------
    setStyleSheet(getSubstitutedCss(UiConst::CSS_CAMCOPS_MAIN));

    // Special for top-level window:
    setWindowIcon(QIcon(UiFunc::iconFilename(UiConst::ICON_CAMCOPS)));
}


CamcopsApp::~CamcopsApp()
{
    // http://doc.qt.io/qt-5.7/objecttrees.html
    // Only delete things that haven't been assigned a parent
    delete m_p_main_window;
}


// ============================================================================
// Core
// ============================================================================

int CamcopsApp::run()
{
    qDebug() << "CamcopsApp::run()";

    m_p_main_window = new QMainWindow();
    m_p_main_window->showMaximized();
    m_p_window_stack = new QStackedWidget(m_p_main_window);
    m_p_main_window->setCentralWidget(m_p_window_stack);

    m_netmgr = QSharedPointer<NetworkManager>(
                new NetworkManager(*this, m_datadb, m_p_task_factory,
                                   m_p_main_window.data()));

    MainMenu* menu = new MainMenu(*this);
    open(menu);

    if (!hasAgreedTerms()) {
        offerTerms();
    }

    qInfo() << "Starting Qt event processor...";
    return exec();  // Main Qt event loop
}


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


void CamcopsApp::upgradeDatabase(const Version& old_version,
                                 const Version& new_version)
{
    if (old_version == new_version) {
        qInfo() << "Database is current; no special upgrade steps required";
        return;
    }
    qInfo() << "Considering special database upgrade steps from version"
            << old_version << "to version" << new_version;

    // Do things

    qInfo() << "Special database upgrade steps complete";
    return;
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
        m_p_main_window->showFullScreen();
    }

    // 3. Signals
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
        UiFunc::stopApp("CamcopsApp::close: No more windows; closing");
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

        if (varBool(VarConst::OFFER_UPLOAD_AFTER_EDIT) &&
                varBool(VarConst::NEEDS_UPLOAD)) {
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
            checkPassword(VarConst::USER_PASSWORD_HASH,
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
    if (checkPassword(VarConst::PRIV_PASSWORD_HASH,
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
    bool ok = UiFunc::getPassword(text, title, password, m_p_main_window);
    if (!ok) {
        return false;
    }
    bool correct = CryptoFunc::matchesHash(password, hashed_password);
    if (!correct) {
        UiFunc::alert(tr("Wrong password"), title);
    }
    return correct;
}


void CamcopsApp::changeAppPassword()
{
    changePassword(VarConst::USER_PASSWORD_HASH,
                   tr("Change privileged-mode password"));
}


void CamcopsApp::changePrivPassword()
{
    changePassword(VarConst::PRIV_PASSWORD_HASH,
                   tr("Change privileged-mode password"));
}


void CamcopsApp::changePassword(const QString& hashed_password_varname,
                                const QString& text)
{
    QString old_password_hash = varString(hashed_password_varname);
    bool old_password_exists = !old_password_hash.isEmpty();
    QString old_password_from_user;
    QString new_password;
    bool ok = UiFunc::getOldNewPasswords(text, text, old_password_exists,
                                         old_password_from_user, new_password,
                                         m_p_main_window);
    if (!ok) {
        return;  // user cancelled
    }
    if (old_password_exists && !CryptoFunc::matchesHash(old_password_from_user,
                                                        old_password_hash)) {
        UiFunc::alert("Incorrect old password");
        return;
    }
    setHashedPassword(hashed_password_varname, new_password);
}


void CamcopsApp::setHashedPassword(const QString& hashed_password_varname,
                                   const QString& password)
{
    if (password.isEmpty()) {
        qWarning() << "Erasing password:" << hashed_password_varname;
        setVar(hashed_password_varname, "");
    } else {
        setVar(hashed_password_varname, CryptoFunc::hash(password));
    }
}


bool CamcopsApp::storingServerPassword() const
{
    return varBool(VarConst::STORE_SERVER_PASSWORD);
}


void CamcopsApp::setEncryptedServerPassword(const QString& password)
{
    qDebug() << Q_FUNC_INFO;
    DbNestableTransaction trans(m_sysdb);
    resetEncryptionKeyIfRequired();
    QString iv_b64(CryptoFunc::generateIVBase64());  // new one each time
    setVar(VarConst::OBSCURING_IV, iv_b64);
    SecureQString key_b64(varString(VarConst::OBSCURING_KEY));
    setVar(VarConst::SERVER_USERPASSWORD_OBSCURED,
           CryptoFunc::encryptToBase64(password, key_b64, iv_b64));
}


void CamcopsApp::resetEncryptionKeyIfRequired()
{
    qDebug() << Q_FUNC_INFO;
    SecureQString key(varString(VarConst::OBSCURING_KEY));
    if (CryptoFunc::isValidAesKey(key)) {
        return;
    }
    qInfo() << "Resetting internal encryption key (and wiping stored password)";
    setVar(VarConst::OBSCURING_KEY, CryptoFunc::generateObscuringKeyBase64());
    setVar(VarConst::OBSCURING_IV, "");  // will be set by setEncryptedServerPassword
    setVar(VarConst::SERVER_USERPASSWORD_OBSCURED, "");
}


SecureQString CamcopsApp::getPlaintextServerPassword() const
{
    QString encrypted_b64(varString(VarConst::SERVER_USERPASSWORD_OBSCURED));
    if (encrypted_b64.isEmpty()) {
        return "";
    }
    SecureQString key_b64(varString(VarConst::OBSCURING_KEY));
    QString iv_b64(varString(VarConst::OBSCURING_IV));
    if (!CryptoFunc::isValidAesKey(key_b64)) {
        qWarning() << "Unable to decrypt password; key is bad";
        return "";
    }
    if (!CryptoFunc::isValidAesIV(iv_b64)) {
        qWarning() << "Unable to decrypt password; IV is bad";
        return "";
    }
    QString plaintext(CryptoFunc::decryptFromBase64(encrypted_b64, key_b64, iv_b64));
#ifdef DANGER_DEBUG_PASSWORD_DECRYPTION
    qDebug() << Q_FUNC_INFO << "plaintext:" << plaintext;
#endif
    return plaintext;
}


QString CamcopsApp::deviceId() const
{
    return varString(VarConst::DEVICE_ID);
}


void CamcopsApp::regenerateDeviceId()
{
    setVar(VarConst::DEVICE_ID, QUuid::createUuid());
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
    return varBool(VarConst::NEEDS_UPLOAD);
}


void CamcopsApp::setNeedsUpload(bool needs_upload)
{
    bool changed = setVar(VarConst::NEEDS_UPLOAD, needs_upload);
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
    setSelectedPatient(DbConst::NONEXISTENT_PK);
}


void CamcopsApp::reloadPatient(int patient_id)
{
    if (patient_id == DbConst::NONEXISTENT_PK) {
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
    return m_patient ? m_patient->id() : DbConst::NONEXISTENT_PK;
}


PatientPtrList CamcopsApp::getAllPatients(bool sorted)
{
    PatientPtrList patients;
    Patient specimen(*this, m_datadb, DbConst::NONEXISTENT_PK);  // this is why function can't be const
    WhereConditions where;  // but we don't specify any
    SqlArgs sqlargs = specimen.fetchQuerySql(where);
    QSqlQuery query(m_datadb);
    bool success = DbFunc::execQuery(query, sqlargs);
    if (success) {  // success check may be redundant (cf. while clause)
        while (query.next()) {
            PatientPtr p(new Patient(*this, m_datadb, DbConst::NONEXISTENT_PK));
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
    if (!DbConst::isValidWhichIdnum(which_idnum)) {
        return DbConst::BAD_IDNUM_DESC;
    }
    QString field = DbConst::IDDESC_FIELD_FORMAT.arg(which_idnum);
    QString desc_str = varString(field);
    if (desc_str.isEmpty()) {
        return DbConst::UNKNOWN_IDNUM_DESC.arg(which_idnum);
    }
    return desc_str;
}


QString CamcopsApp::idShortDescription(int which_idnum) const
{
    if (!DbConst::isValidWhichIdnum(which_idnum)) {
        return DbConst::BAD_IDNUM_DESC;
    }
    QString field = DbConst::IDSHORTDESC_FIELD_FORMAT.arg(which_idnum);
    QString desc_str = varString(field);
    if (desc_str.isEmpty()) {
        return DbConst::UNKNOWN_IDNUM_DESC.arg(which_idnum);
    }
    return desc_str;
}


IdPolicy CamcopsApp::uploadPolicy() const
{
    return IdPolicy(varString(VarConst::ID_POLICY_UPLOAD));
}


IdPolicy CamcopsApp::finalizePolicy() const
{
    return IdPolicy(varString(VarConst::ID_POLICY_FINALIZE));
}


// ============================================================================
// CSS convenience; fonts etc.
// ============================================================================

QString CamcopsApp::getSubstitutedCss(const QString& filename) const
{
    return (
        FileFunc::textfileContents(filename)
            .arg(fontSizePt(UiConst::FontSize::Normal))     // %1
            .arg(fontSizePt(UiConst::FontSize::Big))        // %2
            .arg(fontSizePt(UiConst::FontSize::Heading))    // %3
            .arg(fontSizePt(UiConst::FontSize::Title))      // %4
            .arg(fontSizePt(UiConst::FontSize::Menus))      // %5
    );
}


int CamcopsApp::fontSizePt(UiConst::FontSize fontsize,
                           double factor_pct) const
{
    double factor;
    if (factor_pct <= 0) {
        factor = var(VarConst::QUESTIONNAIRE_SIZE_PERCENT).toDouble() / 100;
    } else {
        // Custom percentage passed in; use that
        factor = double(factor_pct) / 100;
    }

    switch (fontsize) {
    case UiConst::FontSize::Normal:
        return factor * 12;
    case UiConst::FontSize::Big:
        return factor * 14;
    case UiConst::FontSize::Heading:
        return factor * 16;
    case UiConst::FontSize::Title:
        return factor * 20;
    case UiConst::FontSize::Menus:
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
        return extrastring.value();
    } else {
        if (default_str.isEmpty()) {
            return QString("[string not downloaded: %1/%2]")
                    .arg(taskname)
                    .arg(stringname);
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


// ============================================================================
// Stored variables: generic
// ============================================================================

void CamcopsApp::createVar(const QString &name, QVariant::Type type,
                                 const QVariant &default_value)
{
    if (name.isEmpty()) {
        UiFunc::stopApp("Empty name to createVar");
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
        UiFunc::stopApp(QString("CamcopsApp::setVar: Attempt to set "
                                "nonexistent storedvar: %1").arg(name));
    }
    return m_storedvars[name]->setValue(value, save_to_db);
}


QVariant CamcopsApp::var(const QString& name) const
{
    if (!m_storedvars.contains(name)) {
        UiFunc::stopApp(QString("CamcopsApp::var: Attempt to get nonexistent "
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
        setVar(varname, value);  // ignores return value (changed)
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
    return !var(VarConst::AGREED_TERMS_AT).isNull();
}


QDateTime CamcopsApp::agreedTermsAt() const
{
    return var(VarConst::AGREED_TERMS_AT).toDateTime();
}


void CamcopsApp::offerTerms()
{
    QMessageBox msgbox(QMessageBox::Question,  // icon
                       tr("View terms and conditions of use"),  // title
                       UiConst::TERMS_CONDITIONS,  // text
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
        setVar(VarConst::AGREED_TERMS_AT, QDateTime::currentDateTime());
    } else {
        // Refused terms
        UiFunc::stopApp(tr("OK. Goodbye."), tr("You refused the conditions."));
    }
}

// ============================================================================
// SQL dumping
// ============================================================================

void CamcopsApp::dumpDataDatabase(QTextStream& os)
{
    DumpSql::dumpDatabase(os, m_datadb);
}


void CamcopsApp::dumpSystemDatabase(QTextStream& os)
{
    DumpSql::dumpDatabase(os, m_sysdb);
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
