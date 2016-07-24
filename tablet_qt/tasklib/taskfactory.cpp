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
        Task* pTask = proxy->createObject(*m_app.m_pdb);
        TaskCache cache;
        cache.tablename = pTask->tablename();
        cache.shortname = pTask->shortname();
        cache.longname = pTask->longname();
        cache.proxy = proxy;
        m_map.insert(cache.tablename, cache);
        m_tablenames.append(cache.tablename);
        delete pTask;
    }
    m_tablenames.sort();
}

QStringList TaskFactory::tablenames() const
{
    return m_tablenames;
}

Task* TaskFactory::build(const QString& key, int loadPk) const
{
    if (!m_map.contains(key)) {
        return NULL;
    }
    ProxyType proxy = m_map[key].proxy;
    return proxy->createObject(*m_app.m_pdb, loadPk);
}

void TaskFactory::makeAllTables() const
{
    MapIteratorType it(m_map);
    while (it.hasNext()) {
        it.next();
        ProxyType proxy = it.value().proxy;
        Task* pTask = proxy->createObject(*m_app.m_pdb);
        pTask->makeTables();
        delete pTask;
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
    Task* pTask = build(key);
    if (!pTask) {
        return;
    }
    pTask->makeTables();
    delete pTask;
}
