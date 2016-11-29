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

#pragma once
#include <QPointer>
#include <QObject>
#include <QSslError>

class CamcopsApp;
class LogBox;
class QNetworkAccessManager;
class QNetworkReply;
class QString;


class NetworkManager : public QObject
{
    // Controls network operations, optionally providing a progress display.

    Q_OBJECT
public:
    NetworkManager(const CamcopsApp& app, QWidget* parent);
    ~NetworkManager();
    void setSilent(bool silent);
    void setTitle(const QString& title);
    void testHttpGet(const QString& url, bool offer_cancel = true);
    void testHttpsGet(const QString& url, bool offer_cancel = true,
                      bool ignore_ssl_errors = false);
    void statusMessage(const QString& msg);
signals:
    void cancelled();
    void finished();
public slots:
    void cancel();
    void finish();
protected slots:
    void logboxCancelled();
    void logboxFinished();
protected:
    void testReplyFinished(QNetworkReply* reply);
    void sslIgnoringErrorHandler(QNetworkReply* reply,
                                 const QList<QSslError>& errlist);
    void commonFinish();
    void disconnectManager();
protected:
    const CamcopsApp& m_app;
    QWidget* m_parent;
    QString m_title;
    bool m_offer_cancel;
    bool m_silent;
    QPointer<LogBox> m_logbox;
    QNetworkAccessManager* m_mgr;
};
