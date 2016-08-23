#pragma once
#include <type_traits>  // for std::is_base_of
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
// See also:
// - https://en.wikipedia.org/wiki/Curiously_recurring_template_pattern

// ===========================================================================
// We happen to want to know about this too, for the proxy definitions:
// ===========================================================================

class CamcopsApp;
class TaskFactory;


// ===========================================================================
// Base "descriptor" class, so we can do more things with the class as an
// entity than just instantiate one.
// ===========================================================================

class TaskProxy
{
public:
    TaskProxy(TaskFactory& factory);  // Registers itself with the factory.
    // We do want to create instances...
    virtual TaskPtr create(const QSqlDatabase& db,
                           int load_pk = DbConst::NONEXISTENT_PK) const = 0;
    virtual TaskPtrList fetch(const QSqlDatabase& db,
                              int patient_id = DbConst::NONEXISTENT_PK) const = 0;
protected:
    virtual TaskPtrList fetchWhere(const QSqlDatabase& db,
                                   const WhereConditions& where) const = 0;
};


// ===========================================================================
// Wrapper that makes a TaskProxy out of any Task-derived class
// ===========================================================================

template<class Derived> class TaskRegistrar : public TaskProxy
{
    static_assert(std::is_base_of<Task, Derived>::value,
                  "You can only use Task-derived classes here.");
public:
    TaskRegistrar(TaskFactory& factory) :
        TaskProxy(factory)  // registers proxy with factory (see TaskProxy::TaskProxy)
    {}

    TaskPtr create(const QSqlDatabase& db,
                   int load_pk = DbConst::NONEXISTENT_PK) const override
    {
        // Create a single instance of a task (optionally, loading it)
        return TaskPtr(new Derived(db, load_pk));
    }

    TaskPtrList fetch(const QSqlDatabase& db,
                      int patient_id = DbConst::NONEXISTENT_PK) const override
    {
        // Fetch multiple tasks, either matching a patient_id, or all for
        // the task type.
        Derived specimen(db, DbConst::NONEXISTENT_PK);
        bool anonymous = specimen.isAnonymous();
        if (patient_id != DbConst::NONEXISTENT_PK && anonymous) {
            // No anonymous tasks will match a specific patient.
            return TaskPtrList();
        }
        WhereConditions where;
        if (patient_id != DbConst::NONEXISTENT_PK) {
            where[PATIENT_FK_FIELDNAME] = QVariant(patient_id);
        }
        return fetchWhere(db, where);
    }

protected:
    TaskPtrList fetchWhere(const QSqlDatabase& db,
                           const WhereConditions& where) const override
    {
        // Fetch multiple tasks according to the field/value "where" criteria
        TaskPtrList tasklist;
        Derived specimen(db, DbConst::NONEXISTENT_PK);
        SqlArgs sqlargs = specimen.fetchQuerySql(where);
        QSqlQuery query(db);
        bool success = DbFunc::execQuery(query, sqlargs);
        if (success) {  // success check may be redundant (cf. while clause)
            while (query.next()) {
                TaskPtr p_new_task(new Derived(db, DbConst::NONEXISTENT_PK));
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
    TaskPtr create(const QString& key,
                   int load_pk = DbConst::NONEXISTENT_PK) const;
    QString shortname(const QString& key) const;
    QString longname(const QString& key) const;
    void makeTables(const QString& key) const;
    TaskPtrList fetch(const QString& tablename = "", bool sort = true) const;
protected:
    CamcopsApp& m_app;
    QStringList m_tablenames;
    QList<ProxyType> m_initial_proxy_list;
    MapType m_map;
};


typedef QSharedPointer<TaskFactory> TaskFactoryPtr;
