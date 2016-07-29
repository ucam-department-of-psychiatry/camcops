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


CamcopsApp::CamcopsApp(int argc, char *argv[]) :
    m_pdb(NULL),
    m_psysdb(NULL),
    m_pTaskFactory(NULL),
    m_privileged(false),
    m_patientLocked(false),
    m_pMainWindow(NULL),
    m_pWindowStack(NULL),
    m_pQApp(NULL)
{
    // - The VERY FIRST THING we do is to create a QApplication, and that
    //   requires one bit of preamble.
    //   http://stackoverflow.com/questions/27963697
    // - Prevent native styling, which makes (for example) QListWidget colours
    //   not work from the stylsheet. This must be done before the app is
    //   created. See https://bugreports.qt.io/browse/QTBUG-45517
    // QApplication::setStyle("fusion");
    m_pQApp = new QApplication(argc, argv);
    // However, we can't do things like opening the database until we have
    // created the app. So don't open the database in the initializer list!

    QDateTime dt = now();
    qDebug() << "CamCOPS starting at:" << qPrintable(datetimeToIsoMs(dt))
             << "=" << qPrintable(datetimeToIsoMsUtc(dt));

    // m_db = QSqlDatabase::addDatabase("QSQLITE", "data");
    // m_sysdb = QSqlDatabase::addDatabase("QSQLITE", "sys");
    // openDatabaseOrDie(m_db, DATA_DATABASE_FILENAME);
    // openDatabaseOrDie(m_sysdb, SYSTEM_DATABASE_FILENAME);

    // m_pTaskFactory = new TaskFactory(*this);
    // InitTasks(m_taskFactory);  // ensures all tasks are registered
    // m_taskFactory.finishRegistration();
    // qDebug() << "Registered tasks:" << m_pTaskFactory->tablenames();

    // m_taskFactory.makeAllTables();
    // *** also need to make the special tables at this point

    // m_pQApp->setStyleSheet(textfileContents(CSS_CAMCOPS));
}

CamcopsApp::~CamcopsApp()
{
    delete m_pMainWindow;  // owns m_pWindowStack
    delete m_pQApp;
}

int CamcopsApp::run()
{
    m_pMainWindow = new QMainWindow();
    m_pWindowStack = new QStackedWidget(m_pMainWindow);
    m_pMainWindow->setCentralWidget(m_pWindowStack);

    MainMenu* menu = new MainMenu(*this);
    pushScreen(menu);

    qDebug() << "*** Screen pushed";

    m_pMainWindow->show();

    qDebug() << "*** Window shown";

    // run_tests(*this);
    qDebug() << "Starting Qt event processor...";
    return m_pQApp->exec();
}

void CamcopsApp::pushScreen(QWidget *widget)
{
    qDebug() << "Pushing screen";
    int index = m_pWindowStack->addWidget(widget);
    // The stack takes over ownership.
    m_pWindowStack->setCurrentIndex(index);
}

void CamcopsApp::popScreen()
{
    QWidget* top = m_pWindowStack->currentWidget();
    qDebug() << "Popping screen";
    m_pWindowStack->removeWidget(top);
    // Ownership is returned to the application, so...
    delete top;
}
