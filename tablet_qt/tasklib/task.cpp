#include "task.h"
#include <QObject>
#include <QVariant>
#include "common/camcopsapp.h"
#include "dbobjects/patient.h"
#include "lib/datetimefunc.h"
#include "lib/uifunc.h"

const QString PATIENT_FK_FIELDNAME("patient_id");
const QString FIRSTEXIT_IS_FINISH_FIELDNAME("firstexit_is_finish");
const QString FIRSTEXIT_IS_ABORT_FIELDNAME("firstexit_is_abort");
const QString WHEN_FIRSTEXIT_FIELDNAME("when_firstexit");
const QString EDITING_TIME_S_FIELDNAME("editing_time_s");


Task::Task(CamcopsApp& app,
           const QSqlDatabase& db,
           const QString& tablename,
           bool is_anonymous,
           bool has_clinician,
           bool has_respondent) :
    DatabaseObject(db, tablename, DbConst::PK_FIELDNAME, true, true),
    m_app(app),
    m_patient(nullptr),
    m_editing(false)
{
    // WATCH OUT: you can't call a derived class's overloaded function
    // here; its vtable is incomplete.
    // http://stackoverflow.com/questions/6561429/calling-virtual-function-of-derived-class-from-base-class-constructor

    addField(FIRSTEXIT_IS_FINISH_FIELDNAME, QVariant::Bool);
    addField(FIRSTEXIT_IS_ABORT_FIELDNAME, QVariant::Bool);
    addField(WHEN_FIRSTEXIT_FIELDNAME, QVariant::DateTime);
    addField(Field(EDITING_TIME_S_FIELDNAME, QVariant::Double).setDefaultValue(0.0));

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


bool Task::save()
{
    // Sanity checks before we permit saving
    if (!isAnonymous() && value(PATIENT_FK_FIELDNAME).isNull()) {
        UiFunc::stopApp("Task has no patient ID (and is not anonymous); "
                        "cannot save");
    }
    return DatabaseObject::save();
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


void Task::editStarted()
{
    m_editing = true;
    m_editing_started = DateTime::now();
}


void Task::editFinished(bool aborted)
{
    if (!m_editing) {
        qDebug() << Q_FUNC_INFO << "wasn't editing";
        return;
    }
    m_editing = false;
    // Time
    QDateTime now = DateTime::now();
    double editing_time_s = valueDouble(EDITING_TIME_S_FIELDNAME);
    editing_time_s += DateTime::doubleSecondsFrom(m_editing_started, now);
    setValue(EDITING_TIME_S_FIELDNAME, editing_time_s);
    // Exit flags
    if (!valueBool(FIRSTEXIT_IS_FINISH_FIELDNAME)
            && !valueBool(FIRSTEXIT_IS_ABORT_FIELDNAME)) {
        // First exit, so set flags:
        if (aborted) {
            setValue(FIRSTEXIT_IS_ABORT_FIELDNAME, true);
        } else {
            setValue(FIRSTEXIT_IS_FINISH_FIELDNAME, true);
        }
    }
    save();
}


void Task::setPatient(int patient_id)
{
    // It's a really dangerous thing to set a patient ID invalidly, so this
    // function will just stop the app if something stupid is attempted.
    if (isAnonymous()) {
        UiFunc::stopApp("Attempt to set patient ID for an anonymous task");
    }
    if (!value(PATIENT_FK_FIELDNAME).isNull()) {
        UiFunc::stopApp("Setting patient ID, but it was already set");
    }
    setValue(PATIENT_FK_FIELDNAME, patient_id);
    m_patient = QSharedPointer<Patient>(nullptr);
}


Patient* Task::patient() const
{
    if (!m_patient && !isAnonymous()) {
        QVariant patient_id_var = value(PATIENT_FK_FIELDNAME);
        if (!patient_id_var.isNull()) {
            int patient_id = patient_id_var.toInt();
            m_patient = QSharedPointer<Patient>(
                    new Patient(m_app, m_db, patient_id));
        }
    }
    return m_patient.data();
}
