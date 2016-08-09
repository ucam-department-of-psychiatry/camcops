#define DEBUG_NETWORK_REQUESTS
#define DEBUG_NETWORK_REPLIES

#include "netcore.h"
#include <QDebug>
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
#ifdef DEBUG_NETWORK_REQUESTS
    qDebug() << "Testing HTTP connection to:" << m_url;
#endif
    QNetworkAccessManager* manager = new QNetworkAccessManager();
    QNetworkRequest request;
    // URL
    request.setUrl(QUrl(m_url));
    // Callback
    connect(manager, &QNetworkAccessManager::finished,
            this, &NetworkManager::replyFinished);
    // GET
    manager->get(request);
#ifdef DEBUG_NETWORK_REQUESTS
    qDebug() << "... sent request to: " << m_url;
#endif
}


void NetworkManager::testHttps()
{
#ifdef DEBUG_NETWORK_REQUESTS
    qDebug() << "Testing HTTPS connection to:" << m_url;
#endif
    QNetworkAccessManager* manager = new QNetworkAccessManager();
    QNetworkRequest request;
    // SSL
    QSslConfiguration config = QSslConfiguration::defaultConfiguration();
    config.setProtocol(QSsl::TlsV1_2);
    request.setSslConfiguration(config);
    // URL
    request.setUrl(QUrl(m_url));
    // Callback
    // http://wiki.qt.io/New_Signal_Slot_Syntax
    connect(manager, &QNetworkAccessManager::finished,
            this, &NetworkManager::replyFinished);
    // GET
    manager->get(request);
#ifdef DEBUG_NETWORK_REQUESTS
    qDebug() << "... sent request to: " << m_url;
#endif
}


void NetworkManager::replyFinished(QNetworkReply* reply)
{
#ifdef DEBUG_NETWORK_REPLIES
    qDebug() << "Result from" << m_url <<":" << reply->readAll();
#endif
}
