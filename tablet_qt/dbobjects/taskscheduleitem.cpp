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
#include "lib/datetime.h"
#include "tasklib/taskfactory.h"
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
    addField(FN_DUE_FROM, QVariant::String, true);
    addField(FN_DUE_BY, QVariant::String, true);

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


QDate TaskScheduleItem::dueFrom() const
{
    return value(FN_DUE_FROM).toDate();
}


QDate TaskScheduleItem::dueBy() const
{
    return value(FN_DUE_BY).toDate();
}

QString TaskScheduleItem::taskTableName() const
{
    const QString table_name = valueString(FN_TASK_TABLE_NAME);

    return table_name.isEmpty() ? "?" : table_name;
}

QString TaskScheduleItem::title() const
{
    TaskFactory* factory = m_app.taskFactory();
    TaskPtr task = factory->create(taskTableName());

    return QString(task->longname());
}

QString TaskScheduleItem::subtitle() const
{
    TaskFactory* factory = m_app.taskFactory();
    TaskPtr task = factory->create(taskTableName());

    return QString(tr("Complete between %1 and %2")).arg(
        dueFrom().toString(datetime::LONG_DATE_FORMAT),
        dueBy().toString(datetime::LONG_DATE_FORMAT)
    );
}

bool TaskScheduleItem::active() const
{
    auto today = QDate::currentDate();

    return today >= dueFrom();
}
