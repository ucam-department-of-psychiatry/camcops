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
#include <functional>
#include <QString>


class WhiskerCallbackDefinition
{
public:
    using CallbackFunction = std::function<void()>;
    // ... a function that is called with no parameters and returns void
public:
    WhiskerCallbackDefinition(const QString& event,
                              const CallbackFunction& callback,
                              const QString& name = "",
                              int target_n_calls = 0,
                              bool swallow_event = false);
    WhiskerCallbackDefinition();  // for QVector
    QString event() const;
    QString name() const;
    bool isDefunct() const;
    bool swallowEvent() const;
    void call();
protected:
    QString m_event;
    CallbackFunction m_callback;
    QString m_name;
    int m_target_n_calls;
    bool m_swallow_event;
    int m_n_calls;
};
