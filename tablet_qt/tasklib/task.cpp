#include "task.h"
#include <QObject>
#include <QVariant>
#include "lib/datetimefunc.h"

const QString PATIENT_FK_FIELDNAME = "patient_id";


Task::Task(const QSqlDatabase& db,
           const QString& tablename,
           bool is_anonymous,
           bool has_clinician,
           bool has_respondent) :
    DatabaseObject(tablename, db, true, true, true)
{
    // WATCH OUT: you can't call a derived class's overloaded function
    // here; its vtable is incomplete.
    // http://stackoverflow.com/questions/6561429/calling-virtual-function-of-derived-class-from-base-class-constructor

    addField("firstexit_is_finish", QVariant::Bool);
    addField("firstexit_is_abort", QVariant::Bool);
    addField("when_firstexit", QVariant::DateTime);
    addField(Field("editing_time_s", QVariant::Double).setDefaultValue(0.0));

    if (!is_anonymous) {
        addField(PATIENT_FK_FIELDNAME, QVariant::Int);
    }
    if (has_clinician) {
        addField("clinician_specialty", QVariant::String);
        addField("clinician_name", QVariant::String);
        addField("clinician_professional_registration", QVariant::String);
        addField("clinician_post", QVariant::String);
        addField("clinician_service", QVariant::String);
        addField("clinician_contact_details", QVariant::String);
    }
    if (has_respondent) {
        addField("respondent_name", QVariant::String);
        addField("respondent_relationship", QVariant::String);
    }
}


void Task::setPatient(int patient_id)
{
    if (isAnonymous()) {
        qCritical() << "Attempt to set patient ID for an anonymous task";
        return;
    }
    if (!getValue(PATIENT_FK_FIELDNAME).isNull()) {
        qWarning() << "Setting patient ID, but it was already set";
    }
    setValue(PATIENT_FK_FIELDNAME, patient_id);
}


void Task::makeTables()
{
    makeTable();
    makeAncillaryTables();
}


bool Task::load(int pk)
{
    if (pk == NONEXISTENT_PK) {
        return false;
    }
    return DatabaseObject::load(pk);
}


QString Task::whenCreatedMenuFormat() const
{
    return "boo! ***";
    return getValue(CREATION_TIMESTAMP_FIELDNAME)
        .toDateTime()
        .toString(SHORT_DATETIME_FORMAT);
}


QString Task::getSummaryWithCompleteSuffix() const
{
    QString result = getSummary();
    if (!isComplete()) {
        result += QObject::tr(" (INCOMPLETE)");
    }
    return result;
}
