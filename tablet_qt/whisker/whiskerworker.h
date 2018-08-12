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
#include <QAbstractSocket>
#include <QMutex>
#include <QString>
#include <QVector>
#include <QWaitCondition>
#include "whisker/whiskerconnectionstate.h"
#include "whisker/whiskerconstants.h"
#include "whisker/whiskerinboundmessage.h"
#include "whisker/whiskeroutboundcommand.h"
class QTcpSocket;
class WhiskerManager;


class WhiskerWorker : public QObject
{
    Q_OBJECT
public:
    WhiskerWorker(WhiskerManager* manager);
    WhiskerInboundMessage getPendingImmediateReply();  // called from OTHER THREADS
    bool isMainConnected() const;
    bool isImmediateConnected() const;
signals:
    void connectionStateChanged(WhiskerConnectionState state);
    void receivedFromServerMainSocket(const WhiskerInboundMessage& msg);  // to WhiskerManager
    void socketError(const QString& msg);
    void internalSend(const WhiskerOutboundCommand& cmd);
public slots:
    void connectToServer(
            const QString& host,
            quint16 main_port = whiskerconstants::WHISKER_DEFAULT_PORT
#ifdef WHISKER_NETWORK_TIMEOUT_CONFIGURABLE
            , int timeout_ms = whiskerconstants::WHISKER_DEFAULT_TIMEOUT_MS
#endif
        );
    void disconnectFromServer();
    void sendToServer(const WhiskerOutboundCommand& cmd);  // from WhiskerManager
protected slots:
    void onMainSocketConnected();
    void onImmSocketConnected();
    void onAnySocketDisconnected();
    void onDataReadyFromMainSocket();
    void onDataReadyFromImmediateSocket();
    void onMainSocketError(QAbstractSocket::SocketError error);
    void onImmSocketError(QAbstractSocket::SocketError error);
protected:
    void setConnectionState(WhiskerConnectionState state);
    QVector<WhiskerInboundMessage> getIncomingMessagesFromSocket(
            bool via_immediate_socket);
    QVector<WhiskerInboundMessage> getIncomingMessagesFromBuffer(
            QString& buffer, bool via_immediate_socket,
            const QDateTime& timestamp);
    void processMainSocketMessage(const WhiskerInboundMessage& msg);
    void pushImmediateReply(WhiskerInboundMessage& msg);
protected:
    WhiskerManager* m_manager;
    quint16 m_main_port;
    quint16 m_imm_port;
    QString m_host;
    QString m_code;
    QTcpSocket* m_main_socket;
    QTcpSocket* m_immediate_socket;
    WhiskerConnectionState m_connection_state;
    QString m_inbound_buffer_main;
    QString m_inbound_buffer_imm;
    QVector<WhiskerOutboundCommand> m_imm_commands_awaiting_reply;
    QVector<WhiskerInboundMessage> m_imm_replies_awaiting_collection;
    QMutex m_mutex_imm;  // mutex for m_imm_replies_awaiting_collection AND m_imm_commands_awaiting_reply
    QWaitCondition m_immediate_reply_arrived;
};
