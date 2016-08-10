#pragma once
#include <QApplication>
#include <QMainWindow>
#include <QStackedWidget>
#include "tasklib/taskfactory.h"


enum class LockState {
    Unlocked,
    Locked,
    Privileged
};


class CamcopsApp : public QApplication
{
    Q_OBJECT
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
    bool privileged() const;
    bool locked() const;
    LockState lockstate() const;
    void unlock();
    void lock();
    void grantPrivilege();
signals:
    void lockStateChanged(LockState lockstate);
protected:
    void setLockState(LockState lockstate);
    LockState m_lockstate;
    QMainWindow* m_p_main_window;
    QStackedWidget* m_p_window_stack;
};
