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
#include "db/databaseobject.h"

class TaskScheduleItem : public DatabaseObject
{
    // Represents a scheduled task.

    Q_OBJECT

public:
    // Possible states of a scheduled task.
    enum class State {
        Future,  // Not yet due.
        Due,  // Needs to be done. Ready to create task instance.
        Started,  // Task instance has been created; not yet complete.
        Completed,  // Task instance has been created and completed.
        Missed  // Due date/time has passed without completion.
    };

public:
    // ------------------------------------------------------------------------
    // Creation
    // ------------------------------------------------------------------------

    // Normal constructor.
    TaskScheduleItem(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK
    );

    // Construct from JSON.
    TaskScheduleItem(
        int schedule_fk,
        CamcopsApp& app,
        DatabaseManager& db,
        const QJsonObject& json_obj
    );

    // Item ID number.
    int id() const;

    // When the task starts to be due, in UTC.
    QDateTime dueFromUtc() const;

    // When the task should be completed by, in UTC.
    QDateTime dueByUtc() const;

    // When the task starts to be due, in UTC.
    QDateTime dueFromLocal() const;

    // When the task should be completed by, in the local timezone.
    QDateTime dueByLocal() const;

    // Returns the associated task instance (or a null pointer if there isn't
    // one).
    TaskPtr getTask() const;

    // Returns the table name of the scheduled task.
    QString taskTableName() const;

    // Returns any JSON settings set by the schedule.
    QJsonObject settings() const;

    // Title of the scheduled task, used as the title for a two-line menu item.
    QString title() const;

    // State/due-by information, used as the subtitle for a two-line menu item.
    QString subtitle() const;

    // Is the task in an editable state?
    bool isEditable() const;

    // Returns the state of the scheduled task.
    State state() const;

    // Returns the complete status of the scheduled task
    bool isComplete() const;

    // When was the task completed?
    QDateTime whenCompleted() const;

    // Marks the scheduled task as complete (or not).
    void setComplete(
        bool complete, const QDateTime& when_completed = QDateTime()
    );

    // Returns the anonymous status of the scheduled task
    bool isAnonymous() const;

    // Marks the scheduled task as anonymous (or not).
    void setAnonymous(bool anonymous);

    // Sets the associated task instance (using the task PK within its table).
    void setTask(int task_id);

    // True if a task is incomplete and we're still before the due date
    bool isIncompleteAndCurrent() const;

    static const QString TABLENAME;

    static const QString FK_TASK_SCHEDULE;
    static const QString FN_TASK_TABLE_NAME;
    static const QString FN_SETTINGS;
    static const QString FN_DUE_FROM;
    static const QString FN_DUE_BY;
    static const QString FN_COMPLETE;
    static const QString FN_ANONYMOUS;
    static const QString FK_TASK;
    static const QString FN_WHEN_COMPLETED;

    static const QString KEY_TABLE;
    static const QString KEY_SETTINGS;
    static const QString KEY_DUE_FROM;
    static const QString KEY_DUE_BY;
    static const QString KEY_COMPLETE;
    static const QString KEY_ANONYMOUS;
    static const QString KEY_WHEN_COMPLETED;
};
