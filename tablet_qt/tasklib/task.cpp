#include "task.h"
#include <QObject>
#include <QVariant>
#include "common/camcopsapp.h"
#include "db/dbfunc.h"
#include "dbobjects/patient.h"
#include "lib/datetimefunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"

const QString Task::PATIENT_FK_FIELDNAME("patient_id");
const QString FIRSTEXIT_IS_FINISH_FIELDNAME("firstexit_is_finish");
const QString FIRSTEXIT_IS_ABORT_FIELDNAME("firstexit_is_abort");
const QString WHEN_FIRSTEXIT_FIELDNAME("when_firstexit");
const QString EDITING_TIME_S_FIELDNAME("editing_time_s");

const QString CLINICIAN_SPECIALTY("clinician_specialty");
const QString CLINICIAN_NAME("clinician_name");
const QString CLINICIAN_PROFESSIONAL_REGISTRATION("clinician_professional_registration");
const QString CLINICIAN_POST("clinician_post");
const QString CLINICIAN_SERVICE("clinician_service");
const QString CLINICIAN_CONTACT_DETAILS("clinician_contact_details");

const QString RESPONDENT_NAME("respondent_name");
const QString RESPONDENT_RELATIONSHIP("respondent_relationship");


Task::Task(CamcopsApp& app,
           const QSqlDatabase& db,
           const QString& tablename,
           bool is_anonymous,
           bool has_clinician,
           bool has_respondent) :
    DatabaseObject(app, db, tablename, DbConst::PK_FIELDNAME, true, true),
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
        addField(CLINICIAN_SPECIALTY, QVariant::String);
        addField(CLINICIAN_NAME, QVariant::String);
        addField(CLINICIAN_PROFESSIONAL_REGISTRATION, QVariant::String);
        addField(CLINICIAN_POST, QVariant::String);
        addField(CLINICIAN_SERVICE, QVariant::String);
        addField(CLINICIAN_CONTACT_DETAILS, QVariant::String);
    }
    if (has_respondent) {
        addField(RESPONDENT_NAME, QVariant::String);
        addField(RESPONDENT_RELATIONSHIP, QVariant::String);
    }
}


// ============================================================================
// General info
// ============================================================================

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
        return QString("%1; %2").arg(
            shortname(),
            whenCreated().toString(DateTime::SHORT_DATETIME_FORMAT));
    } else {
        Patient* pt = patient();
        return QString("%1; %2; %3").arg(
            shortname(),
            pt ? pt->surnameUpperForename() : tr("MISSING PATIENT"),
            whenCreated().toString(DateTime::SHORT_DATETIME_FORMAT));
    }
}


// ============================================================================
// Tables
// ============================================================================

QStringList Task::allTables() const
{
    QStringList all_tables(tablename());
    all_tables += ancillaryTables();
    return all_tables;
}


void Task::makeTables()
{
    makeTable();
    makeAncillaryTables();
}


int Task::count(const WhereConditions& where) const
{
    return DbFunc::count(m_db, m_tablename, where);
}


int Task::countForPatient(int patient_id) const
{
    if (isAnonymous()) {
        return 0;
    }
    WhereConditions where;
    where[PATIENT_FK_FIELDNAME] = patient_id;
    return count(where);
}


void Task::deleteFromDatabase()
{
    // Delete any ancillary objects (which should in turn look after themselves)
    // ***
    // Delete ourself
    DatabaseObject::deleteFromDatabase();
}


// ============================================================================
// Database object functions
// ============================================================================

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


// ============================================================================
// Specific info
// ============================================================================

QString Task::summary() const
{
    return tr("MISSING SUMMARY");
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


// ============================================================================
// Assistance functions
// ============================================================================

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


QString Task::xstring(const QString &stringname) const
{
    return m_app.xstring(xstringTaskname(), stringname);
}


QString Task::totalScorePhrase(int score, int max_score) const
{
    return QString("%1: <b>%2</b> / %3")
            .arg(tr("Total score")).arg(score).arg(max_score);
}


QStringList Task::fieldSummaries(const QString& xstringprefix,
                                 const QString& xstringsuffix,
                                 const QString& spacer,
                                 const QString& fieldprefix,
                                 int first,
                                 int last) const
{
    using StringFunc::strseq;
    QStringList xstringnames = strseq(xstringprefix, first, last,
                                      xstringsuffix);
    QStringList fieldnames = strseq(fieldprefix, first, last);
    QStringList list;
    for (int i = 0; i < fieldnames.length(); ++i) {
        QString fieldname = fieldnames.at(i);
        QString xstringname = xstringnames.at(i);
        list.append(QString("%1%2<b>%3</b>")
                    .arg(xstring(xstringname))
                    .arg(spacer)
                    .arg(prettyValue(fieldname)));
    }
    return list;
}


// ============================================================================
// Editing
// ============================================================================

double Task::editingTimeSeconds() const
{
    return valueDouble(EDITING_TIME_S_FIELDNAME);
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


// ============================================================================
// Patient functions (for non-anonymous tasks)
// ============================================================================

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
    m_patient.clear();
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
