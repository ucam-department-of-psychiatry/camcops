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
        const int patient_id = m_app.selectedPatientId();
        task->setupForEditingAndSave(patient_id);
        m_p_task_schedule_item->setTask(task->pkvalue().toInt());
    }

    // TODO: Checks as in SingleTaskMenu::addTask()
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


void TaskScheduleItemEditor::onTaskFinished()
{
    m_p_task_schedule_item->setComplete(true);

    TaskPtr task = m_p_task_schedule_item->getTask();

    task->setMoveOffTablet(true);

    // The task will be wiped from the database when we next
    // connect to the server so remove our foreign key now
    m_p_task_schedule_item->setTask(dbconst::NONEXISTENT_PK);
}
