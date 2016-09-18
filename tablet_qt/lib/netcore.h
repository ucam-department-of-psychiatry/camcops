#pragma once
#include <QSslError>

class QNetworkReply;
class QString;


class NetworkManager
{
public:
    NetworkManager(const QString& url);
    void testHttpGet();
    void testHttpsGet(bool ignore_ssl_errors = false);
protected:
    void testReplyFinished(QNetworkReply* reply);
    void sslIgnoringErrorHandler(QNetworkReply* reply,
                                 const QList<QSslError>& errlist);
protected:
    QString m_url;
};
