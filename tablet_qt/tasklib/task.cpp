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

void Task::initDatabaseObject(int loadPk)
{
    m_pDbObject = makeDatabaseObject();
    if (loadPk != NONEXISTENT_PK) {
        m_pDbObject->loadByPk(loadPk);
    }
}

DatabaseObject* Task::makeBaseDatabaseObject()
{
    DatabaseObject* dbo = new DatabaseObject(tablename(), m_db);
    dbo->addField("id", QVariant::Int, true, true, true);  // PK
    dbo->addField("when_created", QVariant::DateTime);
    dbo->addField("firstexit_is_finish", QVariant::Bool);
    dbo->addField("firstexit_is_abort", QVariant::Bool);
    dbo->addField("when_firstexit", QVariant::DateTime);
    Field editing_time_s("editing_time_s", QVariant::Double);
    editing_time_s.setDefaultValue(0.0);
    dbo->addField(editing_time_s);

    if (!anonymous()) {
        dbo->addField(PATIENT_FK_FIELDNAME, QVariant::Int);
    }
    if (hasClinician()) {
        dbo->addField("clinician_specialty", QVariant::String);
        dbo->addField("clinician_name", QVariant::String);
        dbo->addField("clinician_professional_registration", QVariant::String);
        dbo->addField("clinician_post", QVariant::String);
        dbo->addField("clinician_service", QVariant::String);
        dbo->addField("clinician_contact_details", QVariant::String);
    }
    if (hasRespondent()) {
        dbo->addField("respondent_name", QVariant::String);
        dbo->addField("respondent_relationship", QVariant::String);
    }
    return dbo;
}

DatabaseObject* Task::makeDatabaseObject()
{
    DatabaseObject* dbo = makeBaseDatabaseObject();
    return dbo;
}

void Task::setEditable(bool editable)
{
    m_editable = editable;
}

void Task::setCrippled(bool crippled)
{
    m_crippled = crippled;
}

QVariant Task::value(const QString& fieldname)
{
    return m_pDbObject->value(fieldname);
}

bool Task::setValue(const QString& fieldname, const QVariant& value)
{
    return m_pDbObject->setValue(fieldname, value);
}

void Task::makeTables()
{
    m_pDbObject->makeTable();
    makeAncillaryTables();
}

QDebug operator<<(QDebug debug, const Task& t)
{
    debug.nospace() << *t.m_pDbObject;
    return debug;
}
