#include "task.h"
#include <QObject>
#include <QVariant>
#include "common/camcopsapp.h"
#include "lib/datetimefunc.h"

const QString PATIENT_FK_FIELDNAME("patient_id");


Task::Task(CamcopsApp& app,
           const QSqlDatabase& db,
           const QString& tablename,
           bool is_anonymous,
           bool has_clinician,
           bool has_respondent) :
    DatabaseObject(db, tablename, DbConst::PK_FIELDNAME, true, true),
    m_app(app)
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
    if (!value(PATIENT_FK_FIELDNAME).isNull()) {
        qWarning() << "Setting patient ID, but it was already set";
    }
    setValue(PATIENT_FK_FIELDNAME, patient_id);
}


QString Task::menutitle() const
{
    return QString("%1 (%2)").arg(longname(), shortname());
}


bool Task::hasExtraStrings() const
{
    return m_app.hasExtraStrings(xstringTaskname());
}


QString Task::infoFilenameStem() const
{
    return m_tablename;
}


QString Task::xstringTaskname() const
{
    return m_tablename;
}


QString Task::instanceTitle() const
{
    if (isAnonymous()) {
        return QString("%1, %2").arg(
            shortname(),
            whenCreated().toString(DateTime::SHORT_DATETIME_FORMAT));
    } else {
        return QString("%1, ***PATIENT***, %2").arg(
            shortname(),
            // *** patient info
            whenCreated().toString(DateTime::SHORT_DATETIME_FORMAT));
    }
}


void Task::makeTables()
{
    makeTable();
    makeAncillaryTables();
}


bool Task::load(int pk)
{
    if (pk == DbConst::NONEXISTENT_PK) {
        return false;
    }
    return DatabaseObject::load(pk);
}


QDateTime Task::whenCreated() const
{
    return value(DbConst::CREATION_TIMESTAMP_FIELDNAME)
        .toDateTime();
}


QString Task::summaryWithCompleteSuffix() const
{
    QString result = summary();
    if (!isComplete()) {
        result += tr(" (INCOMPLETE)");
    }
    return result;
}


QString Task::summary() const
{
    return "MISSING SUMMARY";
}


QString Task::detail() const
{
    return recordSummary();
}


OpenableWidget* Task::editor(bool read_only)
{
    Q_UNUSED(read_only)
    qWarning() << "Base class Task::edit called - not a good thing!";
    return nullptr;
}


QString Task::xstring(const QString &stringname) const
{
    return m_app.xstring(xstringTaskname(), stringname);
}
