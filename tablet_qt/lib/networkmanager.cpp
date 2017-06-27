/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#define DEBUG_NETWORK_REQUESTS
// #define DEBUG_NETWORK_REPLIES

#include "networkmanager.h"
#include <functional>
#include <QObject>
#include <QSqlQuery>
#include <QtNetwork/QNetworkAccessManager>
#include <QtNetwork/QNetworkRequest>
#include <QtNetwork/QNetworkReply>
#include <QtNetwork/QSslConfiguration>
#include <QUrl>
#include <QUrlQuery>
#include "common/camcopsapp.h"
#include "common/camcopsversion.h"
#include "common/varconst.h"
#include "db/dbtransaction.h"
#include "dialogs/passwordentrydialog.h"
#include "dialogs/logbox.h"
#include "dbobjects/blob.h"
#include "lib/convert.h"
#include "lib/datetime.h"
#include "lib/idpolicy.h"
#include "lib/uifunc.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"

using dbfunc::delimit;

// Keys used by server or client (S server, C client, B bidirectional)
const QString KEY_CAMCOPS_VERSION("camcops_version");  // C->S
const QString KEY_DATABASE_TITLE("databaseTitle");  // S->C
const QString KEY_DEVICE("device");  // C->S
const QString KEY_DEVICE_FRIENDLY_NAME("devicefriendlyname");  // C->S
const QString KEY_ERROR("error");  // S->C
const QString KEY_FIELDS("fields");    // B; fieldnames
const QString KEY_ID_POLICY_UPLOAD("idPolicyUpload");  // S->C
const QString KEY_ID_POLICY_FINALIZE("idPolicyFinalize");  // S->C
const QString KEY_NFIELDS("nfields");  // B
const QString KEY_NRECORDS("nrecords");  // B
const QString KEY_OPERATION("operation");  // C->S
const QString KEY_PASSWORD("password");  // C->S
const QString KEY_PKNAME("pkname");  // C->S
const QString KEY_PKVALUES("pkvalues");  // C->S
const QString KEY_RESULT("result");  // S->C
const QString KEY_SERVER_CAMCOPS_VERSION("serverCamcopsVersion");  // S->C
const QString KEY_SESSION_ID("session_id");  // B
const QString KEY_SESSION_TOKEN("session_token");  // B
const QString KEY_SUCCESS("success");  // S->C
const QString KEY_TABLE("table");  // C->S
const QString KEY_TABLES("tables");  // C->S
const QString KEY_USER("user");  // C->S
const QString KEY_VALUES("values");  // C->S
const QString KEYSPEC_ID_DESCRIPTION("idDescription%1");  // S->C
const QString KEYSPEC_ID_SHORT_DESCRIPTION("idShortDescription%1");  // S->C
const QString KEYSPEC_RECORD("record%1");  // B

// Operations for server:
const QString OP_CHECK_DEVICE_REGISTERED("check_device_registered");
const QString OP_CHECK_UPLOAD_USER_DEVICE("check_upload_user_and_device");
const QString OP_DELETE_WHERE_KEY_NOT("delete_where_key_not");
const QString OP_END_UPLOAD("end_upload");
const QString OP_GET_EXTRA_STRINGS("get_extra_strings");
const QString OP_GET_ID_INFO("get_id_info");
const QString OP_REGISTER("register");
const QString OP_START_PRESERVATION("start_preservation");
const QString OP_START_UPLOAD("start_upload");
const QString OP_UPLOAD_TABLE("upload_table");
const QString OP_UPLOAD_RECORD("upload_record");
const QString OP_UPLOAD_EMPTY_TABLES("upload_empty_tables");
const QString OP_WHICH_KEYS_TO_SEND("which_keys_to_send");

// Notification text:
const QString PLEASE_REREGISTER(QObject::tr("Please re-register with the server."));


// ============================================================================
// NetworkManager
// ============================================================================

// CALLBACK LIFETIME SAFETY in this class:
// - There is only one NetworkManager in the whole app, owned by the
//   CamcopsApp.
// - The QNetworkAccessManager lives as long as the NetworkManager.
// - Therefore, any callbacks to this class are lifetime-safe and can use
//   std::bind.
// - HOWEVER, callbacks to something transient may not be (e.g. another object
//   sets up a callback to itself but with std::bind rather than to a QObject;
//   network function is called; object is deleted; network replies; boom).
//   So BEWARE there.
// - Since we have a single set of principal network access functions relating
//   to upload/server interaction, the simplest thing is to build them all into
//   this class, and then we don't have to worry about lifetime problems.


NetworkManager::NetworkManager(CamcopsApp& app,
                               const QSqlDatabase& db,
                               TaskFactoryPtr p_task_factory,
                               QWidget* parent) :
    m_app(app),
    m_db(db),
    m_p_task_factory(p_task_factory),
    m_parent(parent),
    m_offer_cancel(true),
    m_silent(parent == nullptr),
    m_logbox(nullptr),
    m_mgr(new QNetworkAccessManager(this))
{
}


NetworkManager::~NetworkManager()
{
    deleteLogBox();
}


// ============================================================================
// User interface
// ============================================================================

void NetworkManager::ensureLogBox()
{
    if (!m_logbox) {
        qDebug() << Q_FUNC_INFO << "creating logbox";
        m_logbox = new LogBox(m_parent, m_title, m_offer_cancel);
        m_logbox->setStyleSheet(
                    m_app.getSubstitutedCss(uiconst::CSS_CAMCOPS_MAIN));
        connect(m_logbox.data(), &LogBox::accepted,
                this, &NetworkManager::logboxFinished,
                Qt::UniqueConnection);
        connect(m_logbox.data(), &LogBox::rejected,
                this, &NetworkManager::logboxCancelled,
                Qt::UniqueConnection);
        m_logbox->open();
    }
}


void NetworkManager::deleteLogBox()
{
    if (!m_logbox) {
        return;
    }
    m_logbox->deleteLater();
    m_logbox = nullptr;
}


void NetworkManager::setSilent(bool silent)
{
    m_silent = silent;
}


void NetworkManager::setTitle(const QString& title)
{
    m_title = title;
    if (m_logbox) {
        m_logbox->setWindowTitle(title);
    }
}


void NetworkManager::statusMessage(const QString& msg)
{
    qInfo() << "Network:" << msg;
    if (m_silent) {
        qDebug() << Q_FUNC_INFO << "silent";
        return;
    }
    ensureLogBox();
    m_logbox->statusMessage(
                QString("%1: %2").arg(datetime::nowTimestamp()).arg(msg));
}


void NetworkManager::logboxCancelled()
{
    // User has hit cancel
    qDebug() << Q_FUNC_INFO;
    cleanup();
    deleteLogBox();
    emit cancelled();
}


void NetworkManager::logboxFinished()
{
    // User has acknowledged finish
    qDebug() << Q_FUNC_INFO;
    cleanup();
    deleteLogBox();
    emit finished();
}


// ============================================================================
// Basic connection management
// ============================================================================

void NetworkManager::disconnectManager()
{
    m_mgr->disconnect();
}


QNetworkRequest NetworkManager::createRequest(const QUrl& url,
                                              bool offer_cancel,
                                              bool ssl,
                                              bool ignore_ssl_errors,
                                              QSsl::SslProtocol ssl_protocol)
{
    // Clear any previous callbacks
    disconnectManager();

    m_offer_cancel = offer_cancel;

    QNetworkRequest request;

#ifdef DEBUG_NETWORK_REQUESTS
    qDebug().nospace().noquote()
            << Q_FUNC_INFO
            << ": offer_cancel=" << offer_cancel
            << ", ssl=" << ssl
            << ", ignore_ssl_errors=" << ignore_ssl_errors
            << ", ssl_protocol=" << convert::describeSslProtocol(ssl_protocol);
#endif

    if (ssl) {
        QSslConfiguration config = QSslConfiguration::defaultConfiguration();
        config.setProtocol(ssl_protocol);
        // NB the OpenSSL version must also support the protocol (e.g. TLSv2);
        // ... see also https://bugreports.qt.io/browse/QTBUG-31230
        // ... but TLSv2 working fine with manually compiled OpenSSL
        request.setSslConfiguration(config);
        if (ignore_ssl_errors) {
            QObject::connect(
                        m_mgr, &QNetworkAccessManager::sslErrors,
                        std::bind(&NetworkManager::sslIgnoringErrorHandler,
                                  this, std::placeholders::_1,
                                  std::placeholders::_2));

        }
    }

    // URL
    request.setUrl(url);

    return request;
}


QUrl NetworkManager::serverUrl(bool& success) const
{
    QUrl url;
#ifdef DEBUG_OFFER_HTTP_TO_SERVER
    url.setScheme(m_app.varBool(varconst::DEBUG_USE_HTTPS_TO_SERVER) ? "https"
                                                                     : "http");
#else
    url.setScheme("https");
#endif
    url.setHost(m_app.varString(varconst::SERVER_ADDRESS));
    url.setPort(m_app.varInt(varconst::SERVER_PORT));
    QString path = m_app.varString(varconst::SERVER_PATH);
    if (!path.startsWith('/')) {
        path = "/" + path;
    }
    url.setPath(path);
    success = !url.host().isEmpty();
    return url;
}


QString NetworkManager::serverUrlDisplayString() const
{
    bool success;
    QUrl url = serverUrl(success);
    QString str = url.toDisplayString();
    return str;
}


QNetworkRequest NetworkManager::createServerRequest(bool& success)
{
    QSsl::SslProtocol ssl_protocol = convert::sslProtocolFromDescription(
                m_app.varString(varconst::SSL_PROTOCOL));
    return createRequest(
                serverUrl(success),
                true,  // always offer cancel
                true,  // always use SSL
                !m_app.varBool(varconst::VALIDATE_SSL_CERTIFICATES),  // ignore SSL errors?
                ssl_protocol);
}


void NetworkManager::serverPost(Dict dict, ReplyFuncPtr reply_func,
                                bool include_user)
{
    // Request (URL, SSL, etc.).
    bool success = true;
    QNetworkRequest request = createServerRequest(success);
    if (!success) {
        statusMessage(tr("Server host details not specified; see Settings"));
        fail();
        return;
    }

    // Complete the dictionary
    // dict[KEY_CAMCOPS_VERSION] = camcopsversion::CAMCOPS_VERSION.toFloatString();  // outdated
    dict[KEY_CAMCOPS_VERSION] = camcopsversion::CAMCOPS_VERSION.toString();  // server copes as of v2.0.0
    dict[KEY_DEVICE] = m_app.deviceId();
    if (include_user) {
        QString user = m_app.varString(varconst::SERVER_USERNAME);
        if (user.isEmpty()) {
            statusMessage(tr("User information required but you have not yet "
                             "specified it; see Settings"));
            fail();
            return;
        }
        dict[KEY_USER] = user;

        if (!ensurePasswordKnown()) {
            statusMessage(tr("Password not specified"));
            fail();
            return;
        }
        dict[KEY_PASSWORD] = m_tmp_password;
    }
    if (!m_tmp_session_id.isEmpty() && !m_tmp_session_token.isEmpty()) {
        dict[KEY_SESSION_ID] = m_tmp_session_id;
        dict[KEY_SESSION_TOKEN] = m_tmp_session_token;
    }

    // Clean up the reply storage objects
    m_reply_data.clear();
    m_reply_dict.clear();

    // Connect up the reply signals
    QObject::connect(m_mgr, &QNetworkAccessManager::finished,
                     this, reply_func);

    // Send the request
    QUrlQuery postdata = convert::getPostDataAsUrlQuery(dict);
    request.setHeader(QNetworkRequest::ContentTypeHeader,
                      "application/x-www-form-urlencoded");
    QByteArray final_data = postdata.toString(QUrl::FullyEncoded).toUtf8();
    // See discussion of encoding in Convert::getPostDataAsUrlQuery
#ifdef DEBUG_NETWORK_REQUESTS
    qDebug() << "Request to server: " << final_data;
#endif
    statusMessage("... sending " + sizeBytes(final_data.length()));
    m_mgr->post(request, final_data);
}


bool NetworkManager::processServerReply(QNetworkReply* reply)
{
    if (!reply) {
        statusMessage("Bug: null pointer to processServerReply");
        fail();
        return false;
    }
    reply->deleteLater();
    if (reply->error() == QNetworkReply::NoError) {
        m_reply_data = reply->readAll();  // can probably do this only once
        statusMessage("... received " + sizeBytes(m_reply_data.length()));
#ifdef DEBUG_NETWORK_REPLIES
        qDebug() << "Network reply (raw): " << m_reply_data;
#endif
        m_reply_dict = convert::getReplyDict(m_reply_data);
#ifdef DEBUG_NETWORK_REPLIES
        qInfo() << "Network reply (dictionary): " << m_reply_dict;
#endif
        m_tmp_session_id = m_reply_dict[KEY_SESSION_ID];
        m_tmp_session_token = m_reply_dict[KEY_SESSION_TOKEN];
        if (replyReportsSuccess()) {
            return true;
        } else {
            // If the server's reporting success=0, it should provide an
            // error too:
            statusMessage("Server reported an error: " +
                          m_reply_dict[KEY_ERROR]);
            fail();
            return false;
        }
    } else {
        statusMessage("Network failure: " + reply->errorString());
        fail();
        return false;
    }
}


QString NetworkManager::sizeBytes(qint64 size)
{
    return convert::prettySize(size, true, false, true, "bytes");
}


bool NetworkManager::replyReportsSuccess()
{
    return m_reply_dict[KEY_SUCCESS].toInt();
}


RecordList NetworkManager::getRecordList()
{
    RecordList recordlist;

    if (!m_reply_dict.contains(KEY_NRECORDS) ||
            !m_reply_dict.contains(KEY_NFIELDS) ||
            !m_reply_dict.contains(KEY_FIELDS)) {
        statusMessage("ERROR: missing field or record information");
        return RecordList();
    }

    int nrecords = m_reply_dict[KEY_NRECORDS].toInt();
    if (nrecords <= 0) {
        statusMessage("ERROR: No records");
        return RecordList();
    }

    int nfields = m_reply_dict[KEY_NFIELDS].toInt();
    QString fields = m_reply_dict[KEY_FIELDS];
    QStringList fieldnames = fields.split(',');
    if (nfields != fieldnames.length()) {
        statusMessage(
            QString("WARNING: nfields (%1) doesn't match number of actual "
                    "fields (%2); field list is: %3")
                    .arg(nfields)
                    .arg(fieldnames.length())
                    .arg(fields));
        nfields = fieldnames.length();
    }
    if (nfields <= 0) {
        statusMessage("ERROR: No fields");
        return RecordList();
    }
    for (int r = 0; r < nrecords; ++r) {
        QMap<QString, QVariant> record;
        QString recordname = KEYSPEC_RECORD.arg(r);
        if (!m_reply_dict.contains(recordname)) {
            statusMessage("ERROR: missing record " + recordname);
            return RecordList();
        }
        QString valuelist = m_reply_dict[recordname];
        QVector<QVariant> values = convert::csvSqlLiteralsToValues(valuelist);
        if (values.length() != nfields) {
            statusMessage("ERROR: #values not equal to #fields");
            return RecordList();
        }
        for (int f = 0; f < nfields; ++f) {
            record[fieldnames[f]] = values[f];
        }
        recordlist.push_back(record);
    }
    return recordlist;
}


bool NetworkManager::ensurePasswordKnown()
{
    if (!m_tmp_password.isEmpty()) {
        // We already have it, from whatever source
        return true;
    }
    if (m_app.storingServerPassword()) {
        m_tmp_password = m_app.getPlaintextServerPassword();
        if (!m_tmp_password.isEmpty()) {
            return true;
        }
    }
    // If we get here, either we're not storing the password or it hasn't been
    // entered.
    QString text = QString(tr("Enter password for user <b>%1</b> on "
                              "server %2"))
            .arg(m_app.varString(varconst::SERVER_USERNAME),
                 serverUrlDisplayString());
    QString title = tr("Enter server password");
    QWidget* parent = m_logbox ? m_logbox : m_parent;
    PasswordEntryDialog dlg(text, title, parent);
    int reply = dlg.exec();
    if (reply != QDialog::Accepted) {
        return false;
    }
    // fetch/write back password
    m_tmp_password = dlg.password();
    return true;
}


void NetworkManager::cleanup()
{
    disconnectManager();
    m_tmp_password = "";
    m_tmp_session_id = "";
    m_tmp_session_token = "";
    m_reply_data.clear();
    m_reply_dict.clear();

    m_upload_next_stage = NextUploadStage::Invalid;
    m_upload_patient_ids_to_move_off.clear();
    m_upload_empty_tables.clear();
    m_upload_tables_to_send_whole.clear();
    m_upload_tables_to_send_recordwise.clear();
    m_upload_recordwise_table_in_progress = "";
    m_upload_recordwise_fieldnames.clear();
    m_upload_n_records = 0;
    m_upload_current_record_index = -1;
    m_upload_recordwise_pks_to_send.clear();
    m_upload_tables_to_wipe.clear();
}


void NetworkManager::sslIgnoringErrorHandler(QNetworkReply* reply,
                                             const QList<QSslError> & errlist)
{
    // Error handle that ignores SSL certificate errors and continues
    statusMessage(QString("+++ Ignoring %1 SSL error(s):").arg(errlist.length()));
    for (auto err : errlist) {
        statusMessage("    " + err.errorString());
    }
    reply->ignoreSslErrors();
}


void NetworkManager::cancel()
{
    qDebug() << Q_FUNC_INFO;
    cleanup();
    if (m_logbox) {
        m_logbox->reject();  // its rejected() signal calls our logboxCancelled()
    } else {
        emit cancelled();
    }
}


void NetworkManager::fail()
{
    finish(false);
}


void NetworkManager::succeed()
{
    finish(true);
}


void NetworkManager::finish(bool success)
{
    qDebug() << Q_FUNC_INFO;
    cleanup();
    if (m_logbox) {
        m_logbox->finish(success);  // its signals call our logboxCancelled() or logboxFinished()
    } else {
        if (success) {
            emit finished();
        } else {
            emit cancelled();
        }
    }
}



// ============================================================================
// Testing
// ============================================================================

void NetworkManager::testHttpGet(const QString& url, bool offer_cancel)
{
    QNetworkRequest request = createRequest(QUrl(url), offer_cancel,
                                            false, false);
    statusMessage("Testing HTTP GET connection to: " + url);
    // Safe object lifespan signal: can use std::bind
    QObject::connect(m_mgr, &QNetworkAccessManager::finished,
                     std::bind(&NetworkManager::testReplyFinished,
                               this, std::placeholders::_1));
    // GET
    m_mgr->get(request);
    statusMessage("... sent request to: " + url);
}


void NetworkManager::testHttpsGet(const QString& url, bool offer_cancel,
                                  bool ignore_ssl_errors)
{
    QNetworkRequest request = createRequest(QUrl(url), offer_cancel,
                                            true, ignore_ssl_errors,
                                            QSsl::AnyProtocol);
    statusMessage("Testing HTTPS GET connection to: " + url);
    // Safe object lifespan signal: can use std::bind
    QObject::connect(m_mgr, &QNetworkAccessManager::finished,
                     std::bind(&NetworkManager::testReplyFinished, this,
                               std::placeholders::_1));
    // Note: the reply callback arrives on the main (GUI) thread.
    // GET
    m_mgr->get(request);
    statusMessage("... sent request to: " + url);
}


void NetworkManager::testReplyFinished(QNetworkReply* reply)
{
    if (reply->error() == QNetworkReply::NoError) {
        statusMessage("Result:");
        statusMessage(reply->readAll());
    } else {
        statusMessage("Network error: " + reply->errorString());
    }
    reply->deleteLater();  // http://doc.qt.io/qt-5/qnetworkaccessmanager.html#details
    finish();
}


// ============================================================================
// Server registration
// ============================================================================

void NetworkManager::registerWithServer()
{
    statusMessage("Registering with " + serverUrlDisplayString());
    Dict dict;
    dict[KEY_OPERATION] = OP_REGISTER;
    dict[KEY_DEVICE_FRIENDLY_NAME] = m_app.varString(varconst::DEVICE_FRIENDLY_NAME);
    serverPost(dict, &NetworkManager::registerSub1);
}


void NetworkManager::registerSub1(QNetworkReply* reply)
{
    if (!processServerReply(reply)) {
        return;
    }
    statusMessage("... registered and received identification information");
    storeServerIdentificationInfo();

    statusMessage("Requesting extra strings");
    Dict dict;
    dict[KEY_OPERATION] = OP_GET_EXTRA_STRINGS;
    serverPost(dict, &NetworkManager::registerSub2);
}


void NetworkManager::registerSub2(QNetworkReply *reply)
{
    if (!processServerReply(reply)) {
        return;
    }
    statusMessage("... received extra strings");
    storeExtraStrings();
    succeed();
}


void NetworkManager::fetchIdDescriptions()
{
    statusMessage("Getting ID info from " + serverUrlDisplayString());
    Dict dict;
    dict[KEY_OPERATION] = OP_GET_ID_INFO;
    serverPost(dict, &NetworkManager::fetchIdDescriptionsSub1);
}


void NetworkManager::fetchIdDescriptionsSub1(QNetworkReply* reply)
{
    if (!processServerReply(reply)) {
        return;
    }
    statusMessage("... registered and received identification information");
    storeServerIdentificationInfo();
    succeed();
}


void NetworkManager::fetchExtraStrings()
{
    statusMessage("Getting extra strings from " + serverUrlDisplayString());
    Dict dict;
    dict[KEY_OPERATION] = OP_GET_EXTRA_STRINGS;
    serverPost(dict, &NetworkManager::fetchExtraStringsSub1);
}


void NetworkManager::fetchExtraStringsSub1(QNetworkReply* reply)
{
    if (!processServerReply(reply)) {
        return;
    }
    statusMessage("... received extra strings");
    storeExtraStrings();
    succeed();
}


void NetworkManager::storeServerIdentificationInfo()
{
    m_app.setVar(varconst::SERVER_DATABASE_TITLE, m_reply_dict[KEY_DATABASE_TITLE]);
    m_app.setVar(varconst::SERVER_CAMCOPS_VERSION, m_reply_dict[KEY_SERVER_CAMCOPS_VERSION]);
    m_app.setVar(varconst::ID_POLICY_UPLOAD, m_reply_dict[KEY_ID_POLICY_UPLOAD]);
    m_app.setVar(varconst::ID_POLICY_FINALIZE, m_reply_dict[KEY_ID_POLICY_FINALIZE]);
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        QString key_desc = KEYSPEC_ID_DESCRIPTION.arg(n);
        QString key_shortdesc = KEYSPEC_ID_SHORT_DESCRIPTION.arg(n);
        QString varname_desc = dbconst::IDDESC_FIELD_FORMAT.arg(n);
        QString varname_shortdesc = dbconst::IDSHORTDESC_FIELD_FORMAT.arg(n);
        m_app.setVar(varname_desc, m_reply_dict[key_desc]);
        m_app.setVar(varname_shortdesc, m_reply_dict[key_shortdesc]);
    }

    m_app.setVar(varconst::LAST_SERVER_REGISTRATION, datetime::now());

    // Deselect patient, or its description text may be out of date
    m_app.deselectPatient();
}


void NetworkManager::storeExtraStrings()
{
    RecordList recordlist = getRecordList();
    if (!recordlist.isEmpty()) {
        m_app.setAllExtraStrings(recordlist);
        statusMessage(QString("Saved %1 extra strings").arg(recordlist.length()));
    }
}


// ============================================================================
// Upload
// ============================================================================

void NetworkManager::upload(UploadMethod method)
{
    statusMessage(tr("Preparing to upload to: ") + serverUrlDisplayString());
    // ... in part so uploadNext() status message looks OK

    // The GUI doesn't get a chance to respond until after this function
    // has completed.
    // SlowGuiGuard guard();  // not helpful

    m_app.processEvents();  // these, scattered around, are very helpful.

    cleanup();
    m_upload_method = method;

    // Offline things first:
    if (!isPatientInfoComplete()) {
        fail();
        return;
    }
    m_app.processEvents();
    if (!pruneDeadBlobs()) {
        fail();
        return;
    }
    m_app.processEvents();
    if (!applyPatientMoveOffTabletFlagsToTasks()) {
        fail();
        return;
    }
    m_app.processEvents();
    if (!writeIdDescriptionsToPatientTable()) {
        fail();
        return;
    }
    m_app.processEvents();
    catalogueTablesForUpload();
    m_app.processEvents();

    // Begin comms with the server by checking device is registered.
    checkDeviceRegistered();
    m_upload_next_stage = NextUploadStage::CheckUser;
}


bool NetworkManager::isPatientInfoComplete()
{
    statusMessage("Checking patient information sufficiently complete");

    Patient specimen_patient(m_app, m_db);
    SqlArgs sqlargs = specimen_patient.fetchQuerySql();
    QSqlQuery query(m_db);
    if (!dbfunc::execQuery(query, sqlargs)) {
        queryFail(sqlargs.sql);
        return false;
    }
    int nfailures_upload = 0;
    int nfailures_finalize = 0;
    int nfailures_clash = 0;
    while (query.next()) {
        Patient patient(m_app, m_db);
        patient.setFromQuery(query, true);
        if (!patient.compliesWithUpload()) {
            ++nfailures_upload;
        }
        if (!patient.compliesWithFinalize()) {
            ++nfailures_finalize;
        }
        if (patient.anyIdClash()) {
            // not the most efficient; COUNT DISTINCT...
            // However, this gives us the number of patients clashing.
            ++nfailures_clash;
        }
        if (m_upload_method != UploadMethod::Move &&
                patient.shouldMoveOffTablet()) {
            m_upload_patient_ids_to_move_off.append(patient.pkvalue().toInt());
        }
    }
    if (nfailures_clash > 0) {
        statusMessage(QString("Failure: %1 patient(s) having clashing ID "
                              "numbers")
                      .arg(nfailures_clash));
        return false;
    }
    if (m_upload_method == UploadMethod::Copy && nfailures_upload > 0) {
        // Copying; we're allowed not to meet the finalizing requirements,
        // but we must meet the uploading requirements
        statusMessage(QString("Failure: %1 patient(s) do not meet the "
                              "server's upload ID policy of: %2")
                      .arg(nfailures_upload)
                      .arg(m_app.uploadPolicy().pretty()));
        return false;
    }
    if (m_upload_method != UploadMethod::Copy &&
            (nfailures_upload + nfailures_finalize) > 0) {
        // Finalizing; must meet all requirements
        statusMessage(QString(
            "Failure: %1 patient(s) do not meet the server's upload ID policy "
            "[%2]; %3 patient(s) do not meet the its finalize ID policy [%4]")
                      .arg(nfailures_upload)
                      .arg(m_app.uploadPolicy().pretty())
                      .arg(nfailures_finalize)
                      .arg(m_app.finalizePolicy().pretty()));
        return false;
    }
    return true;
}


bool NetworkManager::applyPatientMoveOffTabletFlagsToTasks()
{
    // If we were uploading, we need to undo our move-off flags (in case the
    // user changes their mind about a patient)
    // We could use a system of "set before upload, clear afterwards".
    // However, failing to clear (for some reason) is a risk.
    // Therefore, we set and clear flags here, for all tables.
    // That is, we make sure these flags are all correct immediately before
    // an upload (which is when we care).

    if (m_upload_method != UploadMethod::Copy) {
        // if we're not using UploadMethod::Copy, everything is going to be
        // moved anyway, by virtue of startPreservation()
        return false;
    }

    statusMessage("Setting move-off flags for tasks, where applicable");

    DbTransaction trans(m_db);

    // ========================================================================
    // Step 1: clear all move-off flags, except in the source tables (being:
    // patient tables and anonymous task primary tables).
    // ========================================================================
    for (auto specimen : m_p_task_factory->allSpecimens()) {
        if (specimen->isAnonymous()) {
            // anonymous task: clear the ancillary tables
            for (auto tablename : specimen->ancillaryTables()) {
                if (!clearMoveOffTabletFlag(tablename)) {
                    queryFailClearingMoveOffFlag(tablename);
                    return false;
                }
            }
        } else {
            // task with patient: clear all tables
            for (auto tablename : specimen->allTables()) {
                if (!clearMoveOffTabletFlag(tablename)) {
                    queryFailClearingMoveOffFlag(tablename);
                    return false;
                }
            }
        }
    }
    // Clear all flags for BLOBs
    if (!clearMoveOffTabletFlag(Blob::TABLENAME)) {
        queryFailClearingMoveOffFlag(Blob::TABLENAME);
        return false;
    }

    // ========================================================================
    // Step 2: Apply flags from patients to their tasks/ancillary tables.
    // ========================================================================
    // m_upload_patient_ids_to_move_off has been precalculated for efficiency

    int n_patients = m_upload_patient_ids_to_move_off.length();
    if (n_patients > 0) {
        QString pt_paramholders = dbfunc::sqlParamHolders(n_patients);
        ArgList pt_args = dbfunc::argListFromIntList(m_upload_patient_ids_to_move_off);
        // Maximum length of an SQL statement: lots
        // https://www.sqlite.org/limits.html
        QString sql;

        for (auto specimen : m_p_task_factory->allSpecimens()) {
            if (specimen->isAnonymous()) {
                continue;
            }
            QString main_tablename = specimen->tablename();
            // (a) main table, with FK to patient
            sql = QString("UPDATE %1 SET %2 = 1 WHERE %3 IN (%4)")
                    .arg(delimit(main_tablename),
                         delimit(dbconst::MOVE_OFF_TABLET_FIELDNAME),
                         delimit(Task::PATIENT_FK_FIELDNAME),
                         pt_paramholders);
            if (!dbfunc::exec(m_db, sql, pt_args)) {
                queryFail(sql);
                return false;
            }
            // (b) ancillary tables
            QStringList ancillary_tables = specimen->ancillaryTables();
            if (ancillary_tables.isEmpty()) {
                // no ancillary tables
                continue;
            }
            WhereConditions where;
            where[dbconst::MOVE_OFF_TABLET_FIELDNAME] = 1;
            QVector<int> task_pks = dbfunc::getSingleFieldAsIntList(
                        m_db, main_tablename, dbconst::PK_FIELDNAME, where);
            if (task_pks.isEmpty()) {
                // no tasks to be moved off
                continue;
            }
            QString fk_task_fieldname = specimen->ancillaryTableFKToTaskFieldname();
            if (fk_task_fieldname.isEmpty()) {
                uifunc::stopApp(QString(
                    "Task %1 has ancillary tables but "
                    "ancillaryTableFKToTaskFieldname() returns empty")
                                .arg(main_tablename));
            }
            QString task_paramholders = dbfunc::sqlParamHolders(task_pks.length());
            ArgList task_args = dbfunc::argListFromIntList(task_pks);
            for (auto ancillary_table : ancillary_tables) {
                sql = QString("UPDATE %1 SET %2 = 1 WHERE %3 IN (%4)")
                        .arg(delimit(ancillary_table),
                             delimit(dbconst::MOVE_OFF_TABLET_FIELDNAME),
                             delimit(fk_task_fieldname),
                             task_paramholders);
                if (!dbfunc::exec(m_db, sql, task_args)) {
                    queryFail(sql);
                    return false;
                }
            }
        }
    }

    // ========================================================================
    // Step 3: Apply flags from anonymous tasks to their ancillary tables.
    // ========================================================================

    for (auto specimen : m_p_task_factory->allSpecimens()) {
        if (!specimen->isAnonymous()) {
            continue;
        }
        QString main_tablename = specimen->tablename();
        QStringList ancillary_tables = specimen->ancillaryTables();
        if (ancillary_tables.isEmpty()) {
            continue;
        }
        // Get PKs of all anonymous tasks being moved off
        WhereConditions where;
        where[dbconst::MOVE_OFF_TABLET_FIELDNAME] = 1;
        QVector<int> task_pks = dbfunc::getSingleFieldAsIntList(
                    m_db, main_tablename, dbconst::PK_FIELDNAME, where);
        if (task_pks.isEmpty()) {
            // no tasks to be moved off
            continue;
        }
        QString fk_task_fieldname = specimen->ancillaryTableFKToTaskFieldname();
        if (fk_task_fieldname.isEmpty()) {
            uifunc::stopApp(QString(
                "Task %1 has ancillary tables but "
                "ancillaryTableFKToTaskFieldname() returns empty")
                            .arg(main_tablename));
        }
        QString task_paramholders = dbfunc::sqlParamHolders(task_pks.length());
        ArgList task_args = dbfunc::argListFromIntList(task_pks);
        for (auto ancillary_table : ancillary_tables) {
            QString sql = QString("UPDATE %1 SET %2 = 1 WHERE %3 IN (%4)")
                    .arg(delimit(ancillary_table),
                         delimit(dbconst::MOVE_OFF_TABLET_FIELDNAME),
                         delimit(fk_task_fieldname),
                         task_paramholders);
            if (!dbfunc::exec(m_db, sql, task_args)) {
                queryFail(sql);
                return false;
            }
        }
    }

    // ========================================================================
    // Step 4. BLOB table.
    // ========================================================================
    // Options here are:
    // - iterate through every task (and ancillary table), loading them from
    //   SQL to C++, and asking each what BLOB IDs they possess;
    // - store patient_id (or NULL) with each BLOB;
    // - iterate through each BLOB, looking for the move-off flag on the
    //   associated task/ancillary record.
    // The most efficient and simple is likely to be (3).

    // (a) For every BLOB...
    QString sql = dbfunc::selectColumns(QStringList{dbconst::PK_FIELDNAME,
                                                    Blob::SRC_TABLE_FIELDNAME,
                                                    Blob::SRC_PK_FIELDNAME},
                                        Blob::TABLENAME);
    QSqlQuery query(m_db);
    if (!dbfunc::execQuery(query, sql)) {
        queryFail(sql);
        return false;
    }
    while (query.next()) {
        // (b) find the table/PK of the linked task (or other table)
        int blob_pk = query.value(0).toInt();
        QString src_table = query.value(1).toString();
        int src_pk = query.value(2).toInt();

        // (c) find the move-off flag for that linked task
        SqlArgs sub1_sqlargs(
                    dbfunc::selectColumns(
                        QStringList{dbconst::MOVE_OFF_TABLET_FIELDNAME},
                        src_table));
        WhereConditions sub1_where{{dbconst::PK_FIELDNAME, src_pk}};
        dbfunc::addWhereClause(sub1_where, sub1_sqlargs);
        int move_off_int = dbfunc::dbFetchInt(m_db, sub1_sqlargs, -1);
        if (move_off_int == -1) {
            // No records matching
            qWarning().nospace()
                    << "BLOB refers to "
                    << src_table
                    << "."
                    << dbconst::PK_FIELDNAME
                    << " = "
                    << src_pk
                    << " but record doesn't exist!";
            continue;
        }
        if (move_off_int == 0) {
            // Record exists; task not marked for move-off
            continue;
        }

        // (d) set the BLOB's move-off flag
        UpdateValues update_values{{dbconst::MOVE_OFF_TABLET_FIELDNAME, true}};
        SqlArgs sub2_sqlargs = dbfunc::updateColumns(update_values, Blob::TABLENAME);
        WhereConditions sub2_where{{dbconst::PK_FIELDNAME, blob_pk}};
        dbfunc::addWhereClause(sub2_where, sub2_sqlargs);
        if (!dbfunc::exec(m_db, sub2_sqlargs)) {
            queryFail(sub2_sqlargs.sql);
            return false;
        }
    }
    return true;
}


bool NetworkManager::writeIdDescriptionsToPatientTable()
{
    statusMessage("Writing ID descriptions to patient table for upload");
    QStringList assignments;
    ArgList args;
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        assignments.append(
                    delimit(dbconst::IDDESC_FIELD_FORMAT.arg(n)) + "=?");
        args.append(m_app.idDescription(n));
        assignments.append(
                    delimit(dbconst::IDSHORTDESC_FIELD_FORMAT.arg(n)) + "=?");
        args.append(m_app.idShortDescription(n));
    }
    QString sql = QString("UPDATE %1 SET %2")
            .arg(delimit(Patient::TABLENAME),
                 assignments.join(", "));
    if (!dbfunc::exec(m_db, sql, args)) {
        queryFail(sql);
        return false;
    }
    return true;
}


void NetworkManager::catalogueTablesForUpload()
{
    statusMessage("Cataloguing tables for upload");
    QStringList recordwise_tables{Blob::TABLENAME};
    QStringList patient_tables{Patient::TABLENAME};
    QStringList all_tables = dbfunc::getAllTables(m_db);
    for (auto table : all_tables) {
        // How to upload?
        if (dbfunc::count(m_db, table) == 0) {
            m_upload_empty_tables.append(table);
        } else if (recordwise_tables.contains(table)) {
            m_upload_tables_to_send_recordwise.append(table);
        } else {
            m_upload_tables_to_send_whole.append(table);
        }

        // Whether to clear afterwards?
        switch (m_upload_method) {
        case UploadMethod::Copy:
        default:
            break;
        case UploadMethod::MoveKeepingPatients:
            if (!patient_tables.contains(table)) {
                m_upload_tables_to_wipe.append(table);
            }
            break;
        case UploadMethod::Move:
            m_upload_tables_to_wipe.append(table);
            break;
        }
    }
}


void NetworkManager::checkDeviceRegistered()
{
    statusMessage("Checking device is registered with server");
    Dict dict;
    dict[KEY_OPERATION] = OP_CHECK_DEVICE_REGISTERED;
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::uploadNext(QNetworkReply* reply)
{
    // This function imposes an order on the upload sequence, which makes
    // everything else work.

    if (!processServerReply(reply) ||
            m_upload_next_stage == NextUploadStage::Invalid) {
        // stage might be Invalid if user hit cancel while messages still
        // inbound
        return;
    }
    statusMessage("... OK");

    switch (m_upload_next_stage) {

    case NextUploadStage::CheckUser:
        checkUploadUser();
        m_upload_next_stage = NextUploadStage::FetchPolicies;
        break;

    case NextUploadStage::FetchPolicies:
        uploadFetchServerIdInfo();
        m_upload_next_stage = NextUploadStage::CheckPoliciesThenStartUpload;
        break;

    case NextUploadStage::CheckPoliciesThenStartUpload:
        if (!isServerVersionOK() || !arePoliciesOK() || !areDescriptionsOK()) {
            fail();
            return;
        }
        startUpload();
        if (m_upload_method == UploadMethod::Copy) {
            // If we copy, we proceed to uploading
            m_upload_next_stage = NextUploadStage::Uploading;
        } else {
            // If we're moving, we preserve records.
            m_upload_next_stage = NextUploadStage::StartPreservation;
        }
        break;

    case NextUploadStage::StartPreservation:
        startPreservation();
        m_upload_next_stage = NextUploadStage::Uploading;
        break;

    case NextUploadStage::Uploading:
        if (!m_upload_empty_tables.isEmpty()) {

            sendEmptyTables(m_upload_empty_tables);
            m_upload_empty_tables.clear();

        } else if (!m_upload_tables_to_send_whole.isEmpty()) {

            QString table = m_upload_tables_to_send_whole.front();
            m_upload_tables_to_send_whole.pop_front();
            sendTableWhole(table);

        } else if (!m_upload_recordwise_pks_to_send.isEmpty()) {

            sendNextRecord();

        } else if (!m_upload_tables_to_send_recordwise.isEmpty()) {

            QString table = m_upload_tables_to_send_recordwise.front();
            m_upload_tables_to_send_recordwise.pop_front();
            sendTableRecordwise(table);

        } else {

            endUpload();
            m_upload_next_stage = NextUploadStage::Finished;

        }
        break;

    case NextUploadStage::Finished:
        // All done successfully
        wipeTables();
        statusMessage("Finished");
        m_app.setNeedsUpload(false);
        succeed();
        break;

    default:
        uifunc::stopApp("Bug: unknown m_upload_next_stage");
        break;
    }
}


void NetworkManager::checkUploadUser()
{
    statusMessage("Checking user/device permitted to upload");
    Dict dict;
    dict[KEY_OPERATION] = OP_CHECK_UPLOAD_USER_DEVICE;
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::uploadFetchServerIdInfo()
{
    statusMessage("Fetching server's version/ID policies/ID descriptions");
    Dict dict;
    dict[KEY_OPERATION] = OP_GET_ID_INFO;
    serverPost(dict, &NetworkManager::uploadNext);
}


bool NetworkManager::isServerVersionOK()
{
    statusMessage("Checking server CamCOPS version");
    QString server_version_str = m_reply_dict[KEY_SERVER_CAMCOPS_VERSION];
    Version server_version(server_version_str);
    bool ok = server_version >= camcopsversion::MINIMUM_SERVER_VERSION;
    if (ok) {
        statusMessage("... OK");
    } else {
        statusMessage(QString("Server CamCOPS version (%1) is too old; must "
                              "be >= %2")
                      .arg(server_version_str,
                           camcopsversion::MINIMUM_SERVER_VERSION.toString()));
    }
    return ok;
}


bool NetworkManager::arePoliciesOK()
{
    statusMessage("Checking ID policies match server");
    QString local_upload = m_app.uploadPolicy().pretty();
    QString local_finalize = m_app.finalizePolicy().pretty();
    QString server_upload = IdPolicy(m_reply_dict[KEY_ID_POLICY_UPLOAD]).pretty();
    QString server_finalize = IdPolicy(m_reply_dict[KEY_ID_POLICY_FINALIZE]).pretty();
    bool ok = true;
    if (local_upload != server_upload) {
        statusMessage(QString("Local upload policy [%1] doesn't match "
                              "server's [%2]. ")
                      .arg(local_upload,
                           server_upload) + PLEASE_REREGISTER);
        ok = false;
    }
    if (local_finalize != server_finalize) {
        statusMessage(QString("Local finalize policy [%1] doesn't match "
                              "server's [%2]. ")
                      .arg(local_finalize,
                           server_finalize) + PLEASE_REREGISTER);
        ok = false;
    }
    if (ok) {
        statusMessage("... OK");
    }
    return ok;
}


bool NetworkManager::areDescriptionsOK()
{
    statusMessage("Checking ID descriptions match server");
    bool ok = true;
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        QString key_desc = KEYSPEC_ID_DESCRIPTION.arg(n);
        QString key_shortdesc = KEYSPEC_ID_SHORT_DESCRIPTION.arg(n);
        QString varname_desc = dbconst::IDDESC_FIELD_FORMAT.arg(n);
        QString varname_shortdesc = dbconst::IDSHORTDESC_FIELD_FORMAT.arg(n);
        QString local_desc = m_app.varString(varname_desc);
        QString local_shortdesc = m_app.varString(varname_shortdesc);
        QString server_desc = m_reply_dict[key_desc];
        QString server_shortdesc = m_reply_dict[key_shortdesc];
        ok = ok && local_desc == server_desc && local_shortdesc == server_shortdesc;
    }
    if (ok) {
        statusMessage("... OK");
    } else {
        statusMessage("Descriptions do not match! " + PLEASE_REREGISTER);
    }
    return ok;
}


void NetworkManager::startUpload()
{
    statusMessage("Starting upload");
    Dict dict;
    dict[KEY_OPERATION] = OP_START_UPLOAD;
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::startPreservation()
{
    statusMessage("Starting preservation");
    Dict dict;
    dict[KEY_OPERATION] = OP_START_PRESERVATION;
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::sendEmptyTables(const QStringList& tablenames)
{
    statusMessage(tr("Uploading empty tables: ") + tablenames.join(", "));
    Dict dict;
    dict[KEY_OPERATION] = OP_UPLOAD_EMPTY_TABLES;
    dict[KEY_TABLES] = tablenames.join(",");
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::sendTableWhole(const QString& tablename)
{
    statusMessage(tr("Uploading table: ") + tablename);
    Dict dict;
    dict[KEY_OPERATION] = OP_UPLOAD_TABLE;
    dict[KEY_TABLE] = tablename;
    QStringList fieldnames = dbfunc::getFieldNames(m_db, tablename);
    dict[KEY_FIELDS] = fieldnames.join(",");
    QString sql = dbfunc::selectColumns(fieldnames, tablename);
    QSqlQuery query(m_db);
    if (!dbfunc::execQuery(query, sql)) {
        queryFail(sql);
        return;
    }
    int record = 0;
    while (query.next()) {
        dict[KEYSPEC_RECORD.arg(record)] = dbfunc::csvRow(query);
        ++record;
    }
    dict[KEY_NRECORDS] = QString::number(record);
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::sendTableRecordwise(const QString& tablename)
{
    statusMessage(tr("Preparing to send table (recordwise): ") + tablename);

    m_upload_recordwise_table_in_progress = tablename;
    m_upload_recordwise_fieldnames = dbfunc::getFieldNames(m_db, tablename);
    m_upload_recordwise_pks_to_send = dbfunc::getPKs(m_db, tablename,
                                                     dbconst::PK_FIELDNAME);
    m_upload_n_records = m_upload_recordwise_pks_to_send.length();
    m_upload_current_record_index = 0;

    // First, DELETE WHERE pk NOT...
    QString pkvalues;
    for (int i = 0; i < m_upload_recordwise_pks_to_send.length(); ++i) {
        if (i > 0) {
            pkvalues += ",";
        }
        pkvalues += QString::number(m_upload_recordwise_pks_to_send.at(i));
    }
    Dict dict;
    dict[KEY_OPERATION] = OP_DELETE_WHERE_KEY_NOT;
    dict[KEY_TABLE] = tablename;
    dict[KEY_PKNAME] = dbconst::PK_FIELDNAME;
    dict[KEY_PKVALUES] = pkvalues;
    statusMessage("Sending delete-where-key-not message");
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::sendNextRecord()
{
    ++m_upload_current_record_index;
    statusMessage(QString("Uploading table %1, record %2/%3")
                  .arg(m_upload_recordwise_table_in_progress)
                  .arg(m_upload_current_record_index)
                  .arg(m_upload_n_records));
    int pk = m_upload_recordwise_pks_to_send.front();
    m_upload_recordwise_pks_to_send.pop_front();

    SqlArgs sqlargs(dbfunc::selectColumns(
                        m_upload_recordwise_fieldnames,
                        m_upload_recordwise_table_in_progress));
    WhereConditions where;
    where[dbconst::PK_FIELDNAME] = pk;
    dbfunc::addWhereClause(where, sqlargs);
    QSqlQuery query(m_db);
    if (!dbfunc::execQuery(query, sqlargs) || !query.next()) {
        queryFail(sqlargs.sql);
        return;
    }
    QString values = dbfunc::csvRow(query);

    Dict dict;
    dict[KEY_OPERATION] = OP_UPLOAD_RECORD;
    dict[KEY_TABLE] = m_upload_recordwise_table_in_progress;
    dict[KEY_FIELDS] = m_upload_recordwise_fieldnames.join(",");
    dict[KEY_PKNAME] = dbconst::PK_FIELDNAME;
    dict[KEY_VALUES] = values;
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::endUpload()
{
    statusMessage("Finishing upload");
    Dict dict;
    dict[KEY_OPERATION] = OP_END_UPLOAD;
    serverPost(dict, &NetworkManager::uploadNext);
}


void NetworkManager::wipeTables()
{
    DbTransaction trans(m_db);

    // Plain wipes
    for (auto wipe_table : m_upload_tables_to_wipe) {
        statusMessage(tr("Wiping table: ") + wipe_table);
        if (!dbfunc::deleteFrom(m_db, wipe_table)) {
            statusMessage(tr("... failed to delete!"));
            trans.fail();
            fail();
        }
    }

    if (!m_upload_patient_ids_to_move_off.isEmpty()) {
        statusMessage(tr("Wiping specifically requested patients"));
        WhereConditions where;
        where[dbconst::MOVE_OFF_TABLET_FIELDNAME] = 1;
        // Selective wipes: tasks
        if (m_upload_method == UploadMethod::Copy) {
            for (auto tablename : m_p_task_factory->allTablenames()) {
                if (m_upload_tables_to_wipe.contains(tablename)) {
                    continue;  // already wiped
                }
                dbfunc::deleteFrom(m_db, tablename, where);
            }
        }
        // Selective wipes: patients
        dbfunc::deleteFrom(m_db, Patient::TABLENAME, where);
    }
}


void NetworkManager::queryFail(const QString &sql)
{
    statusMessage("Query failed: " + sql);
    fail();
}


void NetworkManager::queryFailClearingMoveOffFlag(const QString& tablename)
{
    queryFail("... trying to clear move-off-tablet flag for table: " +
              tablename);
}


bool NetworkManager::clearMoveOffTabletFlag(const QString& tablename)
{
    // 1. Clear all
    QString sql = QString("UPDATE %1 SET %2 = 0")
            .arg(delimit(tablename),
                 delimit(dbconst::MOVE_OFF_TABLET_FIELDNAME));
    return dbfunc::exec(m_db, sql);
}


bool NetworkManager::pruneDeadBlobs()
{
    using dbfunc::delimit;
    statusMessage("Removing any defunct binary large objects");

    QStringList all_tables = dbfunc::getAllTables(m_db);
    QVector<int> bad_blob_pks;

    // For all BLOBs...
    QString sql = dbfunc::selectColumns(QStringList{dbconst::PK_FIELDNAME,
                                                    Blob::SRC_TABLE_FIELDNAME,
                                                    Blob::SRC_PK_FIELDNAME},
                                        Blob::TABLENAME);
    QSqlQuery query(m_db);
    if (!dbfunc::execQuery(query, sql)) {
        queryFail(sql);
        return false;
    }
    while (query.next()) {
        int blob_pk = query.value(0).toInt();
        QString src_table = query.value(1).toString();
        int src_pk = query.value(2).toInt();
        if (src_pk == dbconst::NONEXISTENT_PK) {
            continue;
        }
        // Does our BLOB refer to something non-existent?
        if (!all_tables.contains(src_table) ||
                !dbfunc::existsByPk(m_db, src_table,
                                    dbconst::PK_FIELDNAME, src_pk)) {
            bad_blob_pks.append(blob_pk);
        }
    }

    int n_bad_blobs = bad_blob_pks.length();
    if (n_bad_blobs == 0) {
        return true;
    }

    qWarning() << "Deleting defunct BLOBs with PKs:" << bad_blob_pks;
    QString paramholders = dbfunc::sqlParamHolders(n_bad_blobs);
    sql = QString("DELETE FROM %1 WHERE %2 IN (%3)")
            .arg(delimit(Blob::TABLENAME),
                 delimit(dbconst::PK_FIELDNAME),
                 paramholders);
    ArgList args = dbfunc::argListFromIntList(bad_blob_pks);
    if (!dbfunc::exec(m_db, sql, args)) {
        queryFail(sql);
        return false;
    }
    return true;
}


// ============================================================================
// Analytics
// ============================================================================

void NetworkManager::sendAnalytics()
{

}
