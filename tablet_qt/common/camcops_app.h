#pragma once
#include <QApplication>
#include <QMainWindow>
#include <QStackedWidget>
#include "tasklib/taskfactory.h"


class CamcopsApp
{
public:
    CamcopsApp(int argc, char *argv[]);
    ~CamcopsApp();
    int run();
    void pushScreen(QWidget* widget);
    void popScreen();
public:
    QSqlDatabase* m_pdb;
    QSqlDatabase* m_psysdb;
    TaskFactory* m_pTaskFactory;
    bool m_privileged;
    bool m_patientLocked;
protected:
    QMainWindow* m_pMainWindow;
    QStackedWidget* m_pWindowStack;
    QApplication* m_pQApp;
};
