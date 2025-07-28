/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#pragma once

// #define DEBUG_OFFER_HTTP_TO_SERVER
// ... should NOT be defined in production (which is HTTPS only)

#include <QMap>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QObject>
#include <QPointer>
#include <QSqlDatabase>
#include <QSslError>
#include <QString>
#include <QUrl>

#include "common/aliases_camcops.h"

class CamcopsApp;
class LogBox;
class QNetworkAccessManager;
class Version;

// Controls network operations, optionally providing a progress display.
class NetworkManager : public QObject
{
    Q_OBJECT

    // ------------------------------------------------------------------------
    // Shorthand
    // ------------------------------------------------------------------------

    using ReplyFuncPtr = void (NetworkManager::*)(QNetworkReply*);
    // ... a pointer to a member function of NetworkManager that takes a
    // QNetworkReply* parameter and returns void

    // ------------------------------------------------------------------------
    // Helper classes
    // ------------------------------------------------------------------------

public:
    // How should we upload?
    enum class UploadMethod {
        Invalid,  // clinician pressed "cancel"
        // clinician mode or single user mode if any current tasks started
        Copy,
        // clinician mode or single user mode if no started current tasks
        MoveKeepingPatients,
        Move  // clinician mode: move all data
    };

    // Types of network error.
    enum ErrorCode {
        NoError,
        IncorrectReplyFormat,
        GenericNetworkError,
        ServerError,
        JsonParseError,
    };

    // ------------------------------------------------------------------------
    // Core
    // ------------------------------------------------------------------------

public:
    NetworkManager(
        CamcopsApp& app,
        DatabaseManager& db,
        TaskFactoryPtr p_task_factory,
        QWidget* parent
    );
    ~NetworkManager();

    // ------------------------------------------------------------------------
    // User interface
    // ------------------------------------------------------------------------

public:
    // Operate in silent mode (without status information)?
    void enableLogging();
    void disableLogging();
    bool isLogging() const;

    // Sets the window title.
    void setTitle(const QString& title);

    // Shows a plain-text status message.
    void statusMessage(const QString& msg) const;

    // Shows an HTML status message.
    void htmlStatusMessage(const QString& html) const;

protected:
    // Ensure we have a logbox.
    void ensureLogBox() const;

    // Delete our logbox.
    void deleteLogBox();

protected slots:
    // "The user pressed cancel on the logbox dialogue."
    void logboxCancelled();

    // "The user pressed OK/Finish on the logbox dialogue."
    void logboxFinished();

    // ------------------------------------------------------------------------
    // Basic connection management
    // ------------------------------------------------------------------------

protected:
    // Ensure we know the user's upload password (ask if not).
    bool ensurePasswordKnown();

    // Disconnect signals/slots from our Qt manager object.
    void disconnectManager();

    // Create a generic network request.
    QNetworkRequest createRequest(
        const QUrl& url,
        bool offer_cancel,
        bool ssl,
        bool ignore_ssl_errors,
        QSsl::SslProtocol ssl_protocol = QSsl::AnyProtocol
    );

    QString userAgent() const;

    // Returns the URL for the CamCOPS server, as a QUrl.
    QUrl serverUrl(bool& success) const;

    // Returns the URL for the CamCOPS server, as a string.
    QString serverUrlDisplayString() const;

    // Create a request to our server.
    QNetworkRequest createServerRequest(bool& success);

    // Send a message to the server via an HTTP POST, and set up a callback
    // for the results.
    void serverPost(
        Dict dict, ReplyFuncPtr reply_func, bool include_user = true
    );

    // Process the server's reply into our internal data structures,
    // principally m_reply_dict.
    bool processServerReply(QNetworkReply* reply);

    // Formats a human-readable version of "size", e.g. "3 Kb" or similar.
    QString sizeBytes(qint64 size) const;

    // Returns a list of downloaded records from our internal m_reply_dict.
    RecordList getRecordList() const;

    // Does the reply have the correct format from the CamCOPS API?
    bool replyFormatCorrect() const;

    // Did the reply say it was successful?
    bool replyReportsSuccess() const;

    // Wipe internal transmission/reply information.
    void cleanup();

    // Doesn't do very much at present (but in theory converts Qt network
    // errors to our own mapping).
    ErrorCode convertQtNetworkCode(const QNetworkReply::NetworkError error_code
    );

protected slots:
    // We come here when there's an SSL error and we want to ignore it.
    void sslIgnoringErrorHandler(
        QNetworkReply* reply, const QList<QSslError>& errlist
    );

public slots:
    // "User pressed cancel."
    void cancel();

    // "Network operation failed somehow."
    void fail(
        const NetworkManager::ErrorCode error_code
        = NetworkManager::ErrorCode::NoError,
        const QString& error_string = QString()
    );

    // "Network operation succeeded."
    void succeed();

    // ------------------------------------------------------------------------
    // Testing
    // ------------------------------------------------------------------------

public:
    // Tests HTTP GET.
    void testHttpGet(const QString& url, bool offer_cancel = true);

    // Tests HTTPS GET.
    void testHttpsGet(
        const QString& url,
        bool offer_cancel = true,
        bool ignore_ssl_errors = false
    );

protected:
    // Callback for the tests.
    void testReplyFinished(QNetworkReply* reply);

    // ------------------------------------------------------------------------
    // Registering a device with the server.
    // ------------------------------------------------------------------------

public:
    // Register with the CamCOPS server.
    void registerWithServer();  // "register" is a C++ keyword

    // Fetch all information without registration (i.e. fetch ID descriptions,
    // table details, extra strings...).
    void fetchAllServerInfo();

    // Fetch ID number type description/information (and group ID policies)
    // from the server.
    void fetchIdDescriptions();

    // Fetch extra strings from the server.
    void fetchExtraStrings();

protected:
    // Regular entry point for phases under registerWithServer().
    void registerNext(QNetworkReply* reply = nullptr);

    // Parse reply to fetchIdDescriptions().
    void fetchIdDescriptionsSub1(QNetworkReply* reply);

    // Parse reply to fetchExtraStrings().
    void fetchExtraStringsSub1(QNetworkReply* reply);

    // Parse reply to fetchAllServerInfo().
    void fetchAllServerInfoSub1(QNetworkReply* reply);

    // Store ID/policy information from the server.
    void storeServerIdentificationInfo();

    // Store "which tables are allowed" information from the server.
    void storeAllowedTables();

    // Store extra strings from the server.
    void storeExtraStrings();

    // ------------------------------------------------------------------------
    // Upload
    // ------------------------------------------------------------------------

public:
    // Upload to the server.
    void upload(UploadMethod method);

protected:
    // Upload core (called repeatedly at different phases):
    void uploadNext(QNetworkReply* reply);

    // Does a "no-op"-type request to ensure our device is registered.
    void checkDeviceRegistered();

    // Check our user/device is permitted to upload.
    void checkUploadUser();

    // Fetch server's version/ID policies/ID descriptions.
    void uploadFetchServerIdInfo();

    // Does this server version support validation of patient details being
    // uploaded?
    bool serverSupportsValidatePatients() const;

    // Validate patients for upload.
    void uploadValidatePatients();

    // Fetch details of which tables the server will accept.
    void uploadFetchAllowedTables();

    // Start the actual upload.
    void startUpload();

    // Ask the server to begin a preservation "transaction".
    void startPreservation();

    // Send details of all empty tables (in a quick way).
    void sendEmptyTables(const QStringList& tablenames);

    // Send a table in one go.
    void sendTableWhole(const QString& tablename);

    // Sent a table, record-wise (for giant tables).
    void sendTableRecordwise(const QString& tablename);

    // "Here are my PKs, record modification dates, etc. Which ones do you
    // want to receive full data for?" (Used to speed up the upload of giant
    // tables.)
    void requestRecordwisePkPrune();

    // Called repeatedly during record-wise upload.
    void sendNextRecord();

    // Tell the server the upload has finished (asking it to "commit" our
    // ongoing transaction.)
    void endUpload();

    // Is our internal patient info complete (e.g. compliant with the server's
    // ID policies)?
    bool isPatientInfoComplete();

    // For those patients the user has flagged individually to move off, copy
    // the move-off status to those patients' tasks.
    bool applyPatientMoveOffTabletFlagsToTasks();

    // Trawl our tables, populating our internal catalogues
    // (m_upload_empty_tables, m_upload_tables_to_send_recordwise,
    // m_upload_tables_to_send_whole, m_upload_tables_to_wipe).
    bool catalogueTablesForUpload();

    // Check the server version (a) matches what we had stored, and (b) is
    // new enough for us to upload at all.
    bool isServerVersionOK() const;

    // Server version matches what we had stored.
    bool serverVersionMatchesStored() const;

    // Server version is new enough for us to upload at all.
    bool serverVersionNewEnough() const;

    // Version returned by the server.
    Version serverVersionFromReply() const;

    // Do our ID policies match those of the server?
    bool arePoliciesOK() const;

    // Do our ID number description match those of the server?
    bool areDescriptionsOK() const;

    // Which ID number types are in use?
    QVector<int> whichIdnumsUsedOnTablet() const;

    // Based on the server's reply to requestRecordwisePkPrune(), restrict
    // which records we will send.
    bool pruneRecordwisePks();

    // Wipe all tables marked to be wiped.
    void wipeTables();

    // Tell the user about the failure of a local SQL query.
    void queryFail(const QString& sql);

    // Tell the user about an SQL query failure whilst clearing the move-off
    // flag.
    void queryFailClearingMoveOffFlag(const QString& tablename);

    // Clear the move-off flag for all records in a table.
    bool clearMoveOffTabletFlag(const QString& tablename);

    // Delete local records of any BLOBs that have become orphaned.
    bool pruneDeadBlobs();

    // Does the server support the newer one-step upload feature?
    bool serverSupportsOneStepUpload() const;

    // Should we use the one-step upload feature, because (a) the user wants
    // it, and (b) the server supports it?
    bool shouldUseOneStepUpload() const;

    // Perform a one-step upload (via a big JSON dump).
    void uploadOneStep();

    // Provide (as a JSON string) a mapping from table name to PK name.
    QString getPkInfoAsJson();

    // ------------------------------------------------------------------------
    // Single-user mode
    // ------------------------------------------------------------------------

public:
    // In single-user mode, send the server a proquint access key and receive
    // patient details, user details, and schedule information.
    void registerPatient();

    // Update task schedules for the single user.
    void updateTaskSchedulesAndPatientDetails();

protected:
    // Parse reply to registerPatient().
    void registerPatientSub1(QNetworkReply* reply);

    // Store the username/password that the server has given us.
    void setUserDetails();

    // From the server's reply, including patient details, create a local
    // patient record (and select it as our sole patient).
    bool createSinglePatient();

    // From the server's reply, set our local variables regarding the
    // intellectual property context in which we're operating.
    bool setIpUseInfo();

    // Parse reply to updateTaskSchedules().
    void receivedTaskSchedulesAndPatientDetails(QNetworkReply* reply);

    // Store the task schedules.
    void storeTaskSchedulesAndPatientDetails();

    // Copy complete status for anonymous tasks when updating tasks
    void updateCompleteStatusForAnonymousTasks(
        TaskSchedulePtrList old_schedules, TaskSchedulePtrList new_schedules
    );

    // ------------------------------------------------------------------------
    // Signals
    // ------------------------------------------------------------------------
signals:
    // "Operation was cancelled."
    void cancelled(
        const NetworkManager::ErrorCode error_code, const QString& error_string
    );

    // "Operation has finished, successfully or not; user has acknowledged."
    void finished();

    // ------------------------------------------------------------------------
    // Translatable text
    // ------------------------------------------------------------------------

protected:
    // Provides text to say "please re-fetch server information".
    static QString txtPleaseRefetchServerInfo();

    // ------------------------------------------------------------------------
    // Data
    // ------------------------------------------------------------------------

protected:
    // Our app.
    CamcopsApp& m_app;

    // The data database.
    DatabaseManager& m_db;

    // Our app's task factory.
    TaskFactoryPtr m_p_task_factory;

    // Parent widget.
    QWidget* m_parent;

    // Window title.
    QString m_title;

    // Offer a cancel button?
    bool m_offer_cancel;

    // Suppress all status messages?
    bool m_silent;

    // Our logbox (triggered when a status message is displayed)
    mutable QPointer<LogBox> m_logbox;

    // Our Qt network manager
    QNetworkAccessManager* m_mgr;

    // Temporary storage of information going to the server:
    QString m_tmp_password;
    QString m_tmp_session_id;
    QString m_tmp_session_token;

    // Incoming information.
    // We store these here to save passing around large objects, and for
    // convenience:
    QByteArray m_reply_data;
    Dict m_reply_dict;  // the main repository of information received

    // How will we upload?
    UploadMethod m_upload_method;

    // Sequencing of the upload steps
    enum class NextUploadStage {
        Invalid,
        CheckUser,
        FetchServerIdInfo,
        StoreExtraStrings,
        ValidatePatients,  // v2.3.0
        FetchAllowedTables,
        CheckPoliciesThenStartUpload,
        StartPreservation,
        Uploading,
        Finished,
    };

    // Internal calculations for uploading.
    NextUploadStage m_upload_next_stage;
    QVector<int> m_upload_patient_ids_to_move_off;
    QStringList m_upload_empty_tables;
    QStringList m_upload_tables_to_send_whole;
    QStringList m_upload_tables_to_send_recordwise;
    QString m_upload_recordwise_table_in_progress;
    QStringList m_upload_recordwise_fieldnames;
    int m_upload_current_record_index;
    bool m_recordwise_prune_req_sent;
    bool m_recordwise_pks_pruned;
    QVector<int> m_upload_recordwise_pks_to_send;
    int m_upload_n_records;
    // ... cached as m_upload_recordwise_pks_to_send shrinks during upload
    QStringList m_upload_tables_to_wipe;
    QString m_upload_patient_info_json;

    // Possible states during single-user-mode patient registration.
    enum class NextRegisterStage {
        Invalid,
        Register,
        StoreServerIdentification,
        GetAllowedTables,
        StoreAllowedTables,
        GetExtraStrings,
        StoreExtraStrings,
        GetTaskSchedules,
        StoreTaskSchedules,
        Finished,
    };

    // Current registration stage.
    NextRegisterStage m_register_next_stage;
};
