#include "taskfactory.h"
#include <algorithm>
#include "common/camcops_app.h"
#include "task.h"


// ===========================================================================
// TaskProxy
// ===========================================================================

TaskProxy::TaskProxy(TaskFactory& factory)
{
    factory.registerTask(this);
}


// ===========================================================================
// TaskFactory
// ===========================================================================

TaskFactory::TaskFactory(CamcopsApp& app) :
    m_app(app)
{
}


void TaskFactory::registerTask(ProxyType proxy)
{
    m_initial_proxy_list.append(proxy);
    // We are here from WITHIN A CONSTRUCTOR (TaskProxy::TaskProxy), so don't
    // call back to the proxy.
}


void TaskFactory::finishRegistration()
{
    for (int i = 0; i < m_initial_proxy_list.size(); ++i) {
        ProxyType proxy = m_initial_proxy_list[i];
        TaskPtr p_task = proxy->createObject(m_app.m_db);
        TaskCache cache;
        cache.tablename = p_task->tablename();
        cache.shortname = p_task->shortname();
        cache.longname = p_task->longname();
        cache.proxy = proxy;
        m_map.insert(cache.tablename, cache);  // tablenames are the keys
        m_tablenames.append(cache.tablename);
    }
    m_tablenames.sort();
}


QStringList TaskFactory::tablenames() const
{
    return m_tablenames;
}


TaskPtr TaskFactory::build(const QString& key, int load_pk) const
{
    if (!m_map.contains(key)) {
        qWarning().nospace() << "TaskFactoryBuild(" << key << ", "
                             << load_pk << ")" << "... no such task";
        return TaskPtr(nullptr);
    }
    qDebug().nospace() << "TaskFactoryBuild(" << key << ", "


                       << load_pk << ")";
    ProxyType proxy = m_map[key].proxy;
    return proxy->createObject(m_app.m_db, load_pk);
}


void TaskFactory::makeAllTables() const
{
    MapIteratorType it(m_map);
    while (it.hasNext()) {
        it.next();
        ProxyType proxy = it.value().proxy;
        TaskPtr p_task = proxy->createObject(m_app.m_db);
        p_task->makeTables();
        p_task->save(); // *** FOR TESTING ONLY!
    }
}


QString TaskFactory::getShortName(const QString& key) const
{
    if (!m_map.contains(key)) {
        qWarning() << "Bad task: " << key;
        return nullptr;
    }
    return m_map[key].shortname;
}


QString TaskFactory::getLongName(const QString& key) const
{
    if (!m_map.contains(key)) {
        qWarning() << "Bad task: " << key;
        return nullptr;
    }
    return m_map[key].longname;
}


void TaskFactory::makeTables(const QString& key) const
{
    TaskPtr p_task = build(key);
    if (!p_task) {
        return;
    }
    p_task->makeTables();
}


TaskPtrList TaskFactory::fetch(const QString& tablename, int patient_id)
{
    if (tablename.isEmpty()) {
        // All tasks
        TaskPtrList tasklist;
        MapIteratorType it(m_map);
        while (it.hasNext()) {
            it.next();
            ProxyType proxy = it.value().proxy;
            tasklist += proxy->fetch(m_app.m_db, patient_id);
        }
        return tasklist;
    }
    if (!m_map.contains(tablename)) {
        // Duff task
        qWarning() << "Bad task: " << tablename;
        return TaskPtrList();
    }
    // Specific task
    ProxyType proxy = m_map[tablename].proxy;
    return proxy->fetch(m_app.m_db, patient_id);
}
