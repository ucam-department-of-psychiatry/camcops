// #define DANGER_DEBUG_PASSWORD_DECRYPTION
#define DANGER_DEBUG_WIPE_PASSWORDS

#include "camcopsapp.h"
#include <QApplication>
#include <QDateTime>
#include <QDialog>
#include <QMainWindow>
#include <QPushButton>
#include <QSqlDatabase>
#include <QStackedWidget>
#include "common/uiconstants.h"
#include "common/varconst.h"
#include "crypto/cryptofunc.h"
#include "db/dbfunc.h"
#include "db/dbnestabletransaction.h"
#include "db/dbtransaction.h"
#include "dbobjects/blob.h"
#include "dbobjects/extrastring.h"
#include "dbobjects/patient.h"
#include "dbobjects/storedvar.h"
#include "lib/datetimefunc.h"
#include "lib/filefunc.h"
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
    m_patient_id(DbConst::NONEXISTENT_PK),
    m_netmgr(nullptr)
{
    // ------------------------------------------------------------------------
    // Announce startup
    // ------------------------------------------------------------------------
    QDateTime dt = DateTime::now();
    qInfo() << "CamCOPS starting at:"
            << qUtf8Printable(DateTime::datetimeToIsoMs(dt))
            << "=" << qUtf8Printable(DateTime::datetimeToIsoMsUtc(dt));

    // ------------------------------------------------------------------------
    // Create databases
    // ------------------------------------------------------------------------
    // We can't do things like opening the database until we have
    // created the app. So don't open the database in the initializer list!
    // Database lifetime:
    // http://stackoverflow.com/questions/7669987/what-is-the-correct-way-of-qsqldatabase-qsqlquery
    m_datadb = QSqlDatabase::addDatabase("QSQLITE", "data");
    m_sysdb = QSqlDatabase::addDatabase("QSQLITE", "sys");
    DbFunc::openDatabaseOrDie(m_datadb, DATA_DATABASE_FILENAME);
    DbFunc::openDatabaseOrDie(m_sysdb, SYSTEM_DATABASE_FILENAME);

    // ------------------------------------------------------------------------
    // Register tasks
    // ------------------------------------------------------------------------
    m_p_task_factory = TaskFactoryPtr(new TaskFactory(*this));
    InitTasks(*m_p_task_factory);  // ensures all tasks are registered
    m_p_task_factory->finishRegistration();
    qInfo() << "Registered tasks:" << m_p_task_factory->tablenames();

    // ------------------------------------------------------------------------
    // Make tables
    // ------------------------------------------------------------------------

    // Make special tables: system database
    StoredVar storedvar_specimen(m_sysdb);
    storedvar_specimen.makeTable();
    ExtraString extrastring_specimen(m_sysdb);
    extrastring_specimen.makeTable();

    // Make special tables: main database
    Blob blob_specimen(m_datadb);
    blob_specimen.makeTable();
    Patient patient_specimen(m_datadb);
    patient_specimen.makeTable();

    // Make task tables
    m_p_task_factory->makeAllTables();

    // ------------------------------------------------------------------------
    // Create stored variables: name, type, default
    // ------------------------------------------------------------------------
    {
        DbTransaction trans(m_sysdb);  // https://www.sqlite.org/faq.html#q19

        // Questionnaire
        createVar(VarConst::QUESTIONNAIRE_SIZE_PERCENT, QVariant::Int, 100);

        // Server
        createVar(VarConst::SERVER_ADDRESS, QVariant::String);
        createVar(VarConst::SERVER_PORT, QVariant::Int, 443);  // 443 = HTTPS
        createVar(VarConst::SERVER_PATH, QVariant::String, "camcops/database");
        createVar(VarConst::SERVER_TIMEOUT_MS, QVariant::Int, 50000);
        createVar(VarConst::VALIDATE_SSL_CERTIFICATES, QVariant::Bool, true);
        createVar(VarConst::STORE_SERVER_PASSWORD, QVariant::Bool, true);
        createVar(VarConst::SEND_ANALYTICS, QVariant::Bool, true);

        // Whisker
        createVar(VarConst::WHISKER_HOST, QVariant::String, "localhost");
        createVar(VarConst::WHISKER_PORT, QVariant::Int, 3233);  // 3233 = Whisker
        createVar(VarConst::WHISKER_TIMEOUT_MS, QVariant::Int, 5000);

        // Intellectual property
        createVar(VarConst::IP_USE_CLINICAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
        createVar(VarConst::IP_USE_COMMERCIAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
        createVar(VarConst::IP_USE_EDUCATIONAL, QVariant::Int, CommonOptions::UNKNOWN_INT);
        createVar(VarConst::IP_USE_RESEARCH, QVariant::Int, CommonOptions::UNKNOWN_INT);

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

#ifdef DANGER_DEBUG_WIPE_PASSWORDS
        setHashedPassword(VarConst::USER_PASSWORD_HASH, "");
        setHashedPassword(VarConst::PRIV_PASSWORD_HASH, "");
#endif
    }

    // ------------------------------------------------------------------------
    // Qt stuff
    // ------------------------------------------------------------------------
    setStyleSheet(getSubstitutedCss(UiConst::CSS_CAMCOPS_MAIN));
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
                new NetworkManager(*this, m_p_main_window.data()));

    MainMenu* menu = new MainMenu(*this);
    open(menu);

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


TaskFactoryPtr CamcopsApp::factory()
{
    return m_p_task_factory;
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
                      bool may_alter_task)
{
    if (!widget) {
        qCritical() << Q_FUNC_INFO << "- attempt to open nullptr";
        return;
    }

    SlowGuiGuard guard = getSlowGuiGuard();

    Qt::WindowStates prev_window_state = m_p_main_window->windowState();
    QPointer<OpenableWidget> guarded_widget = widget;

    widget->build();
    qDebug() << Q_FUNC_INFO << "Pushing screen";
    int index = m_p_window_stack->addWidget(widget);  // will show the widget
    // The stack takes over ownership.
    m_p_window_stack->setCurrentIndex(index);
    if (widget->wantsFullscreen()) {
        m_p_main_window->showFullScreen();
    }

    // 3. Signals
    connect(widget, &OpenableWidget::finished,
            this, &CamcopsApp::close);

    m_info_stack.push(OpenableInfo(guarded_widget, task, prev_window_state,
                                   may_alter_task));
    // This stores a QSharedPointer to the task (if supplied), so keeping that
    // keeps the task "alive" whilst its widget is doing things.
}


void CamcopsApp::close()
{
    if (m_info_stack.isEmpty()) {
        UiFunc::stopApp("CamcopsApp::close: No more windows; closing");
    }
    OpenableInfo info = m_info_stack.pop();
    // on function exit, will delete the task if it's the last pointer to it

    QWidget* top = m_p_window_stack->currentWidget();
    qDebug() << Q_FUNC_INFO << "Popping screen";
    m_p_window_stack->removeWidget(top);
    // Ownership is returned to the application, so...
    top->deleteLater();  // later, in case it was this object that called us

    m_p_main_window->setWindowState(info.prev_window_state);

    if (info.may_alter_task) {
        emit taskAlterationFinished(info.task);
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
    QString hashed_password = var(hashed_password_varname).toString();
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
    QString old_password_hash = var(hashed_password_varname).toString();
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
    return var(VarConst::STORE_SERVER_PASSWORD).toBool();
}


void CamcopsApp::setEncryptedServerPassword(const QString& password)
{
    qDebug() << Q_FUNC_INFO;
    DbNestableTransaction trans(m_sysdb);
    resetEncryptionKeyIfRequired();
    QString iv_b64(CryptoFunc::generateIVBase64());  // new one each time
    setVar(VarConst::OBSCURING_IV, iv_b64);
    SecureQString key_b64(var(VarConst::OBSCURING_KEY).toString());
    setVar(VarConst::SERVER_USERPASSWORD_OBSCURED,
           CryptoFunc::encryptToBase64(password, key_b64, iv_b64));
}


void CamcopsApp::resetEncryptionKeyIfRequired()
{
    qDebug() << Q_FUNC_INFO;
    SecureQString key(var(VarConst::OBSCURING_KEY).toString());
    if (!CryptoFunc::isValidAesKey(key)) {
        return;
    }
    qInfo() << "Resetting internal encryption key (and wiping stored password)";
    setVar(VarConst::OBSCURING_KEY, CryptoFunc::generateObscuringKeyBase64());
    setVar(VarConst::OBSCURING_IV, "");
    setVar(VarConst::SERVER_USERPASSWORD_OBSCURED, "");
}


SecureQString CamcopsApp::getPlaintextServerPassword() const
{
    QString encrypted_b64(var(VarConst::SERVER_USERPASSWORD_OBSCURED).toString());
    if (encrypted_b64.isEmpty()) {
        return "";
    }
    SecureQString key_b64(var(VarConst::OBSCURING_KEY).toString());
    QString iv_b64(var(VarConst::OBSCURING_IV).toString());
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


// ============================================================================
// Network
// ============================================================================

NetworkManager* CamcopsApp::networkManager() const
{
    return m_netmgr.data();
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
        emit whiskerConnectionStateChanged(connected);
    }
}


// ============================================================================
// Patient
// ============================================================================

bool CamcopsApp::patientSelected() const
{
    return m_patient_id != DbConst::NONEXISTENT_PK;
}


QString CamcopsApp::patientDetails() const
{
    return "*** patient details ***";
}


void CamcopsApp::setSelectedPatient(int patient_id)
{
    bool changed = patient_id != m_patient_id;
    m_patient_id = patient_id;
    if (changed) {
        // *** emit something? check what calls this
    }
}


int CamcopsApp::currentPatientId() const
{
    return m_patient_id;
}


// ============================================================================
// CSS convenience; fonts etc.
// ============================================================================

QString CamcopsApp::getSubstitutedCss(const QString& filename) const
{
    return (
        FileFunc::textfileContents(filename)
            .arg(fontSizePt(UiConst::FontSize::Normal))  // %1
            .arg(fontSizePt(UiConst::FontSize::Big))  // %2
            .arg(fontSizePt(UiConst::FontSize::Heading))  // %3
            .arg(fontSizePt(UiConst::FontSize::Title))  // %4
            .arg(fontSizePt(UiConst::FontSize::Menus))  // %5
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

QString CamcopsApp::xstring(const QString& taskname, const QString& stringname,
                            const QString& default_str) const
{
    ExtraString extrastring(m_sysdb, taskname, stringname);
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


bool CamcopsApp::hasExtraStrings(const QString& taskname) const
{
    ExtraString extrastring_specimen(m_sysdb);
    return extrastring_specimen.anyExist(taskname);
}


void CamcopsApp::deleteAllExtraStrings()
{
    ExtraString extrastring_specimen(m_sysdb);
    extrastring_specimen.deleteAllExtraStrings();
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
        new StoredVar(m_sysdb, name, type, default_value));
}


bool CamcopsApp::setVar(const QString& name, const QVariant& value,
                        bool save_to_db)
{
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
