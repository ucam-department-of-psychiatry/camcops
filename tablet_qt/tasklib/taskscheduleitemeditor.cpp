/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "taskscheduleitemeditor.h"

#include "core/camcopsapp.h"
#include "lib/datetime.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "menulib/menuwindow.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskscheduleitem.h"

TaskScheduleItemEditor::TaskScheduleItemEditor(
    CamcopsApp& app, TaskScheduleItemPtr task_schedule_item
) :
    m_app(app),
    m_p_task_schedule_item(task_schedule_item)
{
}

void TaskScheduleItemEditor::editTask()
{
    TaskPtr task = m_p_task_schedule_item->getTask();

    if (task == nullptr) {
        const auto tablename = m_p_task_schedule_item->taskTableName();
        task = m_app.taskFactory()->create(tablename);
        if (!task) {
            return;
        }

        if (!canEditTask(task)) {
            return;
        }

        const int patient_id = m_app.selectedPatientId();
        task->setupForEditingAndSave(patient_id);

        // Only apply settings on task creation. The task should save any
        // settings along with the responses. So if a task is re-edited we
        // shouldn't need to apply them here. This will prevent the settings
        // from changing, should they change on the server.
        const QJsonObject settings = m_p_task_schedule_item->settings();
        task->applySettings(settings);
        m_p_task_schedule_item->setTask(task->pkvalueInt());
    }

    OpenableWidget* widget = task->editor(false);
    if (!widget) {
        MenuWindow::complainTaskNotOfferingEditor();
        return;
    }

    Task* ptask = task.data();

    MenuWindow::connectQuestionnaireToTask(widget, ptask);
    // ... in case it's a questionnaire
    QObject::connect(
        ptask,
        &Task::editingFinished,
        this,
        &TaskScheduleItemEditor::onTaskFinished
    );

    m_app.openSubWindow(widget, task, true);
}

bool TaskScheduleItemEditor::canEditTask(TaskPtr task)
{
    QString failure_reason;

    if (!task) {
        uifunc::alert(tr("Null task pointer"), tr("Unable to complete task"));
        return false;
    }

    if (!task->isTaskPermissible(failure_reason)
        || !task->isTaskUploadable(failure_reason)) {
        const QString reason
            = QString("%1<br><br>%2: %3")
                  .arg(
                      tr("You cannot complete this task at this time."),
                      tr("Current reason"),
                      stringfunc::bold(failure_reason)
                  );
        uifunc::alert(reason, tr("Not permitted to complete task"));
        return false;
    }

    return true;
}

void TaskScheduleItemEditor::onTaskFinished()
{
    m_p_task_schedule_item->setComplete(true, datetime::now());
}
