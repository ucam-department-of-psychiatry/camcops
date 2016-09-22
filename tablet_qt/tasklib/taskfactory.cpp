#include "taskfactory.h"
#include <algorithm>
#include "common/camcopsapp.h"
#include "task.h"
#include "tasksorter.h"


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
        TaskPtr p_task = proxy->create(m_app.db());
        TaskCache cache;
        cache.tablename = p_task->tablename();
        cache.shortname = p_task->shortname();
        cache.longname = p_task->longname();
        cache.proxy = proxy;
        if (m_map.contains(cache.tablename)) {
            QString msg = QString(
                "BAD TASK REGISTRATION: table %1 being registered for a second"
                " time by task with longname %2").arg(
                    cache.tablename, cache.longname);
            qFatal("%s", qPrintable(msg));
        }
        m_map.insert(cache.tablename, cache);  // tablenames are the keys
        m_tablenames.append(cache.tablename);
    }
    m_tablenames.sort();
}


QStringList TaskFactory::tablenames() const
{
    return m_tablenames;
}


TaskPtr TaskFactory::create(const QString& key, int load_pk) const
{
    if (!m_map.contains(key)) {
        qWarning().nospace() << "TaskFactory::create(" << key << ", "
                             << load_pk << ")" << "... no such task";
        return TaskPtr(nullptr);
    }
    qDebug().nospace() << "TaskFactory::create(" << key << ", "
                       << load_pk << ")";
    ProxyType proxy = m_map[key].proxy;
    return proxy->create(m_app.db(), load_pk);
}


void TaskFactory::makeAllTables() const
{
    MapIteratorType it(m_map);
    while (it.hasNext()) {
        it.next();
        ProxyType proxy = it.value().proxy;
        TaskPtr p_task = proxy->create(m_app.db());
        p_task->makeTables();
    }
}


QString TaskFactory::shortname(const QString& key) const
{
    if (!m_map.contains(key)) {
        qWarning() << "Bad task: " << key;
        return nullptr;
    }
    return m_map[key].shortname;
}


QString TaskFactory::longname(const QString& key) const
{
    if (!m_map.contains(key)) {
        qWarning() << "Bad task: " << key;
        return nullptr;
    }
    return m_map[key].longname;
}


void TaskFactory::makeTables(const QString& key) const
{
    TaskPtr p_task = create(key);
    if (!p_task) {
        return;
    }
    p_task->makeTables();
}


TaskPtrList TaskFactory::fetch(const QString& tablename, bool sort) const
{
    int patient_id = m_app.currentPatientId();
    // *** implement any necessary locked/no-patient filtering here; think; may be OK, but maybe not
    TaskPtrList tasklist;
    if (tablename.isEmpty()) {
        // All tasks
        MapIteratorType it(m_map);
        while (it.hasNext()) {
            it.next();
            ProxyType proxy = it.value().proxy;
            tasklist += proxy->fetch(m_app.db(), patient_id);
        }
    } else if (!m_map.contains(tablename)) {
        // Duff task
        qWarning() << "Bad task: " << tablename;
    } else {
        // Specific task
        ProxyType proxy = m_map[tablename].proxy;
        tasklist = proxy->fetch(m_app.db(), patient_id);
    }

    if (sort) {
        qDebug() << "Starting sort...";
        qSort(tasklist.begin(), tasklist.end(), TaskSorter());
        qDebug() << "... finished sort";
    }

    return tasklist;
}
