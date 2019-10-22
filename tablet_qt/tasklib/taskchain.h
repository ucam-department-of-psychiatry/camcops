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

#include <QObject>
#include <QStringList>
#include "common/aliases_camcops.h"

class CamcopsApp;


class TaskChain : public QObject
{
    Q_OBJECT

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
              CreationMethod creation_method = CreationMethod::AtStart,
              const QString& title = "",
              const QString& subtitle = "");

    // Title/subtitle, for menus
    QString title() const;
    QString subtitle() const;

    // Description
    QString description(bool longname = false) const;

    // Number of tasks in the chain
    int nTasks() const;

    // Does this chain contain at least one non-anonymous task?
    bool needsPatient() const;

    // Is the chain permissible?
    bool permissible(QStringList& failure_reasons) const;

    // How tasks should be created
    CreationMethod creationMethod() const;

    // Start a chain and manage it
    void start();

protected:
    // Create a specific task
    void ensureTaskCreated(int index);

    // Create all tasks not yet created
    void ensureAllTasksCreated();

    // Fetch a pointer to a specific task.
    TaskPtr getTask(int index);

    // Start the next task in the sequence
    void startNextTask();

    // Not sure this is necessary.
    void onAllTasksFinished();

protected slots:
    // A task has been aborted.
    void onTaskAborted();

    // A task has finished.
    void onTaskFinished();

    // The task has asked the app to close its window and the app has done
    // the necessary.
    void onAppSubWindowClosed();

protected:
    CamcopsApp& m_app;  // our app
    QStringList m_task_tablenames;  // tasks that are part of the chain
    CreationMethod m_creation_method;  // when to create each task
    QString m_title;  // non-default title
    QString m_subtitle;  // non-default subtitle
    int m_current_task_index;
    QMap<int, TaskPtr> m_tasks;
    bool m_proceed_when_app_has_closed_last_task;
};
