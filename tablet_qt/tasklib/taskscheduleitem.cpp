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

#include "taskscheduleitem.h"

#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonParseError>
#include <QJsonValue>
#include <QString>

#include "core/camcopsapp.h"
#include "db/databasemanager.h"
#include "db/databaseobject.h"
#include "lib/datetime.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"

const QString TaskScheduleItem::TABLENAME("task_schedule_item");

const QString TaskScheduleItem::FK_TASK_SCHEDULE("schedule_id");
const QString TaskScheduleItem::FN_TASK_TABLE_NAME("task_table_name");
const QString TaskScheduleItem::FN_SETTINGS("settings");
const QString TaskScheduleItem::FN_DUE_FROM("due_from");
const QString TaskScheduleItem::FN_DUE_BY("due_by");
const QString TaskScheduleItem::FN_COMPLETE("complete");
const QString TaskScheduleItem::FN_ANONYMOUS("anonymous");
const QString TaskScheduleItem::FK_TASK("task");
const QString TaskScheduleItem::FN_WHEN_COMPLETED("when_completed");

const QString TaskScheduleItem::KEY_ANONYMOUS("anonymous");
const QString TaskScheduleItem::KEY_COMPLETE("complete");
const QString TaskScheduleItem::KEY_DUE_BY("due_by");
const QString TaskScheduleItem::KEY_DUE_FROM("due_from");
const QString TaskScheduleItem::KEY_TABLE("table");
const QString TaskScheduleItem::KEY_SETTINGS("settings");
const QString TaskScheduleItem::KEY_WHEN_COMPLETED("when_completed");

// ============================================================================
// Creation
// ============================================================================

TaskScheduleItem::TaskScheduleItem(
    CamcopsApp& app, DatabaseManager& db, const int load_pk
) :
    DatabaseObject(
        app, db, TABLENAME, dbconst::PK_FIELDNAME, true, false, false, false
    )
{
    addField(FK_TASK_SCHEDULE, QMetaType::fromType<int>(), true);
    addField(FN_TASK_TABLE_NAME, QMetaType::fromType<QString>(), true);
    addField(FN_SETTINGS, QMetaType::fromType<QString>(), true);
    addField(FN_DUE_FROM, QMetaType::fromType<QString>(), true);
    addField(FN_DUE_BY, QMetaType::fromType<QString>(), true);
    addField(FN_COMPLETE, QMetaType::fromType<bool>(), true);
    addField(
        FN_ANONYMOUS,
        QMetaType::fromType<bool>(),
        true /* mandatory */,
        false /* unique */,
        false /* pk */,
        false /* default_value */
    );
    addField(FK_TASK, QMetaType::fromType<int>(), true);
    // ... PK of task in its table
    addField(FN_WHEN_COMPLETED, QMetaType::fromType<QDateTime>());

    load(load_pk);
}

TaskScheduleItem::TaskScheduleItem(
    const int schedule_fk,
    CamcopsApp& app,
    DatabaseManager& db,
    const QJsonObject& json_obj
) :
    TaskScheduleItem(app, db)
{
    setValue(FK_TASK_SCHEDULE, schedule_fk);
    setValue(FN_COMPLETE, false);
    setValue(FK_TASK, dbconst::NONEXISTENT_PK);
    setValuesFromJson(
        json_obj,
        QMap<QString, QString>{
            {FN_TASK_TABLE_NAME, KEY_TABLE},
            {FN_DUE_FROM, KEY_DUE_FROM},
            {FN_DUE_BY, KEY_DUE_BY},
            {FN_COMPLETE, KEY_COMPLETE},
            {FN_ANONYMOUS, KEY_ANONYMOUS},
            {FN_WHEN_COMPLETED, KEY_WHEN_COMPLETED},
        }
    );
    const QJsonObject settings = json_obj.value(KEY_SETTINGS).toObject();
    const QJsonDocument doc(settings);
    const QString json_string = doc.toJson(QJsonDocument::Compact);
    setValue(FN_SETTINGS, json_string);
    save();
}

// ============================================================================
// Information about schedule items
// ============================================================================

int TaskScheduleItem::id() const
{
    return pkvalueInt();
}

QDateTime TaskScheduleItem::dueFromUtc() const
{
    return value(FN_DUE_FROM).toDateTime();
}

QDateTime TaskScheduleItem::dueByUtc() const
{
    return value(FN_DUE_BY).toDateTime();
}

QDateTime TaskScheduleItem::dueFromLocal() const
{
    return dueFromUtc().toLocalTime();
}

QDateTime TaskScheduleItem::dueByLocal() const
{
    return dueByUtc().toLocalTime();
}

TaskPtr TaskScheduleItem::getTask() const
{
    const int task_id = value(FK_TASK).toInt();
    if (task_id != dbconst::NONEXISTENT_PK) {
        TaskFactory* factory = m_app.taskFactory();
        return factory->create(taskTableName(), task_id);
    }

    return nullptr;
}

QString TaskScheduleItem::taskTableName() const
{
    const QString table_name = valueString(FN_TASK_TABLE_NAME);

    return table_name.isEmpty() ? "?" : table_name;
}

QJsonObject TaskScheduleItem::settings() const
{
    // Should never be invalid as the whole JSON blob should have failed to
    // validate when the schedules were fetched from the server.
    // Also it's impossible to enter invalid JSON through the form when
    // creating the patient's task schedule.
    const QJsonDocument doc
        = QJsonDocument::fromJson(valueString(FN_SETTINGS).toUtf8());

    assert(!doc.isNull());

    return doc.object();
}

QString TaskScheduleItem::title() const
{
    TaskFactory* factory = m_app.taskFactory();
    TaskPtr task = factory->create(taskTableName());
    if (!task) {
        return "?";
    }

    return QString(task->longname());
}

QString TaskScheduleItem::subtitle() const
{
    const auto task_state = state();

    if (task_state == State::Completed) {
        const QDateTime when_completed = whenCompleted();
        if (when_completed.isNull()) {
            return QString(tr("Completed"));
        } else {
            const QString readable_datetime
                = when_completed.toString(datetime::LONG_DATETIME_FORMAT);
            return QString(tr("Completed at: %1").arg(readable_datetime));
        }
    }

    const QString readable_datetime
        = dueByLocal().toString(datetime::LONG_DATETIME_FORMAT);

    if (task_state == State::Started) {
        return QString(tr("Started, complete by %1")).arg(readable_datetime);
    }

    return QString(tr("Complete by %1")).arg(readable_datetime);
}

bool TaskScheduleItem::isEditable() const
{
    const auto task_state = state();

    return task_state == State::Started || task_state == State::Due;
}

TaskScheduleItem::State TaskScheduleItem::state() const
{
    if (isComplete()) {
        return State::Completed;
    }

    const auto now = QDateTime::currentDateTimeUtc();
    const auto due_by = dueByUtc();

    if (now > due_by) {
        return State::Missed;
    }

    TaskPtr task = getTask();

    if (task) {
        return State::Started;
    }

    const auto due_from = dueFromUtc();

    if (now >= due_from && now <= due_by) {
        return State::Due;
    }

    return State::Future;
}

bool TaskScheduleItem::isComplete() const
{
    return valueBool(FN_COMPLETE);
}

QDateTime TaskScheduleItem::whenCompleted() const
{
    return valueDateTime(FN_WHEN_COMPLETED);
}

void TaskScheduleItem::setComplete(
    const bool complete, const QDateTime& when_completed
)
{
    setValue(FN_COMPLETE, complete);
    setValue(FN_WHEN_COMPLETED, when_completed);
    save();
}

bool TaskScheduleItem::isAnonymous() const
{
    return valueBool(FN_ANONYMOUS);
}

void TaskScheduleItem::setAnonymous(const bool anonymous)
{
    setValue(FN_ANONYMOUS, anonymous);
    save();
}

void TaskScheduleItem::setTask(const int task_id)
{
    setValue(FK_TASK, task_id);
    save();
}

bool TaskScheduleItem::isIncompleteAndCurrent() const
{
    return state() == State::Started;
}
