#pragma once
#include <QApplication>
#include <QSharedPointer>
#include <QPointer>
#include <QSqlDatabase>
#include "common/dbconstants.h"
#include "common/uiconstants.h"

class QMainWindow;
class QStackedWidget;
class TaskFactory;
typedef QSharedPointer<TaskFactory> TaskFactoryPtr;


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

    QSqlDatabase& db();
    QSqlDatabase& sysdb();
    TaskFactoryPtr factory();

    void pushScreen(QWidget* widget);

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

    int fontSizePt(FontSize fontsize) const;

signals:
    void lockStateChanged(LockState lockstate);
    void whiskerConnectionStateChanged(bool connected);
    void selectedPatientChanged(bool selected, const QString& details);

public slots:
    void popScreen();

protected:
    QSqlDatabase m_db;
    QSqlDatabase m_sysdb;
    TaskFactoryPtr m_p_task_factory;
    void setLockState(LockState lockstate);
    LockState m_lockstate;
    bool m_whisker_connected;
    QPointer<QMainWindow> m_p_main_window;
    QPointer<QStackedWidget> m_p_window_stack;
    int m_patient_id;
};
