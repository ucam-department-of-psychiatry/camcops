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
#include <QVector>
#include "whisker/whiskercallbackdefinition.h"


class WhiskerCallbackHandler
{
public:
    WhiskerCallbackHandler();
    void add(
            int target_n_calls,
            const QString& event,
            const WhiskerCallbackDefinition::CallbackFunction& callback,
            const QString& name = "",
            bool swallow_event = true);
    void addSingle(
            const QString& event,
            const WhiskerCallbackDefinition::CallbackFunction& callback,
            const QString& name = "",
            bool swallow_event = true);
    void addPersistent(
            const QString& event,
            const WhiskerCallbackDefinition::CallbackFunction& callback,
            const QString& name = "",
            bool swallow_event = true);
    void removeByEvent(const QString& event);
    void removeByName(const QString& name);
    void clear();
    int processEvent(const QString& event, bool& swallowed);
protected:
    QVector<WhiskerCallbackDefinition> m_callbacks;
};
