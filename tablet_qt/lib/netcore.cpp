#define DEBUG_NETWORK_REQUESTS
#define DEBUG_NETWORK_REPLIES

#include "netcore.h"
#include <functional>
#include <QObject>
#include <QtNetwork/QNetworkAccessManager>
#include <QtNetwork/QNetworkRequest>
#include <QtNetwork/QNetworkReply>
#include <QtNetwork/QSslConfiguration>
#include <QUrl>


NetworkManager::NetworkManager(const QString& url) :
    m_url(url)
{
}

void NetworkManager::testHttpGet()
{
    qInfo() << "Testing HTTP GET connection to:" << m_url;
    QNetworkAccessManager* manager = new QNetworkAccessManager();
    QNetworkRequest request;
    // URL
    request.setUrl(QUrl(m_url));
    // Callback
    QObject::connect(manager, &QNetworkAccessManager::finished,
                     std::bind(&NetworkManager::testReplyFinished,
                               this, std::placeholders::_1));
    // GET
    manager->get(request);
    qInfo() << "... sent request to: " << m_url;
}


void NetworkManager::testHttpsGet(bool ignore_ssl_errors)
{
    qInfo() << "Testing HTTPS GET connection to:" << m_url;
    QNetworkAccessManager* manager = new QNetworkAccessManager();
    QNetworkRequest request;
    // SSL
    QSslConfiguration config = QSslConfiguration::defaultConfiguration();
    config.setProtocol(QSsl::TlsV1_2);
    // NB the OpenSSL version must also support it; see also
    // https://bugreports.qt.io/browse/QTBUG-31230
    // ... but working fine with manually compiled OpenSSL
    request.setSslConfiguration(config);
    // URL
    request.setUrl(QUrl(m_url));
    // Callback
    // http://wiki.qt.io/New_Signal_Slot_Syntax
    QObject::connect(manager, &QNetworkAccessManager::finished,
                     std::bind(&NetworkManager::testReplyFinished, this,
                               std::placeholders::_1));
    if (ignore_ssl_errors) {
        QObject::connect(manager, &QNetworkAccessManager::sslErrors,
                         std::bind(&NetworkManager::sslIgnoringErrorHandler,
                                   this, std::placeholders::_1,
                                   std::placeholders::_2));
    }
    // GET
    manager->get(request);
    qInfo() << "... sent request to: " << m_url;
}


void NetworkManager::sslIgnoringErrorHandler(QNetworkReply* reply,
                                             const QList<QSslError> & errlist)
{
    qWarning() << "Ignoring SSL errors:" << errlist;
    reply->ignoreSslErrors();
}


void NetworkManager::testReplyFinished(QNetworkReply* reply)
{
    if (reply->error() == QNetworkReply::NoError) {
        qInfo() << "Result from" << m_url <<":" << reply->readAll();
    } else {
        qWarning() << "Network error:" << reply->errorString();
    }
}
