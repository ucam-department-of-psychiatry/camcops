#pragma once
#include <QApplication>
#include <QList>
#include <QPointer>
#include <QSharedPointer>
#include <QSqlDatabase>
#include <QStack>
#include "common/dbconstants.h"  // for NONEXISTENT_PK
#include "common/uiconstants.h"  // for FontSize
#include "crypto/secureqstring.h"
#include "db/fieldref.h"  // for FieldRefPtr
#include "dbobjects/patient.h"
#include "lib/slowguiguard.h"
#include "tasklib/task.h"  // for TaskPtr

class NetworkManager;
class OpenableWidget;
using PatientPtr = QSharedPointer<Patient>;
using PatientPtrList = QList<PatientPtr>;
class QSqlDatabase;
class QMainWindow;
class QStackedWidget;
class StoredVar;
using StoredVarPtr = QSharedPointer<StoredVar>;
class TaskFactory;
using TaskFactoryPtr = QSharedPointer<TaskFactory>;
class Version;


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
                     Qt::WindowStates prev_window_state, bool may_alter_task,
                     PatientPtr patient) :
            widget(widget),
            task(task),
            prev_window_state(prev_window_state),
            may_alter_task(may_alter_task),
            patient(patient)
        {}
    public:
        QPointer<OpenableWidget> widget;
        TaskPtr task;
        Qt::WindowStates prev_window_state;
        bool may_alter_task;
        PatientPtr patient;
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
    TaskFactoryPtr taskFactory();
    void upgradeDatabase(const Version& old_version, const Version& new_version);

    // ------------------------------------------------------------------------
    // Opening/closing windows
    // ------------------------------------------------------------------------
public:
    void open(OpenableWidget* widget, TaskPtr task = TaskPtr(nullptr),
              bool may_alter_task = false,
              PatientPtr patient = PatientPtr(nullptr));
    SlowGuiGuard getSlowGuiGuard(const QString& text = "Opening...",
                                 const QString& title = "Please wait...",
                                 int minimum_duration_ms = 100);
signals:
    void taskAlterationFinished(TaskPtr task);
public slots:
    void close();

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
    bool storingServerPassword() const;
    void setEncryptedServerPassword(const QString& password);
    SecureQString getPlaintextServerPassword() const;
    void changeAppPassword();
    void changePrivPassword();
protected:
    void resetEncryptionKeyIfRequired();
    bool checkPassword(const QString& hashed_password_varname,
                       const QString& text, const QString& title);
    void setHashedPassword(const QString& hashed_password_varname,
                           const QString& password);
    void changePassword(const QString& hashed_password_varname,
                        const QString& text);
signals:
    void lockStateChanged(LockState lockstate);

    // ------------------------------------------------------------------------
    // Network
    // ------------------------------------------------------------------------
public:
    NetworkManager* networkManager() const;
    bool needsUpload() const;
    void setNeedsUpload(bool needs_upload);
signals:
    void needsUploadChanged(bool needs_upload);

    // ------------------------------------------------------------------------
    // Whisker
    // ------------------------------------------------------------------------
public:
    bool whiskerConnected() const;
    void setWhiskerConnected(bool connected);
signals:
    void whiskerConnectionStateChanged(bool connected);

    // ------------------------------------------------------------------------
    // Patient
    // ------------------------------------------------------------------------
public:
    bool isPatientSelected() const;
    void setSelectedPatient(int patient_id);
    void patientHasBeenEdited(int patient_id);
    const Patient* selectedPatient() const;
    int selectedPatientId() const;
    PatientPtrList getAllPatients();
    QString idDescription(int which_idnum);
    QString idShortDescription(int which_idnum);
    IdPolicy uploadPolicy() const;
    IdPolicy finalizePolicy() const;
protected:
    void reloadPatient(int patient_id);
signals:
    void selectedPatientChanged(const Patient* patient);
    void selectedPatientDetailsChanged(const Patient* patient);

    // ------------------------------------------------------------------------
    // CSS convenience; fonts etc.
    // ------------------------------------------------------------------------
public:
    QString getSubstitutedCss(const QString& filename) const;
    int fontSizePt(UiConst::FontSize fontsize, double factor_pct = -1) const;
signals:
    void fontSizeChanged();

    // ------------------------------------------------------------------------
    // Extra strings (downloaded from server)
    // ------------------------------------------------------------------------
public:
    QString xstring(const QString& taskname, const QString& stringname,
                    const QString& default_str = "") const;
    bool hasExtraStrings(const QString& taskname) const;
    void clearExtraStringCache();
    void deleteAllExtraStrings();
protected:
    QString xstringDirect(const QString& taskname, const QString& stringname,
                          const QString& default_str = "") const;
    mutable QMap<QPair<QString, QString>, QString> m_extrastring_cache;

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
    bool cachedVarChanged(const QString& name) const;
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
    PatientPtr m_patient;
    QStack<OpenableInfo> m_info_stack;
    QMap<QString, StoredVarPtr> m_storedvars;
    QSharedPointer<NetworkManager> m_netmgr;
    mutable QMap<QString, QVariant> m_cachedvars;
};
