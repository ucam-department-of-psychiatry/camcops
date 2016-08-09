#include "camcops_app.h"
#include <QApplication>
#include <QDateTime>
#include <QDialog>
#include <QDebug>
#include <QPushButton>
#include "common/ui_constants.h"
#include "lib/datetimefunc.h"
#include "lib/dbfunc.h"
#include "lib/filefunc.h"
#include "menu/main_menu.h"
#include "tasklib/inittasks.h"
#include "tests/master_test.h"


CamcopsApp::CamcopsApp(int& argc, char *argv[]) :
    m_p_task_factory(NULL),
    m_privileged(false),
    m_patient_locked(false),
    m_p_main_window(NULL),
    m_p_window_stack(NULL),
    m_p_qapp(NULL)
{
    // - The VERY FIRST THING we do is to create a QApplication, and that
    //   requires one bit of preamble.
    //   http://stackoverflow.com/questions/27963697
    // - Prevent native styling, which makes (for example) QListWidget colours
    //   not work from the stylsheet. This must be done before the app is
    //   created. See https://bugreports.qt.io/browse/QTBUG-45517

    QApplication::setStyle("fusion");
    m_p_qapp = new QApplication(argc, argv);

    QDateTime dt = now();
    qDebug() << "CamCOPS starting at:" << qPrintable(datetimeToIsoMs(dt))
             << "=" << qPrintable(datetimeToIsoMsUtc(dt));

    // However, we can't do things like opening the database until we have
    // created the app. So don't open the database in the initializer list!

    // Database lifetime:
    // http://stackoverflow.com/questions/7669987/what-is-the-correct-way-of-qsqldatabase-qsqlquery
    m_db = QSqlDatabase::addDatabase("QSQLITE", "data");
    m_sysdb = QSqlDatabase::addDatabase("QSQLITE", "sys");
    openDatabaseOrDie(m_db, DATA_DATABASE_FILENAME);
    openDatabaseOrDie(m_sysdb, SYSTEM_DATABASE_FILENAME);

    m_p_task_factory = new TaskFactory(*this);
    InitTasks(*m_p_task_factory);  // ensures all tasks are registered
    m_p_task_factory->finishRegistration();
    qDebug() << "Registered tasks:" << m_p_task_factory->tablenames();

    m_p_task_factory->makeAllTables();
    // *** also need to make the special tables at this point

    m_p_qapp->setStyleSheet(textfileContents(CSS_CAMCOPS));
}


CamcopsApp::~CamcopsApp()
{
    delete m_p_main_window;  // owns m_pWindowStack
    delete m_p_qapp;
}


int CamcopsApp::run()
{
    qDebug("CamcopsApp::run()");

    m_p_main_window = new QMainWindow();
    m_p_window_stack = new QStackedWidget(m_p_main_window);
    m_p_main_window->setCentralWidget(m_p_window_stack);

    MainMenu* menu = new MainMenu(*this);
    pushScreen(menu);
    m_p_main_window->show();

    // run_tests(*this);

    qDebug() << "Starting Qt event processor...";
    return m_p_qapp->exec();
}


void CamcopsApp::pushScreen(QWidget *widget)
{
    qDebug() << "Pushing screen";
    int index = m_p_window_stack->addWidget(widget);
    // The stack takes over ownership.
    m_p_window_stack->setCurrentIndex(index);
}


void CamcopsApp::popScreen()
{
    QWidget* top = m_p_window_stack->currentWidget();
    qDebug() << "Popping screen";
    m_p_window_stack->removeWidget(top);
    // Ownership is returned to the application, so...
    delete top;
}
