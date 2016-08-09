#include "task.h"
#include <QDebug>
#include <QVariant>


Task::Task(const QSqlDatabase& db) :
    m_db(db),
    m_editable(true),
    m_crippled(false)
{
    // WATCH OUT: you can't call a derived class's overloaded function
    // here; its vtable is incomplete.
    // http://stackoverflow.com/questions/6561429/calling-virtual-function-of-derived-class-from-base-class-constructor
}


void Task::loadByPk(int loadPk)
{
    if (m_p_dbobject == NULL) {
        return;
    }
    if (loadPk != NONEXISTENT_PK) {
        m_p_dbobject->loadByPk(loadPk);
    }
}


void Task::setEditable(bool editable)
{
    m_editable = editable;
}


void Task::setCrippled(bool crippled)
{
    m_crippled = crippled;
}


QVariant Task::getValue(const QString& fieldname)
{
    return m_p_dbobject->getValue(fieldname);
}


bool Task::setValue(const QString& fieldname, const QVariant& value)
{
    return m_p_dbobject->setValue(fieldname, value);
}


void Task::makeTables()
{
    m_p_dbobject->makeTable();
    makeAncillaryTables();
}


QDebug operator<<(QDebug debug, const Task& t)
{
    debug.nospace() << *t.m_p_dbobject;
    return debug;
}
