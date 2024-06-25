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

#include "taskschedule.h"

#include <QJsonObject>
#include <QJsonValue>
#include <QString>
#include <QVector>

#include "common/aliases_camcops.h"
#include "common/dbconst.h"
#include "core/camcopsapp.h"
#include "db/ancillaryfunc.h"
#include "tasklib/taskscheduleitem.h"

const QString TaskSchedule::TABLENAME("task_schedule");

const QString TaskSchedule::FN_NAME("name");

const QString TaskSchedule::KEY_TASK_SCHEDULE_NAME("task_schedule_name");

// ============================================================================
// Creation
// ============================================================================


TaskSchedule::TaskSchedule(
    CamcopsApp& app, DatabaseManager& db, const int load_pk
) :
    DatabaseObject(
        app,
        db,
        TABLENAME,
        dbconst::PK_FIELDNAME,
        false,  // Has modification timestamp
        false,  // Has creation timestamp
        false,  // Has move off tablet field
        false
    )  // Triggers need upload
{
    addField(FN_NAME, QMetaType::fromType<QString>());

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

TaskSchedule::TaskSchedule(
    CamcopsApp& app, DatabaseManager& db, const QJsonObject& json_obj
) :
    TaskSchedule(app, db)
{
    setValueFromJson(json_obj, FN_NAME, KEY_TASK_SCHEDULE_NAME);
}

void TaskSchedule::addItems(const QJsonArray& items_json_array)
{
    QJsonArray::const_iterator it;
    for (it = items_json_array.constBegin(); it != items_json_array.constEnd();
         it++) {
        const QJsonObject item_json = it->toObject();

        TaskScheduleItemPtr item = TaskScheduleItemPtr(
            new TaskScheduleItem(id(), m_app, m_app.sysdb(), item_json)
        );
        item->save();

        m_items.append(item);
    }
}

// ============================================================================
// Ancillary management
// ============================================================================

void TaskSchedule::loadAllAncillary(const int pk)
{
    const OrderBy order_by{{TaskScheduleItem::FN_DUE_BY, true}};
    ancillaryfunc::loadAncillary<TaskScheduleItem, TaskScheduleItemPtr>(
        m_items, m_app, m_db, TaskScheduleItem::FK_TASK_SCHEDULE, order_by, pk
    );
}

QVector<DatabaseObjectPtr> TaskSchedule::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>{
        TaskScheduleItemPtr(new TaskScheduleItem(m_app, m_db)),
    };
}

QVector<DatabaseObjectPtr> TaskSchedule::getAllAncillary() const
{
    QVector<DatabaseObjectPtr> ancillaries;
    for (const TaskScheduleItemPtr& item : m_items) {
        ancillaries.append(item);
    }
    return ancillaries;
}

TaskScheduleItemPtr TaskSchedule::findItem(const TaskScheduleItemPtr match)
{
    for (const TaskScheduleItemPtr& item : qAsConst(m_items)) {
        if (item->dueFromUtc() == match->dueFromUtc()
            && item->dueByUtc() == match->dueByUtc()
            && item->taskTableName() == match->taskTableName()) {

            return item;
        }
    }

    return nullptr;
}

QVector<TaskScheduleItemPtr> TaskSchedule::items() const
{
    return m_items;
}

// ============================================================================
// Information about schedules
// ============================================================================

int TaskSchedule::id() const
{
    return pkvalueInt();
}

QString TaskSchedule::name() const
{
    const QString name = valueString(FN_NAME);
    return name.isEmpty() ? "?" : name;
}

bool TaskSchedule::hasIncompleteCurrentTasks() const
{
    for (const TaskScheduleItemPtr& schedule_item : qAsConst(m_items)) {
        if (schedule_item->isIncompleteAndCurrent()) {
            return true;
        }
    }

    return false;
}
