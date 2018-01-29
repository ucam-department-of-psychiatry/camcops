/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once
#include <QApplication>
#include <QPointer>
#include <QSharedPointer>
#include <QSqlDatabase>
#include <QStack>
#include "common/aliases_camcops.h"
#include "common/textconst.h"
#include "common/uiconst.h"  // for FontSize
#include "crypto/secureqstring.h"
#include "db/fieldref.h"  // for FieldRefPtr
#include "dbobjects/patient.h"
#include "questionnairelib/namevalueoptions.h"
#include "tasklib/task.h"  // for TaskPtr
class IdPolicy;
class NetworkManager;
class OpenableWidget;
class QSqlDatabase;
class QMainWindow;
class QStackedWidget;
class QTextStream;
class SlowGuiGuard;
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
    CamcopsApp(int& argc, char* argv[]);
    ~CamcopsApp();
    int run();
    void backgroundStartup();
    DatabaseManager& db();
    DatabaseManager& sysdb();
    TaskFactory* taskFactory();

    // ------------------------------------------------------------------------
    // Initialization
    // ------------------------------------------------------------------------
public:
    QString dbFullPath(const QString& filename);
protected:
    QString defaultDatabaseDir() const;
    bool processCommandLineArguments(int& retcode);  // returns: happy to continue?
    void announceStartup();
    void registerDatabaseDrivers();
    void openOrCreateDatabases();
    void closeDatabases();
    bool connectDatabaseEncryption(QString& new_user_password,
                                   bool& user_cancelled_please_quit);
    bool encryptExistingPlaintextDatabases(const QString& passphrase);
    void seedRng();
    void makeStoredVarTable();
    void createStoredVars();
    Version upgradeDatabaseBeforeTablesMade();
    void upgradeDatabaseAfterTasksRegistered(const Version& old_version);
    void makeOtherSystemTables();
    void registerTasks();
    void makeTaskTables();
    void initGuiOne();
    void initGuiTwoStylesheet();
    void openMainWindow();

    // ------------------------------------------------------------------------
    // Opening/closing windows
    // ------------------------------------------------------------------------
public:
    void open(OpenableWidget* widget, TaskPtr task = TaskPtr(nullptr),
              bool may_alter_task = false,
              PatientPtr patient = PatientPtr(nullptr));
    SlowGuiGuard getSlowGuiGuard(const QString& text = "Opening...",
                                 const QString& title = textconst::PLEASE_WAIT,
                                 int minimum_duration_ms = 100);

signals:
    void taskAlterationFinished(TaskPtr task);
public slots:
    void close();
    void enterFullscreen();
    void leaveFullscreen();

    // ------------------------------------------------------------------------
    // Security and related
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
    QString deviceId() const;
protected:
    void resetEncryptionKeyIfRequired();
    bool checkPassword(const QString& hashed_password_varname,
                       const QString& text, const QString& title);
    void setHashedPassword(const QString& hashed_password_varname,
                           const QString& password);
    bool changePassword(const QString& hashed_password_varname,
                        const QString& text,
                        QString* p_old_password = nullptr,
                        QString* p_new_password = nullptr);
    void regenerateDeviceId();
signals:
    void lockStateChanged(LockState lockstate);

    // ------------------------------------------------------------------------
    // Network
    // ------------------------------------------------------------------------
public:
    NetworkManager* networkManager() const;
    bool needsUpload() const;
    void setNeedsUpload(bool needs_upload);
protected:
    void makeNetManager();
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
    void deselectPatient();
    void patientHasBeenEdited(int patient_id);
    Patient* selectedPatient() const;
    int selectedPatientId() const;
    PatientPtrList getAllPatients(bool sorted = true);
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
    int fontSizePt(uiconst::FontSize fontsize, double factor_pct = -1) const;
    qreal dotsPerInch() const;
signals:
    void fontSizeChanged();

    // ------------------------------------------------------------------------
    // Server info: version, ID numbers, policies
    // ------------------------------------------------------------------------
public:
    Version serverVersion() const;
    IdPolicy uploadPolicy() const;
    IdPolicy finalizePolicy() const;
    bool idDescriptionExists(int which_idnum);
    QString idDescription(int which_idnum);
    QString idShortDescription(int which_idnum);
    void deleteAllIdDescriptions();
    bool setIdDescription(int which_idnum, const QString& desc,
                          const QString& shortdesc);
    QVector<IdNumDescriptionPtr> getAllIdDescriptions();
    QVector<int> whichIdNumsAvailable();
protected:
    void clearIdDescriptionCache();
    QPair<QString, QString> idDescriptionDirect(int which_idnum);  // desc, shortdesc
    QPair<QString, QString> idDescShortDesc(int which_idnum);
    mutable QMap<int, QPair<QString, QString>> m_iddescription_cache;

    // ------------------------------------------------------------------------
    // Extra strings (downloaded from server)
    // ------------------------------------------------------------------------
public:
    QString xstring(const QString& taskname, const QString& stringname,
                    const QString& default_str = "");
    bool hasExtraStrings(const QString& taskname);
    void clearExtraStringCache();
    void deleteAllExtraStrings();
    void setAllExtraStrings(const RecordList& recordlist);
    QString appstring(const QString& stringname,
                      const QString& default_str = "");
protected:
    QString xstringDirect(const QString& taskname, const QString& stringname,
                          const QString& default_str = "");
    mutable QMap<QPair<QString, QString>, QString> m_extrastring_cache;

    // ------------------------------------------------------------------------
    // Allowed tables on the server
    // ------------------------------------------------------------------------
public:
    void setAllowedServerTables(const RecordList& recordlist);
    bool mayUploadTable(const QString& tablename,
                        const Version& server_version,
                        bool& server_has_table,
                        Version& min_client_version,
                        Version& min_server_version);
protected:
    QStringList nonTaskTables() const;
    Version minServerVersionForTable(const QString& tablename);
    void deleteAllowedServerTables();

    // ------------------------------------------------------------------------
    // Stored variables: generic
    // ------------------------------------------------------------------------
public:
    // These have a hidden cache system to reduce database access, in that
    // m_storedvars stores values and doesn't ask the database again:
    QVariant var(const QString& name) const;
    QString varString(const QString& name) const;
    bool varBool(const QString& name) const;
    int varInt(const QString& name) const;
    bool setVar(const QString& name, const QVariant& value,
                bool save_to_db = true);

    bool hasVar(const QString& name) const;
    FieldRefPtr storedVarFieldRef(const QString& name, bool mandatory = true,
                                  bool cached = true);

    // And so we can operate on an "externally visible" cached version, for
    // editing settings (with an option to save or discard), we have a second
    // cache:
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
    // Terms and conditions
    // ------------------------------------------------------------------------
public:
    QDateTime agreedTermsAt() const;
protected:
    bool hasAgreedTerms() const;
    void offerTerms();

    // ------------------------------------------------------------------------
    // Uploading
    // ------------------------------------------------------------------------
public:
    void upload();

    // ------------------------------------------------------------------------
    // App strings, or derived
    // ------------------------------------------------------------------------
public:
    NameValueOptions nhsPersonMaritalStatusCodeOptions();
    NameValueOptions nhsEthnicCategoryCodeOptions();

    // ------------------------------------------------------------------------
    // Internal data
    // ------------------------------------------------------------------------
protected:
    QString m_database_path;
    DatabaseManagerPtr m_datadb;
    DatabaseManagerPtr m_sysdb;
    TaskFactoryPtr m_p_task_factory;
    void setLockState(LockState lockstate);
    LockState m_lockstate;
    bool m_whisker_connected;
    QPointer<QMainWindow> m_p_main_window;
    QPointer<QStackedWidget> m_p_window_stack;
    QSharedPointer<QStackedWidget> m_p_hidden_stack;  // we own it entirely, so QSharedPointer
    PatientPtr m_patient;
    QStack<OpenableInfo> m_info_stack;
    QMap<QString, StoredVarPtr> m_storedvars;
    QSharedPointer<NetworkManager> m_netmgr;
    mutable QMap<QString, QVariant> m_cachedvars;
    qreal m_dpi;
};
