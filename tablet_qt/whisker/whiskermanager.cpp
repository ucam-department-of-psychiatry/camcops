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

// ============================================================================
// debugging #defines
// ============================================================================

#define DEBUG_WHISKER_MESSAGES

// ============================================================================
// #includes
// ============================================================================

#include "whiskermanager.h"
#include <QRegularExpression>
#include "common/varconst.h"
#include "core/camcopsapp.h"
#include "lib/uifunc.h"
#include "whisker/whiskerapi.h"
#include "whisker/whiskerconstants.h"
#include "whisker/whiskerworker.h"
using whiskerapi::msgFromArgs;


// ============================================================================
// WhiskerManager
// ============================================================================

WhiskerManager::WhiskerManager(CamcopsApp& app) :
    m_app(app),
    m_worker(new WhiskerWorker(this))
{
    // As per http://doc.qt.io/qt-5/qthread.html:
    m_worker->moveToThread(&m_worker_thread);  // changes thread affinity
    connect(&m_worker_thread, &QThread::finished,
            m_worker, &QObject::deleteLater);  // this is how we ensure deletion of m_worker

    // Our additional signal/slot connections:
    connect(this, &WhiskerManager::internalConnectToServer,
            m_worker, &WhiskerWorker::connectToServer);
    connect(this, &WhiskerManager::disconnectFromServer,
            m_worker, &WhiskerWorker::disconnectFromServer);
    connect(this, &WhiskerManager::internalSend,
            m_worker, &WhiskerWorker::sendToServer);

    connect(m_worker, &WhiskerWorker::connectionStateChanged,
            this, &WhiskerManager::internalConnectionStateChanged);
    connect(m_worker, &WhiskerWorker::receivedFromServerMainSocket,
            this, &WhiskerManager::internalReceiveFromMainSocket);

    m_worker_thread.start();
}


WhiskerManager::~WhiskerManager()
{
    m_worker_thread.quit();
    m_worker_thread.wait();
}


void WhiskerManager::connectToServer()
{
    const QString host = m_app.varString(varconst::WHISKER_HOST);
    const quint16 port = m_app.varInt(varconst::WHISKER_PORT);
    const int timeout_ms = m_app.varInt(varconst::WHISKER_TIMEOUT_MS);
    emit internalConnectToServer(host, port, timeout_ms);
}


bool WhiskerManager::isConnected() const
{
    return m_worker->isImmediateConnected();
}


void WhiskerManager::sendMain(const QString& command)
{
    WhiskerOutboundCommand cmd(command, false);
    emit internalSend(cmd);
}


void WhiskerManager::sendMain(const QStringList& args)
{
    sendMain(msgFromArgs(args));
}


void WhiskerManager::sendMain(std::initializer_list<QString> args)
{
    sendMain(msgFromArgs(QStringList(args)));
}


void WhiskerManager::sendImmediateNoReply(const QString& command)
{
#ifdef DEBUG_SOCKETS
    qDebug() << "Sending immediate-socket command (for no reply):" << command;
#endif
    WhiskerOutboundCommand cmd(command, true, true);
    emit internalSend(cmd);  // transfer send command to our worker on its socket thread
}


WhiskerInboundMessage WhiskerManager::sendImmediateGetReply(
        const QString& command)
{
#ifdef DEBUG_SOCKETS
    qDebug() << "Sending immediate-socket command:" << command;
#endif
    WhiskerOutboundCommand cmd(command, true, false);
    emit internalSend(cmd);  // transfer send command to our worker on its socket thread
    WhiskerInboundMessage msg = m_worker->getPendingImmediateReply();
#ifdef DEBUG_SOCKETS
        qDebug()
                << "Immediate-socket command" << msg.m_causal_command
                << "-> reply" << msg.m_msg;
#endif
    return msg;
}


bool WhiskerManager::immBool(const QString& command)
{
    WhiskerInboundMessage msg = sendImmediateGetReply(command);
    return msg.immediateReplySucceeded();
}


bool WhiskerManager::immBool(const QStringList& args)
{
    return immBool(msgFromArgs(args));
}


bool WhiskerManager::immBool(std::initializer_list<QString> args)
{
    return immBool(msgFromArgs(QStringList(args)));
}


void WhiskerManager::internalReceiveFromMainSocket(
        const WhiskerInboundMessage& msg)
{
#ifdef DEBUG_WHISKER_MESSAGES
    qDebug() << "Received Whisker main-socket message:" << msg;
#endif
}


void WhiskerManager::internalConnectionStateChanged(
        WhiskerConnectionState state)
{
    emit connectionStateChanged(state == WhiskerConnectionState::G_FullyConnected);
}


void WhiskerManager::onSocketError(const QString& msg)
{
    uifunc::alert("Whisker socket error:\n\n" + msg,
                  whiskerconstants::WHISKER_ALERT_TITLE);
}


int WhiskerManager::getNetworkLatencyMs()
{
    WhiskerInboundMessage reply_ping = sendImmediateGetReply(
                whiskerconstants::CMD_TEST_NETWORK_LATENCY);
    if (reply_ping.m_msg != whiskerconstants::PING) {
        return whiskerconstants::FAILURE_INT;
    }
    WhiskerInboundMessage reply_latency = sendImmediateGetReply(
                whiskerconstants::PING_ACK);
    bool ok;
    int latency_ms = reply_latency.m_msg.toInt(&ok);
    if (!ok) {
        return whiskerconstants::FAILURE_INT;
    }
    return latency_ms;
}
