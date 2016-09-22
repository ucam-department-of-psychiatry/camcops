#pragma once
#include <type_traits>  // for std::is_base_of
#include <QList>
#include <QMap>
#include <QSharedPointer>
#include <QString>
#include <QStringList>
#include "common/dbconstants.h"
#include "task.h"
#include "taskproxy.h"
#include "taskregistrar.h"

class CamcopsApp;

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
        ProxyType proxy;
    };
    using MapType = QMap<QString, TaskCache>;
    using MapIteratorType = QMapIterator<QString, TaskCache>;
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


using TaskFactoryPtr = QSharedPointer<TaskFactory>;
