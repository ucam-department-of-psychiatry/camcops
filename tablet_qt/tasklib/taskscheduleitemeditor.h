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

#pragma once

#include <QObject>

#include "common/aliases_camcops.h"

class TaskScheduleItemEditor : public QObject
{
    Q_OBJECT

public:
    TaskScheduleItemEditor(
        CamcopsApp& app, TaskScheduleItemPtr task_schedule_item
    );
    void editTask();

protected slots:
    // A scheduled task is complete
    void onTaskFinished();

private:
    CamcopsApp& m_app;
    TaskScheduleItemPtr m_p_task_schedule_item;

    bool canEditTask(TaskPtr task);
};
