#include "task.h"
#include <QObject>
#include <QVariant>
#include "common/camcopsapp.h"
#include "common/uiconstants.h"
#include "common/varconst.h"
#include "common/version.h"
#include "db/dbfunc.h"
#include "dbobjects/patient.h"
#include "lib/datetimefunc.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qupage.h"

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
    DatabaseObject(app, db, tablename, dbconst::PK_FIELDNAME, true, true),
    m_patient(nullptr),
    m_editing(false),
    m_is_anonymous(is_anonymous),
    m_has_clinician(has_clinician),
    m_has_respondent(has_respondent)
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
            whenCreated().toString(datetime::SHORT_DATETIME_FORMAT));
    } else {
        Patient* pt = patient();
        return QString("%1; %2; %3").arg(
            shortname(),
            pt ? pt->surnameUpperForename() : tr("MISSING PATIENT"),
            whenCreated().toString(datetime::SHORT_DATETIME_FORMAT));
    }
}


bool Task::isAnonymous() const
{
    return m_is_anonymous;
}


bool Task::hasClinician() const
{
    return m_has_clinician;
}


bool Task::hasRespondent() const
{
    return m_has_respondent;
}


bool Task::isTaskPermissible() const
{
    QVariant commercial = m_app.var(varconst::IP_USE_COMMERCIAL);
    QVariant clinical = m_app.var(varconst::IP_USE_CLINICAL);
    QVariant educational = m_app.var(varconst::IP_USE_EDUCATIONAL);
    QVariant research = m_app.var(varconst::IP_USE_RESEARCH);
    if (prohibitsCommercial() && !mathfunc::eq(commercial, false)) {
        return false;
    }
    if (prohibitsClinical() && !mathfunc::eq(clinical, false)) {
        return false;
    }
    if (prohibitsEducational() && !mathfunc::eq(educational, false)) {
        return false;
    }
    if (prohibitsResearch() && !mathfunc::eq(research, false)) {
        return false;
    }
    return true;
}


QString Task::whyNotPermissible() const
{
    const QString prohibits_commercial = tr("Task not allowed for commercial"
                                            " use (see Task Information).");
    const QString prohibits_clinical = tr("Task not allowed for research"
                                          " use (see Task Information).");
    const QString prohibits_educational = tr("Task not allowed for educational"
                                             " use (see Task Information).");
    const QString prohibits_research = tr("Task not allowed for research"
                                          " use (see Task Information).");
    const QString yes = tr(
                " You have said you ARE using this software in that context "
                "(see Settings). To use this task, you must seek permission "
                "from the copyright holder (see Task Information).");
    const QString unknown = tr(" You have NOT SAID whether you are using this "
                               "software in that context (see Settings).");
    QVariant commercial = m_app.var(varconst::IP_USE_COMMERCIAL);
    QVariant clinical = m_app.var(varconst::IP_USE_CLINICAL);
    QVariant educational = m_app.var(varconst::IP_USE_EDUCATIONAL);
    QVariant research = m_app.var(varconst::IP_USE_RESEARCH);

    auto not_definitely_false = [](const QVariant& v) -> bool {
        return !mathfunc::eq(v, false);
    };
    auto is_unknown = [](const QVariant& v) -> bool {
        return v.isNull() || v.toInt() == CommonOptions::UNKNOWN_INT;
    };


    if (prohibitsCommercial() && not_definitely_false(commercial)) {
        return prohibits_commercial + (is_unknown(commercial) ? unknown : yes);
    }
    if (prohibitsClinical() && not_definitely_false(clinical)) {
        return prohibits_clinical + (is_unknown(clinical) ? unknown : yes);
    }
    if (prohibitsEducational() && not_definitely_false(educational)) {
        return prohibits_educational + (is_unknown(educational) ? unknown : yes);
    }
    if (prohibitsResearch() && not_definitely_false(research)) {
        return prohibits_research + (is_unknown(research) ? unknown : yes);
    }
    return tr("Task permissible");
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
    return dbfunc::count(m_db, m_tablename, where);
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


void Task::upgradeDatabase(const Version& old_version,
                           const Version& new_version)
{
    Q_UNUSED(old_version);
    Q_UNUSED(new_version);
}

// ============================================================================
// Database object functions
// ============================================================================

bool Task::load(int pk)
{
    if (pk == dbconst::NONEXISTENT_PK) {
        return false;
    }
    return DatabaseObject::load(pk);
}


bool Task::save()
{
    // Sanity checks before we permit saving
    if (!isAnonymous() && value(PATIENT_FK_FIELDNAME).isNull()) {
        uifunc::stopApp("Task has no patient ID (and is not anonymous); "
                        "cannot save");
    }
    return DatabaseObject::save();
}


// ============================================================================
// Specific info
// ============================================================================

QStringList Task::summary() const
{
    return QStringList{tr("MISSING SUMMARY")};
}


QStringList Task::detail() const
{
    QStringList result = summaryWithCompletenessInfo();
    result.append("");  // blank line
    result += recordSummaryLines();
    return result;
}


OpenableWidget* Task::editor(bool read_only)
{
    Q_UNUSED(read_only);
    qWarning() << "Base class Task::edit called - not a good thing!";
    return nullptr;
}


// ============================================================================
// Assistance functions
// ============================================================================

QDateTime Task::whenCreated() const
{
    return value(dbconst::CREATION_TIMESTAMP_FIELDNAME)
        .toDateTime();
}


QStringList Task::summaryWithCompletenessInfo() const
{
    if (isComplete()) {
        return summary();
    } else {
        QStringList result{tr("<b>(INCOMPLETE)</b>")};
        result += summary();
        return result;
    }
}


QString Task::xstring(const QString &stringname) const
{
    return m_app.xstring(xstringTaskname(), stringname);
}


QStringList Task::fieldSummaries(const QString& xstringprefix,
                                 const QString& xstringsuffix,
                                 const QString& spacer,
                                 const QString& fieldprefix,
                                 int first,
                                 int last) const
{
    using stringfunc::strseq;
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


QStringList Task::fieldSummariesYesNo(const QString& xstringprefix,
                                      const QString& xstringsuffix,
                                      const QString& spacer,
                                      const QString& fieldprefix,
                                      int first,
                                      int last) const
{
    using stringfunc::strseq;
    using uifunc::yesNo;
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
                    .arg(yesNo(valueBool(fieldname))));
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


void Task::setDefaultClinicianVariablesAtFirstUse()
{
    if (!m_has_clinician) {
        return;
    }
    setValue(CLINICIAN_SPECIALTY, m_app.varString(varconst::DEFAULT_CLINICIAN_SPECIALTY));
    setValue(CLINICIAN_NAME, m_app.varString(varconst::DEFAULT_CLINICIAN_NAME));
    setValue(CLINICIAN_PROFESSIONAL_REGISTRATION, m_app.varString(varconst::DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION));
    setValue(CLINICIAN_POST, m_app.varString(varconst::DEFAULT_CLINICIAN_POST));
    setValue(CLINICIAN_SERVICE, m_app.varString(varconst::DEFAULT_CLINICIAN_SERVICE));
    setValue(CLINICIAN_CONTACT_DETAILS, m_app.varString(varconst::DEFAULT_CLINICIAN_CONTACT_DETAILS));
}


QuElement* Task::getClinicianQuestionnaireBlockRawPointer()
{
    return questionnairefunc::defaultGridRawPointer({
        {tr("Clinician’s specialty"),
         new QuLineEdit(fieldRef(CLINICIAN_SPECIALTY))},
        {tr("Clinician’s name"),
         new QuLineEdit(fieldRef(CLINICIAN_NAME))},
        {tr("Clinician’s professional registration"),
         new QuLineEdit(fieldRef(CLINICIAN_PROFESSIONAL_REGISTRATION))},
        {tr("Clinician’s post"),
         new QuLineEdit(fieldRef(CLINICIAN_POST))},
        {tr("Clinician’s service"),
         new QuLineEdit(fieldRef(CLINICIAN_SERVICE))},
        {tr("Clinician’s contact details"),
         new QuLineEdit(fieldRef(CLINICIAN_CONTACT_DETAILS))},
    }, uiconst::DEFAULT_COLSPAN_Q, uiconst::DEFAULT_COLSPAN_A);
}


QuElementPtr Task::getClinicianQuestionnaireBlockElementPtr()
{
    return QuElementPtr(getClinicianQuestionnaireBlockRawPointer());
}


QuPagePtr Task::getClinicianDetailsPage()
{
    return QuPagePtr(
        (new QuPage{getClinicianQuestionnaireBlockRawPointer()})
            ->setTitle(tr("Clinician’s details"))
            ->setType(QuPage::PageType::Clinician)
    );
}


bool Task::isRespondentComplete() const
{
    if (!m_has_respondent) {
        return false;
    }
    return !valueString(RESPONDENT_NAME).isEmpty() &&
            !valueString(RESPONDENT_RELATIONSHIP).isEmpty();
}


QuElement* Task::getRespondentQuestionnaireBlockRawPointer(bool second_person)
{
    const QString name = second_person
            ? tr("Your name")
            : tr("Respondent’s name");
    const QString relationship = second_person
            ? tr("Your relationship to the patient")
            : tr("Respondent’s relationship to patient");
    return questionnairefunc::defaultGridRawPointer({
        {name, new QuLineEdit(fieldRef(RESPONDENT_NAME))},
        {relationship, new QuLineEdit(fieldRef(RESPONDENT_RELATIONSHIP))},
    }, uiconst::DEFAULT_COLSPAN_Q, uiconst::DEFAULT_COLSPAN_A);
}


QuElementPtr Task::getRespondentQuestionnaireBlockElementPtr(bool second_person)
{
    return QuElementPtr(getRespondentQuestionnaireBlockRawPointer(second_person));
}


QuPagePtr Task::getRespondentDetailsPage(bool second_person)
{
    return QuPagePtr(
        (new QuPage{getRespondentQuestionnaireBlockRawPointer(second_person)})
            ->setTitle(tr("Respondent’s details"))
            ->setType(second_person ? QuPage::PageType::Patient
                                    : QuPage::PageType::Clinician)
    );
}


QuPagePtr Task::getClinicianAndRespondentDetailsPage(bool second_person)
{
    return QuPagePtr(
        (new QuPage{getClinicianQuestionnaireBlockRawPointer(),
                    getRespondentQuestionnaireBlockRawPointer(second_person)})
            ->setTitle(tr("Clinician’s and respondent’s details"))
            ->setType(second_person ? QuPage::PageType::ClinicianWithPatient
                                    : QuPage::PageType::Clinician)
    );
}


void Task::editStarted()
{
    m_editing = true;
    m_editing_started = datetime::now();
}


void Task::editFinished(bool aborted)
{
    if (!m_editing) {
        qDebug() << Q_FUNC_INFO << "wasn't editing";
        return;
    }
    m_editing = false;
    // Time
    QDateTime now = datetime::now();
    double editing_time_s = valueDouble(EDITING_TIME_S_FIELDNAME);
    editing_time_s += datetime::doubleSecondsFrom(m_editing_started, now);
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
        uifunc::stopApp("Attempt to set patient ID for an anonymous task");
    }
    if (!value(PATIENT_FK_FIELDNAME).isNull()) {
        uifunc::stopApp("Setting patient ID, but it was already set");
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


QString Task::getPatientName() const
{
    Patient* pt = patient();
    if (!pt) {
        return "";
    }
    return QString("%1 %2").arg(pt->forename()).arg(pt->surname());
}


bool Task::isFemale() const
{
    Patient* pt = patient();
    return pt ? pt->isFemale() : false;
}


bool Task::isMale() const
{
    Patient* pt = patient();
    return pt ? pt->isMale() : false;
}
