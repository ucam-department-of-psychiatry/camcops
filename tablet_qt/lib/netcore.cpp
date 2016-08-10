#define DEBUG_NETWORK_REQUESTS
#define DEBUG_NETWORK_REPLIES

#include "netcore.h"
#include <QtNetwork/QNetworkAccessManager>
#include <QtNetwork/QNetworkRequest>
#include <QtNetwork/QNetworkReply>
#include <QtNetwork/QSslConfiguration>
#include <QUrl>


NetworkManager::NetworkManager(const QString& url) :
    m_url(url)
{
}

void NetworkManager::testHttp()
{
    qInfo() << "Testing HTTP connection to:" << m_url;
    QNetworkAccessManager* manager = new QNetworkAccessManager();
    QNetworkRequest request;
    // URL
    request.setUrl(QUrl(m_url));
    // Callback
    connect(manager, &QNetworkAccessManager::finished,
            this, &NetworkManager::testReplyFinished);
    // GET
    manager->get(request);
    qInfo() << "... sent request to: " << m_url;
}


void NetworkManager::testHttps(bool ignore_ssl_errors)
{
    qInfo() << "Testing HTTPS connection to:" << m_url;
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
    connect(manager, &QNetworkAccessManager::finished,
            this, &NetworkManager::testReplyFinished);
    if (ignore_ssl_errors) {
        connect(manager, &QNetworkAccessManager::sslErrors,
                this, &NetworkManager::sslIgnoringErrorHandler);
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
