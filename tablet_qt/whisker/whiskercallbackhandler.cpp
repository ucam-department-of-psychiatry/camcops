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

#include "whiskercallbackhandler.h"

WhiskerCallbackHandler::WhiskerCallbackHandler()
{
}


void WhiskerCallbackHandler::add(
        int target_n_calls,
        const QString& event,
        const WhiskerCallbackDefinition::CallbackFunction& callback,
        const QString& name,
        bool swallow_event)
{
    WhiskerCallbackDefinition cb(event, callback, name, target_n_calls, swallow_event);
    m_callbacks.append(cb);
}


void WhiskerCallbackHandler::addSingle(
        const QString& event,
        const WhiskerCallbackDefinition::CallbackFunction& callback,
        const QString& name,
        bool swallow_event)
{
    // Adds a single-shot callback.
    add(1, event, callback, name, swallow_event);
}


void WhiskerCallbackHandler::addPersistent(
        const QString& event,
        const WhiskerCallbackDefinition::CallbackFunction& callback,
        const QString& name,
        bool swallow_event)
{
    // Adds a persistent callback.
    add(0, event, callback, name, swallow_event);
}


void WhiskerCallbackHandler::removeByEvent(const QString& event)
{
    if (event.isEmpty()) {
        return;
    }
    QMutableVectorIterator<WhiskerCallbackDefinition> it(m_callbacks);
    while (it.hasNext()) {
        if (it.next().event() == event) {
            it.remove();
        }
    }
}


void WhiskerCallbackHandler::removeByName(const QString& name)
{
    if (name.isEmpty()) {
        return;
    }
    QMutableVectorIterator<WhiskerCallbackDefinition> it(m_callbacks);
    while (it.hasNext()) {
        if (it.next().name() == name) {
            it.remove();
        }
    }
}


void WhiskerCallbackHandler::clear()
{
    // Removes all callbacks.
    m_callbacks.clear();
}


int WhiskerCallbackHandler::processEvent(const QString& event, bool& swallowed)
{
    // Calls any callbacks for the event.
    // Returns the number of callbacks called.
    int n_called = 0;
    swallowed = false;
    for (WhiskerCallbackDefinition& callback : m_callbacks) {
        if (callback.event() == event) {
            callback.call();
            ++n_called;
            if (callback.swallowEvent()) {
                swallowed = true;
                break;
            }
        }
    }

    // Remove any single-shot (or otherwise expired) events.
    // http://doc.qt.io/qt-5/containers.html#java-style-iterators
    QMutableVectorIterator<WhiskerCallbackDefinition> it(m_callbacks);
    while (it.hasNext()) {
        if (it.next().isDefunct()) {
            it.remove();
        }
    }

    return n_called;
}
