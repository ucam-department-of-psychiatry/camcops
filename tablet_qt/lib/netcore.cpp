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

void NetworkManager::test_https()
{
    qDebug() << "Testing HTTPS connection to:" << m_url;
    QNetworkAccessManager* manager = new QNetworkAccessManager();
    QNetworkRequest request;
    // QSslConfiguration config = QSslConfiguration::defaultConfiguration();
    // config.setProtocol(QSsl::TlsV1_2);
    // request.setSslConfiguration(config);
    request.setUrl(QUrl(m_url));
    request.setHeader(QNetworkRequest::ServerHeader, "application/json");
    // http://wiki.qt.io/New_Signal_Slot_Syntax
    connect(manager, &QNetworkAccessManager::finished,
            this, &NetworkManager::replyFinished);
    manager->get(request);
}

void NetworkManager::replyFinished(QNetworkReply* reply)
{
    qDebug() << "Result from" << m_url <<":" << reply->readAll();
}
