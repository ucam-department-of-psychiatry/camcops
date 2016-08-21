#pragma once
#include <QApplication>
#include <QPointer>
#include <QStack>
#include "common/dbconstants.h"
#include "common/uiconstants.h"
#include "tasklib/taskfactory.h"
#include "widgets/openablewidget.h"

class QSqlDatabase;
class QMainWindow;
class QStackedWidget;


enum class LockState {
    Unlocked,
    Locked,
    Privileged
};


struct OpenableInfo {
public:
    OpenableInfo()
    {}
    OpenableInfo(QPointer<OpenableWidget> widget, TaskPtr task,
                 Qt::WindowStates prev_window_state, bool may_alter_task) :
        widget(widget),
        task(task),
        prev_window_state(prev_window_state),
        may_alter_task(may_alter_task)
    {}
public:
    QPointer<OpenableWidget> widget;
    TaskPtr task;
    Qt::WindowStates prev_window_state;
    bool may_alter_task;
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

    void open(OpenableWidget* widget, TaskPtr task = TaskPtr(nullptr),
              bool may_alter_task = false);

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
    void taskAlterationFinished(TaskPtr task);

public slots:
    void close();

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
    QStack<OpenableInfo> m_info_stack;
};

/*
===============================================================================
Generic problem: derive from QObject or own one?
===============================================================================
- Derive from QObject:
    - can implement signals directly
    - all-in-one design
    - can't copy, so can't use X().chainmethod().clone() idiom
    - requires Q_OBJECT macro in all classes
    - SAFER: CAN USE deleteLater()
- Own QObject:
    - owned QObject has to do the signals emitting
    - two chains of inheritance (derive QObject/QWidget for new signals;
      derive Openable for everything else)
    - copying is not completely safe (as a member that is a QPointer<QWidget>
      will be shallow-copied only)
- Doesn't matter:
    - slots - QObject::connect() works with QObject signals but also with
      std::bind(...) signals, for arbitrary C++ objects.
- Decision:
    - Inherit from QObject via OpenableWidget
*/
