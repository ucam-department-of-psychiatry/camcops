/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
#include <type_traits>  // for std::is_base_of
#include <QList>
#include <QMap>
#include <QSharedPointer>
#include <QString>
#include <QStringList>
#include "common/dbconst.h"
#include "task.h"
#include "taskproxy.h"
#include "taskregistrar.h"

class CamcopsApp;
class Version;

// Two of the best articles on this sort of factory method in C++:
// - http://accu.org/index.php/journals/597
// - http://www.drdobbs.com/cpp/self-registering-objects-in-c/184410633?pgno=1
// Note that:
// - To do more than one thing, and to deal with classes in the abstract
//   without having to instantiate one, we use a proxy class.
// See also:
// - https://en.wikipedia.org/wiki/Curiously_recurring_template_pattern

// ===========================================================================
// The factory does the work.
// ===========================================================================

class TaskFactory  // Stores registered copies of TaskProxy*
{
public:
    using ProxyType = const TaskProxy*;
    class TaskCache
    {
    public:
        QString tablename;
        QString shortname;
        QString longname;
        QStringList alltables;
        bool anonymous;
        ProxyType proxy;
    };
    using MapType = QMap<QString, TaskCache>;
    using MapIteratorType = QMapIterator<QString, TaskCache>;
    enum class TaskClassSortMethod {
        Tablename,
        Shortname,
        Longname,
    };
public:
    TaskFactory(CamcopsApp& app);
    // Making the registry
    void registerTask(ProxyType proxy);
    void finishRegistration();
    // Operations relating to the whole registry
    QStringList tablenames(TaskClassSortMethod sort_method =
            TaskClassSortMethod::Tablename) const;
    QStringList allTablenames() const;
    void makeAllTables() const;
    void upgradeDatabase(const Version& old_version,
                         const Version& new_version);
    // Operations relating to specific tasks
    TaskPtr create(const QString& key,
                   int load_pk = dbconst::NONEXISTENT_PK) const;
    QString shortname(const QString& key) const;
    QString longname(const QString& key) const;
    void makeTables(const QString& key) const;
    TaskPtrList fetch(const QString& tablename = "", bool sort = true) const;
    TaskPtrList fetchAllForPatient(int patient_id) const;
    TaskPtrList allSpecimens() const;
    TaskPtrList allSpecimensExceptAnonymous() const;
    Version minimumServerVersion(const QString& tablename) const;  // main or sub-table
protected:
    CamcopsApp& m_app;
    QStringList m_tablenames;
    QStringList m_all_tablenames;
    QVector<ProxyType> m_initial_proxy_list;
    MapType m_map;  // maps tablename to TaskCache
};
