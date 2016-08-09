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
    // We are here from WITHIN A CONSTRUCTOR, so don't call back
    // to the proxy.
}


void TaskFactory::finishRegistration()
{
    for (int i = 0; i < m_initial_proxy_list.size(); ++i) {
        ProxyType proxy = m_initial_proxy_list[i];
        Task* p_task = proxy->createObject(m_app.m_db);
        TaskCache cache;
        cache.tablename = p_task->tablename();
        cache.shortname = p_task->shortname();
        cache.longname = p_task->longname();
        cache.proxy = proxy;
        m_map.insert(cache.tablename, cache);
        m_tablenames.append(cache.tablename);
        delete p_task;
    }
    m_tablenames.sort();
}


QStringList TaskFactory::tablenames() const
{
    return m_tablenames;
}


Task* TaskFactory::build(const QString& key, int load_pk) const
{
    qDebug() << "TaskFactoryBuild(" << key << ", " << load_pk << ")";
    if (!m_map.contains(key)) {
        qDebug() << "... no such task";
        return NULL;
    }
    ProxyType proxy = m_map[key].proxy;
    return proxy->createObject(m_app.m_db, load_pk);
}


void TaskFactory::makeAllTables() const
{
    MapIteratorType it(m_map);
    while (it.hasNext()) {
        it.next();
        ProxyType proxy = it.value().proxy;
        Task* p_task = proxy->createObject(m_app.m_db);
        p_task->makeTables();
        delete p_task;
    }
}


QString TaskFactory::getShortName(const QString& key) const
{
    if (!m_map.contains(key)) {
        return NULL;
    }
    return m_map[key].shortname;
}


QString TaskFactory::getLongName(const QString& key) const
{
    if (!m_map.contains(key)) {
        return NULL;
    }
    return m_map[key].longname;
}


void TaskFactory::makeTables(const QString& key) const
{
    Task* p_task = build(key);
    if (!p_task) {
        return;
    }
    p_task->makeTables();
    delete p_task;
}
