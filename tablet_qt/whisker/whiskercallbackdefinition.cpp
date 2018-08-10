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

#include "whiskercallbackdefinition.h"
#include <QDebug>


WhiskerCallbackDefinition::WhiskerCallbackDefinition(
        const QString& event, const CallbackFunction& callback,
        const QString& name, int target_n_calls, bool swallow_event) :
    m_event(event),
    m_callback(callback),
    m_name(name),
    m_target_n_calls(target_n_calls),
    m_swallow_event(swallow_event),
    m_n_calls(0)
{
}


WhiskerCallbackDefinition::WhiskerCallbackDefinition()
{
    // nasty default constructor used by QVector; UNSAFE
    // See http://doc.qt.io/qt-5/containers.html#default-constructed-value
    qWarning() << "Unsafe use of WhiskerCallbackDefinition::WhiskerCallbackDefinition()";
}


QString WhiskerCallbackDefinition::event() const
{
    return m_event;
}


QString WhiskerCallbackDefinition::name() const
{
    return m_name;
}


bool WhiskerCallbackDefinition::isDefunct() const
{
    return m_target_n_calls > 0 && m_n_calls >= m_target_n_calls;
}


bool WhiskerCallbackDefinition::swallowEvent() const
{
    return m_swallow_event;
}


void WhiskerCallbackDefinition::call()
{
    ++m_n_calls;
    m_callback();
}
