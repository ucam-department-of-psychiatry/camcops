#pragma once
#include <QObject>
#include <QString>
#include <QtNetwork/QNetworkReply>


class NetworkManager : public QObject
{
    Q_OBJECT
public:
    NetworkManager(const QString& url);
    void test_https();
protected:
    void replyFinished(QNetworkReply* reply);
protected:
    QString m_url;
};
