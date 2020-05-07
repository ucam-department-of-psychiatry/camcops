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

#include <QJsonObject>
#include <QJsonValue>
#include <QString>

#include "core/camcopsapp.h"
#include "db/databasemanager.h"
#include "db/databaseobject.h"
#include "taskscheduleitem.h"

const QString TaskScheduleItem::TABLENAME("task_schedule_item");

const QString TaskScheduleItem::FN_TASK_TABLE_NAME("task_table_name");
const QString TaskScheduleItem::FN_DUE_FROM("due_from");
const QString TaskScheduleItem::FN_DUE_BY("due_by");
const QString TaskScheduleItem::FK_TASK_SCHEDULE("schedule_id");

const QString TaskScheduleItem::KEY_DUE_BY("due_by");
const QString TaskScheduleItem::KEY_DUE_FROM("due_from");
const QString TaskScheduleItem::KEY_TABLE("table");


// ============================================================================
// Creation
// ============================================================================


TaskScheduleItem::TaskScheduleItem(CamcopsApp& app, DatabaseManager& db,
    const int load_pk) :
    DatabaseObject(app, db, TABLENAME,
                   dbconst::PK_FIELDNAME,
                   true,
                   false,
                   false,
                   false)
{
    addField(FK_TASK_SCHEDULE, QVariant::Int, true);
    addField(FN_TASK_TABLE_NAME, QVariant::String, true);
    addField(FN_DUE_FROM, QVariant::Int, true);
    addField(FN_DUE_BY, QVariant::Int, true);

    load(load_pk);
}


TaskScheduleItem::TaskScheduleItem(const int schedule_fk, CamcopsApp& app,
                                   DatabaseManager& db,
                                   const QJsonObject json_obj) :
    TaskScheduleItem(app, db)
{
    setValue(FK_TASK_SCHEDULE, schedule_fk);
    addJsonFields(json_obj);
    save();
}


void TaskScheduleItem::addJsonFields(const QJsonObject json_obj)
{
    auto setValueOrNull = [&](const QString& field, const QString& key) {
        QJsonValue value = json_obj.value(key);
        if (!value.isNull()) {
            setValue(field, value.toString());
        }
    };

    setValueOrNull(FN_TASK_TABLE_NAME, KEY_TABLE);
    setValueOrNull(FN_DUE_FROM, KEY_DUE_FROM);
    setValueOrNull(FN_DUE_BY, KEY_DUE_BY);
}


// ============================================================================
// Information about schedules
// ============================================================================

int TaskScheduleItem::id() const
{
    return pkvalueInt();
}


QString TaskScheduleItem::due_from() const
{
    const QString due_from = valueString(FN_DUE_FROM);

    return due_from.isEmpty() ? "?" : due_from;
}


QString TaskScheduleItem::due_by() const
{
    const QString due_by = valueString(FN_DUE_BY);

    return due_by.isEmpty() ? "?" : due_by;
}
