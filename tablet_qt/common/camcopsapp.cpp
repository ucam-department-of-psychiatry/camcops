#include "camcopsapp.h"
#include <QApplication>
#include <QDateTime>
#include <QDialog>
#include <QMainWindow>
#include <QPushButton>
#include <QSqlDatabase>
#include <QStackedWidget>
#include "common/uiconstants.h"
#include "dbobjects/blob.h"
#include "dbobjects/storedvar.h"
#include "lib/datetimefunc.h"
#include "lib/dbfunc.h"
#include "lib/filefunc.h"
#include "menu/mainmenu.h"
#include "tasklib/inittasks.h"
#include "questionnairelib/questionnaire.h"

const QString VAR_QUESTIONNAIRE_SIZE_PERCENT = "questionnaireTextSizePercent";


CamcopsApp::CamcopsApp(int& argc, char *argv[]) :
    QApplication(argc, argv),
    m_p_task_factory(nullptr),
    m_lockstate(LockState::Locked),
    m_whisker_connected(false),
    m_p_main_window(nullptr),
    m_p_window_stack(nullptr),
    m_patient_id(DbConst::NONEXISTENT_PK)
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
    m_db = QSqlDatabase::addDatabase("QSQLITE", "data");
    m_sysdb = QSqlDatabase::addDatabase("QSQLITE", "sys");
    DbFunc::openDatabaseOrDie(m_db, DATA_DATABASE_FILENAME);
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

    // Make special tables: main database
    Blob blob_specimen(m_db);
    blob_specimen.makeTable();
    // *** make patients table

    // Make task tables
    m_p_task_factory->makeAllTables();

    // ------------------------------------------------------------------------
    // Create stored variables
    // ------------------------------------------------------------------------
    createVar(VAR_QUESTIONNAIRE_SIZE_PERCENT, QVariant::Int, 100);

    // ------------------------------------------------------------------------
    // Qt stuff
    // ------------------------------------------------------------------------
    setStyleSheet(FileFunc::textfileContents(UiConst::CSS_CAMCOPS_MAIN));
}


CamcopsApp::~CamcopsApp()
{
    // http://doc.qt.io/qt-5.7/objecttrees.html
    // Only delete things that haven't been assigned a parent
    delete m_p_main_window;
}


int CamcopsApp::run()
{
    qDebug() << "CamcopsApp::run()";

    m_p_main_window = new QMainWindow();
    m_p_main_window->showMaximized();
    m_p_window_stack = new QStackedWidget(m_p_main_window);
    m_p_main_window->setCentralWidget(m_p_window_stack);

    MainMenu* menu = new MainMenu(*this);
    open(menu);

    qInfo() << "Starting Qt event processor...";
    return exec();  // Main Qt event loop
}


QSqlDatabase& CamcopsApp::db()
{
    return m_db;
}


QSqlDatabase& CamcopsApp::sysdb()
{
    return m_sysdb;
}


TaskFactoryPtr CamcopsApp::factory()
{
    return m_p_task_factory;
}


void CamcopsApp::open(OpenableWidget* widget, TaskPtr task,
                      bool may_alter_task)
{
    if (!widget) {
        qCritical() << Q_FUNC_INFO << "- attempt to open nullptr";
        return;
    }

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
    // *** security check
    setLockState(LockState::Unlocked);
}


void CamcopsApp::lock()
{
    setLockState(LockState::Locked);
}


void CamcopsApp::grantPrivilege()
{
    // *** security check
    setLockState(LockState::Privileged);
}


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

QString CamcopsApp::xstring(const QString& taskname, const QString& stringname,
                            const QString& default_str) const
{
    // ***
    bool found = false;
    if (found) {
        return "*** TO BE IMPLEMENTED ***";
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


int CamcopsApp::fontSizePt(UiConst::FontSize fontsize) const
{
    double factor = var(VAR_QUESTIONNAIRE_SIZE_PERCENT).toDouble() / 100;
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


void CamcopsApp::createVar(const QString &name, QVariant::Type type,
                                 const QVariant &default_value)
{
    if (m_storedvars.contains(name)) {  // Already exists
        return;
    }
    m_storedvars[name] = StoredVarPtr(
        new StoredVar(m_sysdb, name, type, default_value));
}


void CamcopsApp::setVar(const QString& name, const QVariant& value)
{
    if (!m_storedvars.contains(name)) {
        UiFunc::stopApp(QString("CamcopsApp::setVar: Attempt to set "
                                "nonexistent storedvar: %1").arg(name));
    }
    m_storedvars[name]->setValue(value);
}


QVariant CamcopsApp::var(const QString& name) const
{
    if (!m_storedvars.contains(name)) {
        UiFunc::stopApp(QString("CamcopsApp::var: Attempt to get nonexistent "
                                "storedvar: %1").arg(name));
    }
    return m_storedvars[name]->value();
}
