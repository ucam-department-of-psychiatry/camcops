#pragma once
#include <QList>
#include <QMap>
#include <QString>
#include <QStringList>
#include <QSqlDatabase>
#include "common/db_constants.h"
#include "lib/uifunc.h"


// Two of the best articles on this sort of factory method in C++:
// - http://accu.org/index.php/journals/597
// - http://www.drdobbs.com/cpp/self-registering-objects-in-c/184410633?pgno=1
// Note that:
// - To do more than one thing, and to deal with classes in the abstract
//   without having to instantiate one, we use a proxy class.

// ===========================================================================
// The base class of the things we'll build.
// ===========================================================================

class Task;

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
    virtual Task* createObject(const QSqlDatabase& db,
                               int load_pk = NONEXISTENT_PK) const = 0;
    // But we might do other things without creating an instance, using
    // static member functions of Task...
    // ... no, too much hassle; work with instances (see notes in task.h)
};


// ===========================================================================
// Wrapper that makes a TaskProxy out of any Task-derived class
// ===========================================================================

template <class Derived> class TaskRegistrar : public TaskProxy
{
public:
    TaskRegistrar(TaskFactory& factory) :
        TaskProxy(factory)  // does the registration
    {}
    Task* createObject(const QSqlDatabase& db,
                       int load_pk = NONEXISTENT_PK) const
    {
        return new Derived(db, load_pk);
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
    Task* build(const QString& key, int load_pk = NONEXISTENT_PK) const;
    QString getShortName(const QString& key) const;
    QString getLongName(const QString& key) const;
    void makeTables(const QString& key) const;
protected:
    CamcopsApp& m_app;
    QStringList m_tablenames;
    QList<ProxyType> m_initial_proxy_list;
    MapType m_map;
};
