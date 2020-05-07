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

#pragma once
#include "db/databaseobject.h"
#include <QJsonArray>
#include <QJsonObject>
#include <QVector>

class TaskSchedule : public DatabaseObject
{
    Q_OBJECT
public:

    // ------------------------------------------------------------------------
    // Creation
    // ------------------------------------------------------------------------

    TaskSchedule(CamcopsApp& app, DatabaseManager& db);
    TaskSchedule(CamcopsApp& app, DatabaseManager& db,
                 const QJsonObject json_obj);
    void addJsonFields(const QJsonObject json_obj);
    void addItems(const QJsonArray items_json_array);


    // ------------------------------------------------------------------------
    // Ancillary management
    // ------------------------------------------------------------------------

    virtual void loadAllAncillary(int pk) override;
    virtual QVector<DatabaseObjectPtr> getAncillarySpecimens() const override;
    virtual QVector<DatabaseObjectPtr> getAllAncillary() const override;


    // ============================================================================
    // Information about schedules
    // ============================================================================

    int id() const;
    QString name() const;

protected:
    // Schedule items
    QVector<TaskScheduleItemPtr> m_items;

public:
    static const QString TABLENAME;
    static const QString FN_NAME;

    static const QString KEY_NAME;
    static const QString KEY_TASK_SCHEDULE_ITEMS;
};
