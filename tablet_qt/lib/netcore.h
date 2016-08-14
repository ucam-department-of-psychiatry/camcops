#pragma once
#include <QObject>
#include <QString>
#include <QSslError>

class QNetworkReply;


class NetworkManager : public QObject
{
    Q_OBJECT
public:
    NetworkManager(const QString& url);
    void testHttp();
    void testHttps(bool ignore_ssl_errors = false);
protected:
    void testReplyFinished(QNetworkReply* reply);
    void sslIgnoringErrorHandler(QNetworkReply* reply,
                                 const QList<QSslError>& errlist);
protected:
    QString m_url;
};
