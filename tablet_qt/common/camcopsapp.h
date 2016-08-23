#pragma once
#include <QApplication>
#include <QPointer>
#include <QSharedPointer>
#include <QSqlDatabase>
#include <QStack>
#include "common/dbconstants.h"  // for NONEXISTENT_PK
#include "common/uiconstants.h"  // for FontSize
#include "tasklib/task.h"  // for TaskPtr

class QSqlDatabase;
class QMainWindow;
class QStackedWidget;

class OpenableWidget;
class StoredVar;
typedef QSharedPointer<StoredVar> StoredVarPtr;
class TaskFactory;
typedef QSharedPointer<TaskFactory> TaskFactoryPtr;


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
    enum class LockState {
        Unlocked,
        Locked,
        Privileged
    };

public:
    CamcopsApp(int& argc, char *argv[]);
    ~CamcopsApp();
    int run();

    QSqlDatabase& db();
    QSqlDatabase& sysdb();
    TaskFactoryPtr factory();

    // ------------------------------------------------------------------------
    // Opening windows
    // ------------------------------------------------------------------------
    void open(OpenableWidget* widget, TaskPtr task = TaskPtr(nullptr),
              bool may_alter_task = false);

    // ------------------------------------------------------------------------
    // Security
    // ------------------------------------------------------------------------
    bool privileged() const;
    bool locked() const;
    LockState lockstate() const;
    void unlock();
    void lock();
    void grantPrivilege();

    // ------------------------------------------------------------------------
    // Whisker
    // ------------------------------------------------------------------------
    bool whiskerConnected() const;
    void setWhiskerConnected(bool connected);

    // ------------------------------------------------------------------------
    // Patient
    // ------------------------------------------------------------------------
    bool patientSelected() const;
    QString patientDetails() const;
    void setSelectedPatient(int patient_id = DbConst::NONEXISTENT_PK);
    int currentPatientId() const;

    // ------------------------------------------------------------------------
    // Stored variables: specific
    // ------------------------------------------------------------------------
    int fontSizePt(UiConst::FontSize fontsize) const;

signals:
    void lockStateChanged(LockState lockstate);
    void whiskerConnectionStateChanged(bool connected);
    void selectedPatientChanged(bool selected, const QString& details);
    void taskAlterationFinished(TaskPtr task);

public slots:
    void close();

protected:
    // ------------------------------------------------------------------------
    // Stored variables: generic
    // ------------------------------------------------------------------------
    void createVar(const QString& name, QVariant::Type type,
                         const QVariant& default_value);
    void setVar(const QString& name, const QVariant& value);
    QVariant var(const QString& name) const;

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
    QMap<QString, StoredVarPtr> m_storedvars;
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
