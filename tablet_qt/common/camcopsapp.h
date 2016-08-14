#pragma once
#include <QApplication>
#include <QSharedPointer>
#include <QSqlDatabase>
#include "common/dbconstants.h"
#include "tasklib/taskfactory.h"

class QMainWindow;
class QStackedWidget;


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
    TaskFactoryPtr m_p_task_factory;

    bool privileged() const;
    bool locked() const;
    LockState lockstate() const;
    void unlock();
    void lock();
    void grantPrivilege();

    bool whiskerConnected() const;
    void setWhiskerConnected(bool connected);

    bool patientSelected() const;
    QString patientDetails() const;
    void setSelectedPatient(int patient_id = NONEXISTENT_PK);
    int currentPatientId() const;

signals:
    void lockStateChanged(LockState lockstate);
    void whiskerConnectionStateChanged(bool connected);
    void selectedPatientChanged(bool selected, const QString& details);
protected:
    void setLockState(LockState lockstate);
    LockState m_lockstate;
    bool m_whisker_connected;
    QMainWindow* m_p_main_window;
    QStackedWidget* m_p_window_stack;
    int m_patient_id;
};
