#pragma once
#include <QList>
#include <QMap>
#include <QSharedPointer>
#include <QString>
#include <QStringList>
#include <QSqlDatabase>
#include <QSqlQuery>
#include "common/dbconstants.h"
#include "lib/dbfunc.h"
#include "lib/uifunc.h"
#include "tasklib/task.h"


// Two of the best articles on this sort of factory method in C++:
// - http://accu.org/index.php/journals/597
// - http://www.drdobbs.com/cpp/self-registering-objects-in-c/184410633?pgno=1
// Note that:
// - To do more than one thing, and to deal with classes in the abstract
//   without having to instantiate one, we use a proxy class.

// ===========================================================================
// We happen to want to know about this too, for the proxy definitions:
// ===========================================================================

class CamcopsApp;
class TaskFactory;

// ===========================================================================
// Typedefs
// ===========================================================================

typedef QSharedPointer<Task> TaskPtr;
typedef QList<TaskPtr> TaskPtrList;


// ===========================================================================
// Base "descriptor" class, so we can do more things with the class as an
// entity than just instantiate one.
// ===========================================================================

class TaskProxy
{
public:
    TaskProxy(TaskFactory& factory);  // Registers itself with the factory.
    // We do want to create instances...
    virtual TaskPtr createObject(const QSqlDatabase& db,
                                 int load_pk = NONEXISTENT_PK) const = 0;
    // But we might do other things without creating an instance, using
    // static member functions of Task...
    // ... no, too much hassle; work with instances (see notes on database
    // objects)

    virtual TaskPtrList fetch(const QSqlDatabase& db,
                              int patient_id = NONEXISTENT_PK) const = 0;
    virtual TaskPtrList fetchWhere(const QSqlDatabase& db,
                                   QMap<QString, QVariant> where) const = 0;
};


// ===========================================================================
// Wrapper that makes a TaskProxy out of any Task-derived class
// ===========================================================================

template<class Derived> class TaskRegistrar : public TaskProxy
{
public:
    TaskRegistrar(TaskFactory& factory) :
        TaskProxy(factory)  // does the registration; see TaskProxy::TaskProxy
    {}
    TaskPtr createObject(const QSqlDatabase& db,
                         int load_pk = NONEXISTENT_PK) const
    {
        // Create a single instance of a task (optionally, loading it)
        return TaskPtr(new Derived(db, load_pk));
    }
    TaskPtrList fetch(const QSqlDatabase& db,
                      int patient_id = NONEXISTENT_PK) const
    {
        // Fetch multiple tasks, either matching a patient_id, or all for
        // the task type.
        Derived specimen(db, NONEXISTENT_PK);
        bool anonymous = specimen.isAnonymous();
        if (patient_id != NONEXISTENT_PK && anonymous) {
            // No anonymous tasks will match.
            return TaskPtrList();
        }
        QMap<QString, QVariant> where;
        if (patient_id != NONEXISTENT_PK) {
            where[PATIENT_FK_FIELDNAME] = QVariant(patient_id);
        }
        return fetchWhere(db, where);
    }
    TaskPtrList fetchWhere(const QSqlDatabase& db,
                            QMap<QString, QVariant> where) const
    {
        // Fetch multiple tasks according to the field/value "where" criteria
        // CALLER TAKES OWNERSHIP OF POINTERS
        TaskPtrList tasklist;

        // Build SQL
        Derived specimen(db, NONEXISTENT_PK);
        QStringList fieldnames = specimen.getFieldnames();
        QStringList delimited_fieldnames;
        for (int i = 0; i < fieldnames.size(); ++i) {
            delimited_fieldnames.append(delimit(fieldnames.at(i)));
        }
        QString sql = (
            "SELECT " + delimited_fieldnames.join(", ") + " FROM " +
            delimit(specimen.tablename())
        );
        QList<QVariant> args;
        addWhereClause(where, sql, args);

        // Execute SQL
        QSqlQuery query(db);
        bool success = execQuery(query, sql, args);
        if (success) {
            while (query.next()) {
                TaskPtr p_new_task(new Derived(db, NONEXISTENT_PK));
                p_new_task->setFromQuery(query, true);
                tasklist.append(p_new_task);
            }
        }
        return tasklist;
    }
};


// ===========================================================================
// The factory does the work.
// ===========================================================================

class TaskFactory  // Stores registered copies of TaskProxy*
{
public:
    typedef const TaskProxy* ProxyType;
    class TaskCache
    {
    public:
        QString tablename;
        QString shortname;
        QString longname;
        ProxyType proxy;
    };
    typedef QMap<QString, TaskCache> MapType;
    typedef QMapIterator<QString, TaskCache> MapIteratorType;
public:
    TaskFactory(CamcopsApp& app);
    // Making the registry
    void registerTask(ProxyType proxy);
    void finishRegistration();
    // Operations relating to the whole registry
    QStringList tablenames() const;
    void makeAllTables() const;
    // Operations relating to specific tasks
    TaskPtr build(const QString& key, int load_pk = NONEXISTENT_PK) const;
    QString getShortName(const QString& key) const;
    QString getLongName(const QString& key) const;
    void makeTables(const QString& key) const;
    TaskPtrList fetch(const QString& tablename = "",
                      int patient_id = NONEXISTENT_PK) const;
protected:
    CamcopsApp& m_app;
    QStringList m_tablenames;
    QList<ProxyType> m_initial_proxy_list;
    MapType m_map;
};
