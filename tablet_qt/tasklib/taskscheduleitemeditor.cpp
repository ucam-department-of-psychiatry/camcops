/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include "core/camcopsapp.h"
#include "dbobjects/taskscheduleitem.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "menulib/menuwindow.h"
#include "tasklib/taskfactory.h"
#include "taskscheduleitemeditor.h"

TaskScheduleItemEditor::TaskScheduleItemEditor(
    CamcopsApp& app,
    TaskScheduleItemPtr task_schedule_item) :
    m_app(app),
    m_p_task_schedule_item(task_schedule_item)
{
}


void TaskScheduleItemEditor::editTask()
{
    TaskPtr task = m_p_task_schedule_item->getTask();

    if (task == nullptr) {
        auto tablename = m_p_task_schedule_item->taskTableName();
        task = m_app.taskFactory()->create(tablename);

        if (!canEditTask(task)) {
            return;
        }

        const int patient_id = m_app.selectedPatientId();
        task->setupForEditingAndSave(patient_id);
        const QJsonObject settings = m_p_task_schedule_item->settings();
        task->applySettings(settings);
        m_p_task_schedule_item->setTask(task->pkvalue().toInt());
    }

    OpenableWidget* widget = task->editor(false);
    if (!widget) {
        MenuWindow::complainTaskNotOfferingEditor();
        return;
    }

    Task* ptask = task.data();

    MenuWindow::connectQuestionnaireToTask(widget, ptask);  // in case it's a questionnaire
    QObject::connect(ptask, &Task::editingFinished,
                     this, &TaskScheduleItemEditor::onTaskFinished);

    m_app.openSubWindow(widget, task, true);
}


bool TaskScheduleItemEditor::canEditTask(TaskPtr task)
{
    QString why_not_permissible;
    if (!task->isTaskPermissible(why_not_permissible)) {
        const QString reason = QString("%1<br><br>%2: %3").arg(
            tr("You cannot complete this task with your current settings."),
            tr("Current reason"),
            stringfunc::bold(why_not_permissible)
            );
        uifunc::alert(reason, tr("Not permitted to complete task"));
        return false;
    }

    QString why_not_uploadable;
    if (!task->isTaskUploadable(why_not_uploadable)) {
        const QString reason = QString("%1<br><br>%2: %3").arg(
            tr("You cannot complete this task."),
            tr("Current reason"),
            stringfunc::bold(why_not_uploadable)
            );
        uifunc::alert(reason, tr("Unable to complete task"));
        return false;
    }

    return true;
}

void TaskScheduleItemEditor::onTaskFinished()
{
    m_p_task_schedule_item->setComplete(true);

    TaskPtr task = m_p_task_schedule_item->getTask();

    task->setMoveOffTablet(true);

    // The task will be wiped from the database when we next
    // connect to the server so remove our foreign key now
    m_p_task_schedule_item->setTask(dbconst::NONEXISTENT_PK);
}
