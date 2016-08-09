#pragma once
#include <QApplication>
#include <QMainWindow>
#include <QStackedWidget>
#include "tasklib/taskfactory.h"


class CamcopsApp
{
public:
    CamcopsApp(int& argc, char *argv[]);
    ~CamcopsApp();
    int run();
    void pushScreen(QWidget* widget);
    void popScreen();
public:
    QSqlDatabase m_db;
    QSqlDatabase m_sysdb;
    TaskFactory* m_p_task_factory;
    bool m_privileged;
    bool m_patient_locked;
protected:
    QMainWindow* m_p_main_window;
    QStackedWidget* m_p_window_stack;
    QApplication* m_p_qapp;
};
