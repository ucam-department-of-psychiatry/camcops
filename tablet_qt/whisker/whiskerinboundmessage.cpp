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

#include "whiskerinboundmessage.h"
#include "whisker/whiskerconstants.h"


WhiskerInboundMessage::WhiskerInboundMessage(const QString& msg,
                                             bool immediate_socket,
                                             const QDateTime& timestamp,
                                             bool has_timestamp,
                                             qulonglong timestamp_ms) :
    m_msg(msg),
    m_immediate_socket(immediate_socket),
    m_timestamp(timestamp),
    m_has_server_timestamp(has_timestamp),
    m_server_timestamp_ms(timestamp_ms)
{
}


void WhiskerInboundMessage::splitServerTimestamp()
{
    QRegularExpressionMatch match = whiskerconstants::TIMESTAMP_REGEX.match(m_msg);
    if (match.hasMatch()) {
        const QString msg = match.captured(1);
        const QString timestamp_str = match.captured(2);
        bool ok;
        const qulonglong timestamp_ms = timestamp_str.toULongLong(&ok);
        if (ok) {
            m_has_server_timestamp = true;
            m_msg = msg;
            m_server_timestamp_ms = timestamp_ms;
        } else {
            qWarning() << Q_FUNC_INFO << "Bad timestamp:" << timestamp_str;
            m_has_server_timestamp = false;
        }
    }
}


void WhiskerInboundMessage::setCausalCommand(const QString& causal_command)
{
    m_causal_command = causal_command;
}


bool WhiskerInboundMessage::immediateReplySucceeded() const
{
    return m_msg == whiskerconstants::RESPONSE_SUCCESS;
}


QDebug operator<<(QDebug debug, const WhiskerInboundMessage& m)
{
    debug.nospace()
            << "InboundMessage(msg=" << m.m_msg
            << ", immediate_socket=" << m.m_immediate_socket
            << ", timestamp=" << m.m_timestamp
            << ", has_server_timestamp=" << m.m_has_server_timestamp
            << ", server_timestamp_ms=" << m.m_server_timestamp_ms
            << ", causal_command=" << m.m_causal_command
            << ")";
    return debug;
}

