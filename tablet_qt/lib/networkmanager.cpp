/*
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
#define DEBUG_NETWORK_REPLIES

#include "networkmanager.h"
#include <functional>
#include <QObject>
#include <QtNetwork/QNetworkAccessManager>
#include <QtNetwork/QNetworkRequest>
#include <QtNetwork/QNetworkReply>
#include <QtNetwork/QSslConfiguration>
#include <QUrl>
#include "common/camcopsapp.h"
#include "dialogs/logbox.h"


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


NetworkManager::NetworkManager(const CamcopsApp& app, QWidget* parent) :
    m_app(app),
    m_parent(parent),
    m_offer_cancel(true),
    m_silent(parent == nullptr),
    m_logbox(nullptr),
    m_mgr(new QNetworkAccessManager(this))
{
}


NetworkManager::~NetworkManager()
{
    if (m_logbox) {
        m_logbox->deleteLater();
    }
}


// ============================================================================
// User interface
// ============================================================================

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
        qDebug() << "silent";
        return;
    }
    if (!m_logbox) {
        qDebug() << "creating logbox";
        m_logbox = new LogBox(m_parent, m_title, m_offer_cancel);
        m_logbox->setStyleSheet(
                    m_app.getSubstitutedCss(UiConst::CSS_CAMCOPS_MAIN));
        connect(m_logbox.data(), &LogBox::accepted,
                this, &NetworkManager::logboxFinished,
                Qt::UniqueConnection);
        connect(m_logbox.data(), &LogBox::rejected,
                this, &NetworkManager::cancelled,
                Qt::UniqueConnection);
        m_logbox->open();
    }
    m_logbox->statusMessage(msg);
}


void NetworkManager::logboxCancelled()
{
    // User has hit cancel
    qDebug() << Q_FUNC_INFO;
    if (!m_logbox) {
        return;
    }
    m_logbox->deleteLater();
    emit cancelled();
}


void NetworkManager::logboxFinished()
{
    // User has acknowledged finish
    qDebug() << Q_FUNC_INFO;
    if (!m_logbox) {
        return;
    }
    m_logbox->deleteLater();
    emit finished();
}


// ============================================================================
// Basic connection management
// ============================================================================

void NetworkManager::disconnectManager()
{
    m_mgr->disconnect();
}


void NetworkManager::sslIgnoringErrorHandler(QNetworkReply* reply,
                                             const QList<QSslError> & errlist)
{
    // Error handle that ignores SSL certificate errors and continues
    statusMessage("Ignoring SSL errors:");
    for (auto err : errlist) {
        statusMessage(err.errorString());
    }
    reply->ignoreSslErrors();
}


void NetworkManager::cancel()
{
    qDebug() << Q_FUNC_INFO;
    if (m_logbox) {
        m_logbox->reject();  // its rejected() signal calls our cancelled()
    } else {
        emit cancelled();
    }
}


void NetworkManager::finish()
{
    qDebug() << Q_FUNC_INFO;
    if (m_logbox) {
        m_logbox->finish();
    } else {
        emit finished();
    }
}


// ============================================================================
// Testing
// ============================================================================

void NetworkManager::testHttpGet(const QString& url, bool offer_cancel)
{
    m_offer_cancel = offer_cancel;
    statusMessage("Testing HTTP GET connection to: " + url);
    QNetworkRequest request;
    // URL
    request.setUrl(QUrl(url));
    // Callback
    disconnectManager();
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
    m_offer_cancel = offer_cancel;
    statusMessage("Testing HTTPS GET connection to: " + url);
    QNetworkRequest request;
    // SSL
    QSslConfiguration config = QSslConfiguration::defaultConfiguration();
    config.setProtocol(QSsl::TlsV1_2);
    // NB the OpenSSL version must also support it; see also
    // https://bugreports.qt.io/browse/QTBUG-31230
    // ... but working fine with manually compiled OpenSSL
    request.setSslConfiguration(config);
    // URL
    request.setUrl(QUrl(url));
    // Callback
    disconnectManager();
    // Safe object lifespan signal: can use std::bind
    QObject::connect(m_mgr, &QNetworkAccessManager::finished,
                     std::bind(&NetworkManager::testReplyFinished, this,
                               std::placeholders::_1));
    // Note: the reply callback arrives on the main (GUI) thread.
    if (ignore_ssl_errors) {
        QObject::connect(m_mgr, &QNetworkAccessManager::sslErrors,
                         std::bind(&NetworkManager::sslIgnoringErrorHandler,
                                   this, std::placeholders::_1,
                                   std::placeholders::_2));
    }
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
    reply->deleteLater(); //  http://doc.qt.io/qt-5/qnetworkaccessmanager.html#details
    finish();
}


