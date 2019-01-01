/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
#include <functional>
#include <QDateTime>
#include <QString>
class WhiskerInboundMessage;


class WhiskerCallbackDefinition
{
public:
    using CallbackFunction = std::function<void(const WhiskerInboundMessage&)>;
    // ... a function that is called with one parameter, a
    // const WhiskerInboundMessage&, and returns void.
    //
    // To pass other arguments, use std::bind to bind them before passing here.
    //
    // Note that the function doesn't even need to accept the
    // WhiskerInboundMessage, if called via std::bind.
    // See https://stackoverflow.com/questions/29159140/why-stdbind-can-be-assigned-to-argument-mismatched-stdfunction.

    enum class ExpiryType {
        Infinite,
        Count,
        Time,
        TimeOrCount
    };
public:
    WhiskerCallbackDefinition(const QString& event,
                              const CallbackFunction& callback,
                              const QString& name = "",
                              ExpiryType how_expires = ExpiryType::Infinite,
                              int target_n_calls = 0,
                              qint64 lifetime_ms = 0,
                              bool swallow_event = false);
    WhiskerCallbackDefinition();  // for QVector
    QString event() const;
    QString name() const;
    bool hasExpired(const QDateTime& now) const;
    bool swallowEvent() const;
    void call(const WhiskerInboundMessage& msg);
protected:
    QString m_event;
    CallbackFunction m_callback;
    QString m_name;
    ExpiryType m_how_expires;
    int m_target_n_calls;
    qint64 m_lifetime_ms;
    QDateTime m_when_created;
    QDateTime m_when_expires;
    bool m_swallow_event;
    int m_n_calls;
};
