/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

/*

GENERAL THREADING APPROACH FOR WHISKER CLIENT
===============================================================================

- QTcpSocket can run via an event-driven system using the readyRead() signal,
  or a blocking system using waitForReadyRead(). The docs warn that
  waitForReadyRead() can fail randomly under Windows, so that means we must
  use readyRead() [http://doc.qt.io/qt-5/qabstractsocket.html#waitForReadyRead].

- We must presume that the end user will run the task on the GUI thread (which
  is the worst-case scenario; if a separate thread is used, it can do what it
  likes, but if it uses the GUI thread, it mustn't sit there and spin-wait).

- The Whisker side of things mustn't care which thread the user decides to run
  the task on, though. That means that if the task calls a function to send
  data, that data must cross to a socket-owning thread.
  For the main socket, the simplest thing is to use Qt signals/slots, since
  they handle the thread boundary. So that means something like:

    class WhiskerController {
    signals:
        void eventReceived(const QString& event);
    slots:
        void sendToServer(const QString& command);
    };

- Then the tricky bit is the blocking call:

    QString sendImmediateGetReply(const QString& command);

- Remember that there are several ways to use a QThread:
  - let the QThread do its default run(), which runs a Qt event loop, and
    give it (via QObject::moveToThread()) objects that do useful things via
    signals; or
  - override run().
  See http://doc.qt.io/qt-5/qthread.html.

- So the simplest way will be to have a WhiskerWorker that's derived from
  QObject, and for WhiskerManager to put that into a new thread.

*/

#include <QObject>
#include <QPointer>
#include <QThread>
#include "whisker/whiskerconnectionstate.h"

class CamcopsApp;
class WhiskerInboundMessage;
class WhiskerOutboundCommand;
class WhiskerWorker;


class WhiskerManager : public QObject
{
    Q_OBJECT
public:
    WhiskerManager(CamcopsApp& app);
    ~WhiskerManager();
    void sendMain(const QString& command);
    void sendMain(const QStringList& args);
    void sendMain(std::initializer_list<QString> args);
    void sendImmediateNoReply(const QString& command);
    WhiskerInboundMessage sendImmediateGetReply(const QString& command);
    bool immBool(const QString& command);
    bool immBool(const QStringList& args);
    bool immBool(std::initializer_list<QString> args);
    void connectToServer();
    bool isConnected() const;
    int getNetworkLatencyMs();  // whiskerconstants::FAILURE_INT for failure
signals:
    void disconnectFromServer();
    void connectionStateChanged(bool connected);
    void internalConnectToServer(const QString& host, quint16 port,
                                 int timeout_ms);
    void internalSend(const WhiskerOutboundCommand& cmd);
public slots:
    void internalConnectionStateChanged(WhiskerConnectionState state);
    void internalReceiveFromMainSocket(const WhiskerInboundMessage& msg);
    void onSocketError(const QString& msg);
protected:
    CamcopsApp& m_app;
    QThread m_worker_thread;
    QPointer<WhiskerWorker> m_worker;
};
