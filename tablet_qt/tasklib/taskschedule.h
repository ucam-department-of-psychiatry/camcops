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
#include <QJsonArray>
#include <QJsonObject>
#include <QVector>

#include "db/databaseobject.h"

class TaskSchedule : public DatabaseObject
{
    Q_OBJECT

public:
    // ------------------------------------------------------------------------
    // Creation
    // ------------------------------------------------------------------------

    // Normal constructor.
    TaskSchedule(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK
    );

    // Construct from JSON.
    TaskSchedule(
        CamcopsApp& app, DatabaseManager& db, const QJsonObject& json_obj
    );

    // Add schedule items from JSON.
    void addItems(const QJsonArray& items_json_array);

    // ------------------------------------------------------------------------
    // Ancillary management
    // ------------------------------------------------------------------------

    virtual void loadAllAncillary(int pk) override;
    virtual QVector<DatabaseObjectPtr> getAncillarySpecimens() const override;
    virtual QVector<DatabaseObjectPtr> getAllAncillary() const override;

    // ========================================================================
    // Information about schedules
    // ========================================================================

    // Schedule ID.
    int id() const;

    // Schedule name.
    QString name() const;

    // Find a schedule item for the same task and dates/times
    TaskScheduleItemPtr findItem(const TaskScheduleItemPtr match);

    // Schedule items (tasks with dates/times).
    QVector<TaskScheduleItemPtr> items() const;

protected:
    // Schedule items
    QVector<TaskScheduleItemPtr> m_items;

public:
    static const QString TABLENAME;
    static const QString FN_NAME;

    static const QString KEY_TASK_SCHEDULE_NAME;

    bool hasIncompleteCurrentTasks() const;
};
