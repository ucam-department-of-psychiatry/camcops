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

// #define DEBUG_OFFER_HTTP_TO_SERVER  // should NOT be defined in production (which is HTTPS only)

#include <QNetworkRequest>
#include <QMap>
#include <QPointer>
#include <QObject>
#include <QSqlDatabase>
#include <QSslError>
#include <QString>
#include <QUrl>
#include "common/aliases_camcops.h"
#include "common/design_defines.h"

class CamcopsApp;
class LogBox;
class QNetworkAccessManager;
class QNetworkReply;


class NetworkManager : public QObject
{
    // Controls network operations, optionally providing a progress display.

    using ReplyFuncPtr = void (NetworkManager::*)(QNetworkReply*);
    // ... a pointer to a member function of NetworkManager that takes a
    // QNetworkReply* parameter and returns void

    Q_OBJECT
public:
    NetworkManager(CamcopsApp& app, DatabaseManager& db,
                   TaskFactoryPtr p_task_factory, QWidget* parent);
    ~NetworkManager();

    // ------------------------------------------------------------------------
    // User interface
    // ------------------------------------------------------------------------
public:
    void setSilent(bool silent);
    void setTitle(const QString& title);
    void statusMessage(const QString& msg);
    enum class UploadMethod {
        Copy,
        MoveKeepingPatients,
        Move
    };
protected:
    void ensureLogBox();
    void deleteLogBox();
protected slots:
    void logboxCancelled();
    void logboxFinished();

    // ------------------------------------------------------------------------
    // Basic connection management
    // ------------------------------------------------------------------------
protected:
    bool ensurePasswordKnown();
    void disconnectManager();
    QNetworkRequest createRequest(
            const QUrl& url,
            bool offer_cancel,
            bool ssl,
            bool ignore_ssl_errors,
            QSsl::SslProtocol ssl_protocol = QSsl::AnyProtocol);
    QUrl serverUrl(bool& success) const;
    QString serverUrlDisplayString() const;
    QNetworkRequest createServerRequest(bool& success);
    void serverPost(Dict dict, ReplyFuncPtr reply_func,
                    bool include_user = true);
    bool processServerReply(QNetworkReply* reply);
    QString sizeBytes(qint64 size);
    RecordList getRecordList();
    bool replyReportsSuccess();
    void cleanup();
protected slots:
    void sslIgnoringErrorHandler(QNetworkReply* reply,
                                 const QList<QSslError>& errlist);
public slots:
    void cancel();
    void fail();
    void succeed();
    void finish(bool success = true);

    // ------------------------------------------------------------------------
    // Testing
    // ------------------------------------------------------------------------
public:
    void testHttpGet(const QString& url, bool offer_cancel = true);
    void testHttpsGet(const QString& url, bool offer_cancel = true,
                      bool ignore_ssl_errors = false);
protected:
    void testReplyFinished(QNetworkReply* reply);

    // ------------------------------------------------------------------------
    // Server registration
    // ------------------------------------------------------------------------
public:
    void registerWithServer();  // "register" is a C++ keyword
    void fetchIdDescriptions();
    void fetchExtraStrings();
protected:
    void registerSub1(QNetworkReply* reply);
    void registerSub2(QNetworkReply* reply);
    void registerSub3(QNetworkReply* reply);
    void fetchIdDescriptionsSub1(QNetworkReply* reply);
    void fetchExtraStringsSub1(QNetworkReply* reply);
    void storeServerIdentificationInfo();
    void storeAllowedTables();
    void storeExtraStrings();

    // ------------------------------------------------------------------------
    // Upload
    // ------------------------------------------------------------------------
public:
    void upload(UploadMethod method);
protected:
    // core
    void uploadNext(QNetworkReply* reply);
    // comms
    void checkDeviceRegistered();
    void checkUploadUser();
    void uploadFetchServerIdInfo();
    void uploadFetchAllowedTables();
    void startUpload();
    void startPreservation();
    void sendEmptyTables(const QStringList& tablenames);
    void sendTableWhole(const QString& tablename);
    void sendTableRecordwise(const QString& tablename);
    void requestRecordwisePkPrune();
    void sendNextRecord();
    void endUpload();
    // internal functions
    bool isPatientInfoComplete();
    bool applyPatientMoveOffTabletFlagsToTasks();
#ifdef DUPLICATE_ID_DESCRIPTIONS_INTO_PATIENT_TABLE
    bool writeIdDescriptionsToPatientTable();
#endif
    bool catalogueTablesForUpload();
    bool isServerVersionOK();
    bool arePoliciesOK();
    bool areDescriptionsOK();
    QVector<int> whichIdnumsUsedOnTablet();
    bool pruneRecordwisePks();
    void wipeTables();
    void queryFail(const QString& sql);
    void queryFailClearingMoveOffFlag(const QString& tablename);
    bool clearMoveOffTabletFlag(const QString& tablename);
    bool pruneDeadBlobs();

    // ------------------------------------------------------------------------
    // Analytics
    // ------------------------------------------------------------------------
#ifdef ALLOW_SEND_ANALYTICS
    void sendAnalytics();
#endif

    // ------------------------------------------------------------------------
    // Signals
    // ------------------------------------------------------------------------
signals:
    void cancelled();
    void finished();

    // ------------------------------------------------------------------------
    // Data
    // ------------------------------------------------------------------------
protected:
    CamcopsApp& m_app;
    DatabaseManager& m_db;
    TaskFactoryPtr m_p_task_factory;
    QWidget* m_parent;
    QString m_title;
    bool m_offer_cancel;
    bool m_silent;
    QPointer<LogBox> m_logbox;
    QNetworkAccessManager* m_mgr;

    QString m_tmp_password;
    QString m_tmp_session_id;
    QString m_tmp_session_token;
    // We store these here to save passing around large objects, and for convenience:
    QByteArray m_reply_data;
    Dict m_reply_dict;

    UploadMethod m_upload_method;

    enum class NextUploadStage {
        Invalid,
        CheckUser,
        FetchServerIdInfo,
        FetchAllowedTables,
        CheckPoliciesThenStartUpload,
        StartPreservation,
        Uploading,
        Finished,
    };

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
    int m_upload_n_records;  // cached as m_upload_recordwise_pks_to_send shrinks during upload
    QStringList m_upload_tables_to_wipe;
};
