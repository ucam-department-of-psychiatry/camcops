#pragma once
#include <QApplication>
#include <QPointer>
#include <QSharedPointer>
#include <QSqlDatabase>
#include <QStack>
#include "common/dbconstants.h"  // for NONEXISTENT_PK
#include "common/uiconstants.h"  // for FontSize
#include "lib/fieldref.h"  // for FieldRefPtr
#include "lib/slowguiguard.h"
#include "tasklib/task.h"  // for TaskPtr

class QSqlDatabase;
class QMainWindow;
class QStackedWidget;

class NetworkManager;
class OpenableWidget;
class StoredVar;
using StoredVarPtr = QSharedPointer<StoredVar>;
class TaskFactory;
using TaskFactoryPtr = QSharedPointer<TaskFactory>;


class CamcopsApp : public QApplication
{
    Q_OBJECT

    // ------------------------------------------------------------------------
    // Helper classes
    // ------------------------------------------------------------------------
public:
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

    // ------------------------------------------------------------------------
    // Core
    // ------------------------------------------------------------------------
public:
    CamcopsApp(int& argc, char *argv[]);
    ~CamcopsApp();
    int run();
    QSqlDatabase& db();
    QSqlDatabase& sysdb();
    TaskFactoryPtr factory();

    // ------------------------------------------------------------------------
    // Opening/closing windows
    // ------------------------------------------------------------------------
public:
    void open(OpenableWidget* widget, TaskPtr task = TaskPtr(nullptr),
              bool may_alter_task = false);
    SlowGuiGuard getSlowGuiGuard(const QString& text = "Opening...",
                                 const QString& title = "Please wait...",
                                 int minimum_duration_ms = 100);
signals:
    void taskAlterationFinished(TaskPtr task);

    // ------------------------------------------------------------------------
    // Security
    // ------------------------------------------------------------------------
public:
    bool privileged() const;
    bool locked() const;
    LockState lockstate() const;
    void unlock();
    void lock();
    void grantPrivilege();
signals:
    void lockStateChanged(LockState lockstate);

    // ------------------------------------------------------------------------
    // Networking
    // ------------------------------------------------------------------------
public:
    NetworkManager* networkManager() const;

    // ------------------------------------------------------------------------
    // Whisker
    // ------------------------------------------------------------------------
    bool whiskerConnected() const;
    void setWhiskerConnected(bool connected);
signals:
    void whiskerConnectionStateChanged(bool connected);

    // ------------------------------------------------------------------------
    // Patient
    // ------------------------------------------------------------------------
public:
    bool patientSelected() const;
    QString patientDetails() const;
    void setSelectedPatient(int patient_id = DbConst::NONEXISTENT_PK);
    int currentPatientId() const;
signals:
    void selectedPatientChanged(bool selected, const QString& details);

    // ------------------------------------------------------------------------
    // CSS convenience; fonts etc.
    // ------------------------------------------------------------------------
public:
    QString getSubstitutedCss(const QString& filename) const;
    int fontSizePt(UiConst::FontSize fontsize) const;

    // ------------------------------------------------------------------------
    // Extra strings (downloaded from server)
    // ------------------------------------------------------------------------
public:
    QString xstring(const QString& taskname, const QString& stringname,
                    const QString& default_str = "") const;
    bool hasExtraStrings(const QString& taskname) const;

    // ------------------------------------------------------------------------
    // Signals
    // ------------------------------------------------------------------------

public slots:
    void close();

    // ------------------------------------------------------------------------
    // Stored variables: generic
    // ------------------------------------------------------------------------
public:
    bool setVar(const QString& name, const QVariant& value,
                bool save_to_db = true);
    QVariant var(const QString& name) const;
    bool hasVar(const QString& name) const;
    FieldRefPtr storedVarFieldRef(const QString& name, bool mandatory = true,
                                  bool cached = true);
    // And so we can operate on a cached version:
    void clearCachedVars();  // resets them
    QVariant getCachedVar(const QString& name) const;
    bool setCachedVar(const QString& name, const QVariant& value);
public slots:
    void saveCachedVars();
protected:
    void createVar(const QString& name, QVariant::Type type,
                   const QVariant& default_value = QVariant());

    // ------------------------------------------------------------------------
    // Internal data
    // ------------------------------------------------------------------------
protected:
    QSqlDatabase m_datadb;
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
    QSharedPointer<NetworkManager> m_netmgr;
    mutable QMap<QString, QVariant> m_cachedvars;
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
