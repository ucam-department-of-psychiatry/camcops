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

#include <QCoreApplication>  // for Q_DECLARE_TR_FUNCTIONS
#include <QStringList>
#include "common/aliases_camcops.h"

class CamcopsApp;


class TaskChain
{
    Q_DECLARE_TR_FUNCTIONS(TaskChain)

    // ------------------------------------------------------------------------
    // Enums
    // ------------------------------------------------------------------------

public:
    // How should we upload?
    enum class CreationMethod {
        OnDemand,
        AtStart,
        OnDemandOrAbort
    };

    // ------------------------------------------------------------------------
    // TaskChain
    // ------------------------------------------------------------------------

public:
    // Create the chain definition
    TaskChain(CamcopsApp& app,
              const QStringList& task_tablenames,
              CreationMethod creation_method = CreationMethod::OnDemandOrAbort,
              const QString& title = "",
              const QString& subtitle = "");

    // Title/subtitle, for menus
    QString title() const;
    QString subtitle() const;

    // Description
    QString description(bool longname = false) const;

    // Number of tasks in the chain
    int nTasks() const;

    // How tasks should be created
    CreationMethod creationMethod() const;

    // Create a specific task
    TaskPtr makeTask(int index) const;

protected:
    CamcopsApp& m_app;  // our app
    QStringList m_task_tablenames;  // tasks that are part of the chain
    CreationMethod m_creation_method;  // when to create each task
    QString m_title;  // non-default title
    QString m_subtitle;  // non-default subtitle
};
