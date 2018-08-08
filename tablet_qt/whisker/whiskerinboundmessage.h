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
#include <QDateTime>
#include <QDebug>
#include <QString>


class WhiskerInboundMessage {
public:
    // A plain (no arguments) constructor is required so we can put this into
    // a QVector.
    WhiskerInboundMessage(const QString& msg = "",
                          bool immediate_socket = false,
                          const QDateTime& timestamp = QDateTime(),
                          bool has_server_timestamp = false,
                          qulonglong server_timestamp_ms = 0);
    void splitServerTimestamp();
    void setCausalCommand(const QString& causal_command);
    bool immediateReplySucceeded() const;
public:
    QString m_msg;
    bool m_immediate_socket;
    QDateTime m_timestamp;
    bool m_has_server_timestamp;
    qulonglong m_server_timestamp_ms;
    QString m_causal_command;
public:
    friend QDebug operator<<(QDebug debug, const WhiskerInboundMessage& s);
};

Q_DECLARE_METATYPE(WhiskerInboundMessage)
