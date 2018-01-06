/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "patient.h"
#include <limits>
#include <QDebug>
#include "core/camcopsapp.h"
#include "common/dbconst.h"
#include "common/design_defines.h"
#include "db/ancillaryfunc.h"
#include "db/dbfunc.h"
#include "db/dbnestabletransaction.h"
#include "dbobjects/patientidnum.h"
#include "dbobjects/patientidnumsorter.h"
#include "dialogs/nvpchoicedialog.h"
#include "lib/containers.h"
#include "lib/datetime.h"
#include "lib/idpolicy.h"
#include "lib/uifunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quimage.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditlonglong.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"
#include "widgets/openablewidget.h"

const QString Patient::TABLENAME("patient");

// Important that these match ID policy names:
const QString FORENAME_FIELD("forename");
const QString SURNAME_FIELD("surname");
const QString DOB_FIELD("dob");
const QString SEX_FIELD("sex");
const QString IDNUM_FIELD_PREFIX("idnum");
const QString IDNUM_FIELD_FORMAT(IDNUM_FIELD_PREFIX + "%1");
const QString ANY_IDNUM("anyidnum");

// Not so important:
const QString ADDRESS_FIELD("address");
const QString GP_FIELD("gp");
const QString OTHER_FIELD("other");

const qint64 MIN_ID_NUM_VALUE = 0;
const qint64 MAX_ID_NUM_VALUE = std::numeric_limits<qint64>::max();

const QString TAG_POLICY_APP_OK("app_ok");
const QString TAG_POLICY_APP_FAIL("app_fail");
const QString TAG_POLICY_UPLOAD_OK("upload_ok");
const QString TAG_POLICY_UPLOAD_FAIL("upload_fail");
const QString TAG_POLICY_FINALIZE_OK("finalize_ok");
const QString TAG_POLICY_FINALIZE_FAIL("finalize_fail");
const QString TAG_IDCLASH_OK("idclash_ok");
const QString TAG_IDCLASH_FAIL("idclash_fail");
const QString TAG_IDCLASH_DETAIL("idclash_detail");

const QString DELETE_ID_NUM(QObject::tr("Delete ID#"));


// ============================================================================
// Creation
// ============================================================================

Patient::Patient(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    DatabaseObject(app, db, TABLENAME, dbconst::PK_FIELDNAME, true, false),
    m_page(nullptr),
    m_questionnaire(nullptr)
{
    // ------------------------------------------------------------------------
    // Define fields
    // ------------------------------------------------------------------------
    addField(FORENAME_FIELD, QVariant::String);
    addField(SURNAME_FIELD, QVariant::String);
    addField(SEX_FIELD, QVariant::String);
    addField(DOB_FIELD, QVariant::Date);
    addField(ADDRESS_FIELD, QVariant::String);
    addField(GP_FIELD, QVariant::String);
    addField(OTHER_FIELD, QVariant::String);
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        addField(IDNUM_FIELD_FORMAT.arg(n), QVariant::LongLong);
#ifdef DUPLICATE_ID_DESCRIPTIONS_INTO_PATIENT_TABLE
        // Information for these two comes from the server, and is ONLY stored
        // here at the moment of upload (copied from the CamcopsApp's info).
        addField(dbconst::IDSHORTDESC_FIELD_FORMAT.arg(n), QVariant::String);
        addField(dbconst::IDDESC_FIELD_FORMAT.arg(n), QVariant::String);
#endif
    }
#endif

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Ancillary management
// ============================================================================

void Patient::loadAllAncillary(const int pk)
{
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    Q_UNUSED(pk);
#else
    const OrderBy order_by{{PatientIdNum::FN_WHICH_IDNUM, true}};
    ancillaryfunc::loadAncillary<PatientIdNum, PatientIdNumPtr>(
                m_idnums, m_app, m_db,
                PatientIdNum::FK_PATIENT, order_by, pk);
#endif
}


QVector<DatabaseObjectPtr> Patient::getAncillarySpecimens() const
{
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    return QVector<DatabaseObjectPtr>();
#else
    return QVector<DatabaseObjectPtr>{
        PatientIdNumPtr(new PatientIdNum(m_app, m_db)),
    };
#endif
}


QVector<DatabaseObjectPtr> Patient::getAllAncillary() const
{
    QVector<DatabaseObjectPtr> ancillaries;
#ifndef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (auto idnum : m_idnums) {
        ancillaries.append(idnum);
    }
#endif
    return ancillaries;
}


// ============================================================================
// Information about patients
// ============================================================================

int Patient::id() const
{
    return pkvalueInt();
}


QString Patient::forename() const
{
    const QString forename = valueString(FORENAME_FIELD);
    return forename.isEmpty() ? "?" : forename;
}


QString Patient::surname() const
{
    const QString surname = valueString(SURNAME_FIELD);
    return surname.isEmpty() ? "?" : surname;
}


QString Patient::sex() const
{
    const QString sex = valueString(SEX_FIELD);
    return sex.isEmpty() ? "?" : sex;
}


bool Patient::isFemale() const
{
    return sex() == CommonOptions::SEX_FEMALE;
}


bool Patient::isMale() const
{
    return sex() == CommonOptions::SEX_MALE;
}


QDate Patient::dob() const
{
    return valueDate(DOB_FIELD);
}


QString Patient::dobText() const
{
    return datetime::textDate(value(DOB_FIELD));
}


int Patient::ageYears() const
{
    return datetime::ageYears(value(DOB_FIELD));
}


bool Patient::hasIdnum(int which_idnum) const
{
    return !idnumVariant(which_idnum).isNull();
}


QVector<int> Patient::whichIdnumsPresent() const
{
    QVector<int> which;
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        if (hasIdnum(n)) {
            which.append(n);
        }
    }
#else
    for (PatientIdNumPtr idnum : m_idnums) {
        if (idnum->idnumIsPresent()) {
            which.append(idnum->whichIdNum());
        }
    }
#endif
    return which;
}


QVector<int> Patient::whichIdnumsHaveEntries() const
{
    QVector<int> which;
#ifndef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (PatientIdNumPtr idnum : m_idnums) {
        which.append(idnum->whichIdNum());
    }
#endif
    return which;
}


QVariant Patient::idnumVariant(const int which_idnum) const
{
    if (!dbconst::isValidWhichIdnum(which_idnum)) {
        return QVariant();
    }
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    return value(IDNUM_FIELD_FORMAT.arg(which_idnum));
#else
    for (PatientIdNumPtr idnum : m_idnums) {
        if (idnum->whichIdNum() == which_idnum) {
            return idnum->idnumAsVariant();
        }
    }
    return QVariant();
#endif
}


qlonglong Patient::idnumInteger(const int which_idnum) const
{
    return idnumVariant(which_idnum).toULongLong();  // 0 in case of failure
}


bool Patient::hasForename() const
{
    return !valueString(FORENAME_FIELD).isEmpty();
}


bool Patient::hasSurname() const
{
    return !valueString(SURNAME_FIELD).isEmpty();
}


bool Patient::hasDob() const
{
    return !value(DOB_FIELD).isNull();
}


bool Patient::hasSex() const
{
    return !valueString(SEX_FIELD).isEmpty();
}


Patient::AttributesType Patient::policyAttributes() const
{
    AttributesType map;
    map[FORENAME_FIELD] = hasForename();
    map[SURNAME_FIELD] = hasSurname();
    map[DOB_FIELD] = hasDob();
    map[SEX_FIELD] = hasSex();
    bool any_idnum = false;
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        const bool present = hasIdnum(n);
        map[IDNUM_FIELD_FORMAT.arg(n)] = present;
        any_idnum = any_idnum || present;
    }
#else
    for (PatientIdNumPtr idnum : m_idnums) {
        const bool present = idnum->idnumIsPresent();
        map[IDNUM_FIELD_FORMAT.arg(idnum->whichIdNum())] = present;
        any_idnum = any_idnum || present;
    }
#endif
    map[ANY_IDNUM] = any_idnum;
    return map;
}


bool Patient::compliesWith(const IdPolicy& policy) const
{
    return policy.complies(policyAttributes());
}


bool Patient::compliesWithUpload() const
{
    return compliesWith(m_app.uploadPolicy());
}


bool Patient::compliesWithFinalize() const
{
    return compliesWith(m_app.finalizePolicy());
}


QString Patient::shortIdnumSummary() const
{
    QStringList details;
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        if (hasIdnum(n)) {
            details.append(QString("%1 %2")
                           .arg(m_app.idShortDescription(n))
                           .arg(idnumInteger(n)));
        }
    }
#else
    for (PatientIdNumPtr idnum : m_idnums) {
        details.append(QString("%1 %2")
                       .arg(m_app.idShortDescription(idnum->whichIdNum()))
                       .arg(idnum->idnumAsString()));
    }
#endif
    if (details.isEmpty()) {
        return tr("[No ID numbers]");
    }
    return details.join(", ");
}


void Patient::updateQuestionnaireIndicators(const FieldRef* fieldref,
                                            const QObject* originator)
{
    qDebug() << Q_FUNC_INFO;
    Q_UNUSED(fieldref);
    Q_UNUSED(originator);
    if (!m_questionnaire) {
        return;
    }
    AttributesType attributes = policyAttributes();

    const bool tablet_ok = TABLET_ID_POLICY.complies(attributes);
    m_questionnaire->setVisibleByTag(TAG_POLICY_APP_OK, tablet_ok);
    m_questionnaire->setVisibleByTag(TAG_POLICY_APP_FAIL, !tablet_ok);
    fieldRef(SURNAME_FIELD)->setMandatory(!tablet_ok);
    fieldRef(FORENAME_FIELD)->setMandatory(!tablet_ok);
    fieldRef(SEX_FIELD)->setMandatory(!tablet_ok);
    fieldRef(DOB_FIELD)->setMandatory(!tablet_ok);
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        fieldRef(IDNUM_FIELD_FORMAT.arg(n))->setMandatory(!tablet_ok);
    }
#else
    for (PatientIdNumPtr idnum : m_idnums) {
        idnum->fieldRef(PatientIdNum::FN_IDNUM_VALUE)->setMandatory(!tablet_ok);
    }
#endif

    const bool upload_ok = m_app.uploadPolicy().complies(attributes);
    m_questionnaire->setVisibleByTag(TAG_POLICY_UPLOAD_OK, upload_ok);
    m_questionnaire->setVisibleByTag(TAG_POLICY_UPLOAD_FAIL, !upload_ok);

    const bool finalize_ok = m_app.finalizePolicy().complies(attributes);
    m_questionnaire->setVisibleByTag(TAG_POLICY_FINALIZE_OK, finalize_ok);
    m_questionnaire->setVisibleByTag(TAG_POLICY_FINALIZE_FAIL, !finalize_ok);

    bool id_ok = true;
    QStringList clashing_ids;
    const QVector<int> which_idnums_present = whichIdnumsPresent();
    for (const int n : which_idnums_present) {
        if (othersClashOnIdnum(n)) {
            clashing_ids.append(m_app.idShortDescription(n));
            id_ok = false;
        }
    }
    const QString idclash_text = id_ok
            ? "No clashes"
            : ("The following IDs clash: " + clashing_ids.join(", "));
    m_questionnaire->setVisibleByTag(TAG_IDCLASH_OK, id_ok);
    m_questionnaire->setVisibleByTag(TAG_IDCLASH_FAIL, !id_ok);
    QuElement* element = m_questionnaire->getFirstElementByTag(
                TAG_IDCLASH_DETAIL, false);
    QuText* textelement = dynamic_cast<QuText*>(element);
    if (textelement) {
        textelement->setText(idclash_text);
    }
}


bool Patient::othersClashOnIdnum(const int which_idnum) const
{
    // Answers the question: do any other patients share the ID number whose
    // *index* (e.g. 1-8) is which_idnum?
    using dbfunc::delimit;
    if (!dbconst::isValidWhichIdnum(which_idnum)) {
        uifunc::stopApp("Bug: Bad which_idnum to Patient::othersClashOnIdnum");
    }
    const QVariant idvar = idnumVariant(which_idnum);
    if (idvar.isNull()) {
        return false;
    }
    const qlonglong idnum = idnumInteger(which_idnum);
    const int patient_pk = id();
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    const QString id_fieldname = IDNUM_FIELD_FORMAT.arg(which_idnum);
    const SqlArgs sqlargs(
        QString("SELECT COUNT(*) FROM %1 WHERE %2 = ? AND %3 <> ?")
            .arg(delimit(TABLENAME),
                 delimit(id_fieldname),
                 delimit(dbconst::PK_FIELDNAME)),
        ArgList{idnum, patient_pk}
    );
#else
    const SqlArgs sqlargs(
        QString("SELECT COUNT(*) FROM %1 WHERE %2 = ? AND %3 = ? AND %4 <> ?")
            .arg(delimit(PatientIdNum::PATIENT_IDNUM_TABLENAME),
                 delimit(PatientIdNum::FN_WHICH_IDNUM),
                 delimit(PatientIdNum::FN_IDNUM_VALUE),
                 delimit(PatientIdNum::FK_PATIENT)),
        ArgList{which_idnum, idnum, patient_pk}
    );
#endif
    const int c = m_db.fetchInt(sqlargs);
    return c > 0;
}


bool Patient::anyIdClash() const
{
    // With a single SQL statement, answers the question: "Are there any other
    // patients (that is, patients with a different PK) that share any ID
    // numbers with this patient)?"
    using dbfunc::delimit;
    ArgList args;
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    QStringList idnum_criteria;
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        QVariant idvar = idnumVariant(n);
        if (idvar.isNull()) {
            continue;
        }
        QString id_fieldname = IDNUM_FIELD_FORMAT.arg(n);
        idnum_criteria.append(delimit(id_fieldname) + "=?");
        args.append(idvar);
    }
    if (idnum_criteria.isEmpty()) {  // no IDs that are not NULL
        return false;
    }
    const QString sql = QString("SELECT COUNT(*) FROM %1 WHERE (%2) AND %3 <> ?")
            .arg(delimit(TABLENAME),
                 idnum_criteria.join(" OR "),
                 delimit(dbconst::PK_FIELDNAME));
#else
    const QString sql = QString(
                "SELECT COUNT(*) "
                "FROM %1 otherpt "
                "INNER JOIN %1 thispt "
                "  ON otherpt.%2 = thispt.%2 "  // which_idnum
                "  AND otherpt.%3 = thispt.%3 "  // idnum value; will automatically ignore NULLs
                "  AND otherpt.%4 <> thispt.%4 "  // patient PK
                "WHERE thispt.%4 = ?")  // patient PK
            .arg(delimit(PatientIdNum::PATIENT_IDNUM_TABLENAME),  // %1
                 delimit(PatientIdNum::FN_WHICH_IDNUM),  // %2
                 delimit(PatientIdNum::FN_IDNUM_VALUE),  // %3
                 delimit(PatientIdNum::FK_PATIENT));  // %4
#endif
    args.append(id());
    const SqlArgs sqlargs(sql, args);
    const int c = m_db.fetchInt(sqlargs);
    return c > 0;
}


int Patient::numTasks() const
{
    int n = 0;
    const int patient_id = id();
    if (patient_id == dbconst::NONEXISTENT_PK) {
        return 0;
    }
    TaskFactory* factory = m_app.taskFactory();
    for (auto p_specimen : factory->allSpecimensExceptAnonymous()) {
        n += p_specimen->countForPatient(patient_id);  // copes with anonymous
    }
    return n;
}


void Patient::deleteFromDatabase()
{
    // Delete any associated tasks
    const int patient_id = id();
    if (patient_id == dbconst::NONEXISTENT_PK) {
        return;
    }
    DbNestableTransaction trans(m_db);
    TaskFactory* factory = m_app.taskFactory();
    for (auto p_task : factory->fetchAllForPatient(patient_id)) {
        p_task->deleteFromDatabase();
    }
    // Delete ourself
    DatabaseObject::deleteFromDatabase();
}


bool Patient::matchesForMerge(const Patient* other) const
{
    Q_ASSERT(other);
    auto sameOrOneNull = [this, &other](const QString& fieldname) -> bool {
        QVariant a = value(fieldname);
        QVariant b = other->value(fieldname);
        return a.isNull() || b.isNull() || a == b;
    };
    auto sameOrOneBlank = [this, &other](const QString& fieldname) -> bool {
        QString a = valueString(fieldname);
        QString b = other->valueString(fieldname);
        return a.isEmpty() || b.isEmpty() || a == b;
    };

    if (id() == other->id()) {
        qWarning() << Q_FUNC_INFO << "Asked to compare two patients with the "
                                     "same PK for merge! Bug.";
        return false;
    }
    // All ID numbers must match or be blank:
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        QString id_fieldname = IDNUM_FIELD_FORMAT.arg(n);
        if (!sameOrOneNull(id_fieldname)) {
            return false;
        }
    }
#else
    for (PatientIdNumPtr this_id : m_idnums) {
        const int which_idnum = this_id->whichIdNum();
        if (this_id->idnumIsPresent() &&
                other->hasIdnum(which_idnum) &&
                other->idnumInteger(which_idnum) != idnumInteger(which_idnum)) {
            return false;
        }
    }
#endif
    // Forename, surname, DOB, sex must match or be blank:
    return sameOrOneBlank(FORENAME_FIELD) &&
            sameOrOneBlank(SURNAME_FIELD) &&
            sameOrOneNull(DOB_FIELD) &&
            sameOrOneBlank(SEX_FIELD) &&
            sameOrOneBlank(ADDRESS_FIELD) &&
            sameOrOneBlank(GP_FIELD) &&
            sameOrOneBlank(OTHER_FIELD);
}


QString Patient::descriptionForMerge() const
{
    return QString("<b>%1</b><br>%2<br>%3").arg(surnameUpperForename(),
                                                ageSexDob(),
                                                shortIdnumSummary());
}


QString Patient::forenameSurname() const
{
    return QString("%1 %2").arg(forename(), surname());
}


QString Patient::surnameUpperForename() const
{
    return QString("%1, %2").arg(surname().toUpper(), forename());
}


QString Patient::sexAgeDob() const
{
    return QString("%1, %2y, DOB %3").arg(sex(),
                                          QString::number(ageYears()),
                                          dobText());
}


QString Patient::ageSexDob() const
{
    // "A 37-year-old woman..."
    return QString("%1, %2y, DOB %3").arg(sex(),
                                          QString::number(ageYears()),
                                          dobText());
}


QString Patient::twoLineDetailString() const
{
    return QString("%1 (%2)\n%3").arg(surnameUpperForename(),
                                      ageSexDob(),
                                      shortIdnumSummary());
}


QString Patient::oneLineHtmlDetailString() const
{
    return QString("<b>%1</b> (%2); %3").arg(surnameUpperForename(),
                                             ageSexDob(),
                                             shortIdnumSummary());
}


// ============================================================================
// Editing and other manipulations
// ============================================================================

OpenableWidget* Patient::editor(const bool read_only)
{
    buildPage();
    m_questionnaire = new Questionnaire(m_app, {m_page});
    m_questionnaire->setReadOnly(read_only);
    updateQuestionnaireIndicators();
    return m_questionnaire;
}


void Patient::buildPage()
{
    auto addIcon = [this](const QString& name, const QString& tag) {
        QuImage* image = new QuImage(uifunc::iconFilename(name),
                                     uiconst::ICONSIZE);
        image->setAdjustForDpi(false);  // uiconst::ICONSIZE already corrects for this
        image->addTag(tag);
        m_page->addElement(image);
    };

    if (!m_page) {
        m_page = QuPagePtr(new QuPage());
    } else {
        m_page->clearElements();
    }
    m_page->setTitle(tr("Edit patient"));

    QuGridContainer* grid = new QuGridContainer();
    grid->setColumnStretch(0, 1);
    grid->setColumnStretch(1, 2);
    int row = 0;
    const Qt::Alignment ralign = Qt::AlignRight | Qt::AlignTop;
    const Qt::Alignment lalign = Qt::AlignLeft | Qt::AlignTop;
    // Don't apply alignment to the editing widgets; let them fill their cells.
    const int rowspan = 1;
    const int colspan = 1;

    grid->addCell(QuGridCell(new QuText(tr("Surname")),
                             row, 0, rowspan, colspan, ralign));
    grid->addCell(QuGridCell(new QuLineEdit(fieldRef(SURNAME_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Forename")),
                             row, 0, rowspan, colspan, ralign));
    grid->addCell(QuGridCell(new QuLineEdit(fieldRef(FORENAME_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Sex")),
                             row, 0, rowspan, colspan, ralign));
    grid->addCell(QuGridCell(
        (new QuMcq(fieldRef(SEX_FIELD),  // properly mandatory
                   CommonOptions::sexes()))->setHorizontal(true),
        row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Date of birth")),
                             row, 0, rowspan, colspan, ralign));
    grid->addCell(QuGridCell(
        (new QuDateTime(fieldRef(DOB_FIELD,
                                 false)))->setMode(QuDateTime::DefaultDate),
        row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Address")),
                             row, 0, rowspan, colspan, ralign));
    grid->addCell(QuGridCell(new QuTextEdit(fieldRef(ADDRESS_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("General practitioner (GP)")),
                             row, 0, rowspan, colspan, ralign));
    grid->addCell(QuGridCell(new QuTextEdit(fieldRef(GP_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Other details")),
                             row, 0, rowspan, colspan, ralign));
    grid->addCell(QuGridCell(new QuTextEdit(fieldRef(OTHER_FIELD, false)),
                             row++, 1));
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        QString iddesc = m_app.idDescription(n);
        QString idfield = IDNUM_FIELD_FORMAT.arg(n);
        grid->addCell(QuGridCell(new QuText(iddesc),
                                 row, 0, rowspan, colspan, ralign));
        QuLineEditLongLong* num_editor = new QuLineEditLongLong(
                    fieldRef(idfield, false),
                    MIN_ID_NUM_VALUE,
                    MAX_ID_NUM_VALUE);
        grid->addCell(QuGridCell(num_editor, row++, 1));
    }
    m_page->addElement(grid);
#else
    m_page->addElement(grid);
    QuGridContainer* idgrid = new QuGridContainer();
    idgrid->setColumnStretch(0, 1);
    idgrid->setColumnStretch(1, 1);
    idgrid->setColumnStretch(2, 4);
    row = 0;
    for (PatientIdNumPtr idnum : m_idnums) {
        const int which_idnum = idnum->whichIdNum();
        QuButton* delete_id = new QuButton(
                DELETE_ID_NUM + " " + QString::number(which_idnum),
                std::bind(&Patient::deleteIdNum, this, which_idnum));
        idgrid->addCell(QuGridCell(delete_id,
                                   row, 0, rowspan, colspan, lalign));
        QuText* id_label = new QuText(m_app.idDescription(which_idnum));
        idgrid->addCell(QuGridCell(id_label,
                                   row, 1, rowspan, colspan, ralign));
        QuLineEditLongLong* num_editor = new QuLineEditLongLong(
                    idnum->fieldRef(PatientIdNum::FN_IDNUM_VALUE, false),
                    MIN_ID_NUM_VALUE,
                    MAX_ID_NUM_VALUE);
        idgrid->addCell(QuGridCell(num_editor, row++, 2));
    }
    QuButton* add_id = new QuButton(
                tr("Add ID number"),
                std::bind(&Patient::addIdNum, this));
    idgrid->addCell(QuGridCell(add_id,
                               row++, 0, rowspan, colspan, lalign));
    m_page->addElement(idgrid);
#endif

    m_page->addElement(new QuHeading(tr("Minimum ID required for app:")));
    m_page->addElement(new QuText(TABLET_ID_POLICY.pretty()));
    addIcon(uiconst::CBS_OK, TAG_POLICY_APP_OK);
    addIcon(uiconst::ICON_STOP, TAG_POLICY_APP_FAIL);

    m_page->addElement(new QuHeading(tr("Minimum ID required for upload to server:")));
    m_page->addElement(new QuText(m_app.uploadPolicy().pretty()));
    addIcon(uiconst::CBS_OK, TAG_POLICY_UPLOAD_OK);
    addIcon(uiconst::ICON_STOP, TAG_POLICY_UPLOAD_FAIL);

    m_page->addElement(new QuHeading(tr("Minimum ID required to finalize on server:")));
    m_page->addElement(new QuText(m_app.finalizePolicy().pretty()));
    addIcon(uiconst::CBS_OK, TAG_POLICY_FINALIZE_OK);
    addIcon(uiconst::ICON_STOP, TAG_POLICY_FINALIZE_FAIL);

    m_page->addElement(new QuHeading(tr("ID numbers must not clash with another patient:")));
    m_page->addElement((new QuText("?"))->addTag(TAG_IDCLASH_DETAIL));
    addIcon(uiconst::CBS_OK, TAG_IDCLASH_OK);
    addIcon(uiconst::ICON_STOP, TAG_IDCLASH_FAIL);

    QStringList fields{FORENAME_FIELD, SURNAME_FIELD, DOB_FIELD, SEX_FIELD};
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        fields.append(IDNUM_FIELD_FORMAT.arg(n));
    }
#endif
    for (const QString& fieldname : fields) {
        FieldRefPtr fr = fieldRef(fieldname);
        connect(fr.data(), &FieldRef::valueChanged,
                this, &Patient::updateQuestionnaireIndicators);
    }
#ifndef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (PatientIdNumPtr idnum : m_idnums) {
        FieldRefPtr fr = idnum->fieldRef(PatientIdNum::FN_IDNUM_VALUE);
        connect(fr.data(), &FieldRef::valueChanged,
                this, &Patient::updateQuestionnaireIndicators);
    }
#endif
}


void Patient::mergeInDetailsAndTakeTasksFrom(const Patient* other)
{
    DbNestableTransaction trans(m_db);

    const int this_pk = id();
    const int other_pk = other->id();

    // Copy information from other to this
    qInfo() << Q_FUNC_INFO << "Copying information from patient" << other_pk
            << "to patient" << this_pk;
    QStringList fields{
        FORENAME_FIELD,
        SURNAME_FIELD,
        DOB_FIELD,
        SEX_FIELD,
        ADDRESS_FIELD,
        GP_FIELD,
        OTHER_FIELD,
    };
#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        fields.append(IDNUM_FIELD_FORMAT.arg(n));
    }
#else
    bool please_sort = false;
    for (PatientIdNumPtr other_id : other->m_idnums) {
        if (other_id->idnumIsPresent()) {
            const int which_idnum = other_id->whichIdNum();
            const qlonglong other_idnum_value = other_id->idnumAsInteger();
            bool found = false;
            for (PatientIdNumPtr this_id : m_idnums) {
                if (this_id->whichIdNum() == which_idnum) {
                    found = true;
                    if (this_id->idnumIsPresent() &&
                            this_id->idnumAsInteger() != other_idnum_value) {
                        qWarning().nospace()
                                << Q_FUNC_INFO
                                << " Something has gone wrong! ID number mismatch for ID#"
                                << which_idnum
                                << " (this: " << this_id->idnumAsVariant()
                                << ", other: " << other_id->idnumAsVariant()
                                << ") yet we shouldn't be copying if there is mismatch!";
                    }
                    this_id->setIdnumValue(other_id->idnumAsInteger(), true);  // save
                }
            }
            if (!found) {
                PatientIdNumPtr new_id(new PatientIdNum(this_pk, which_idnum,
                                                        m_app, m_db));
                m_idnums.append(new_id);
                please_sort = true;
            }
        }
    }
    if (please_sort) {
        sortIdNums();
    }
#endif
    for (const QString& fieldname : fields) {
        QVariant this_value = value(fieldname);
        QVariant other_value = other->value(fieldname);
        if (this_value.isNull() || (this_value.toString().isEmpty() &&
                                    !other_value.toString().isEmpty())) {
            setValue(fieldname, other_value);
        }
    }
    save();

    // Move tasks from other to this
    qInfo() << Q_FUNC_INFO << "Moving tasks from patient" << other_pk
            << "to patient" << this_pk;
    TaskFactory* factory = m_app.taskFactory();
    for (TaskPtr p_task : factory->fetchAllForPatient(other_pk)) {
        p_task->moveToPatient(this_pk);
        p_task->save();
    }

    qInfo() << Q_FUNC_INFO << "Move complete";
}


void Patient::addIdNum()
{
    const QVector<int> present = whichIdnumsHaveEntries();
    const QVector<int> possible = m_app.whichIdNumsAvailable();
    const QVector<int> unused = containers::setSubtract(possible, present);
    if (unused.isEmpty()) {
        QString msg = tr("All ID numbers offered by the server are already here!");
        if (present.isEmpty()) {
            msg += tr(" (There are no ID numbers at all – have you "
                      "registered with a server?)");
        }
        uifunc::alert(msg);
        return;
    }
    NameValueOptions options;
    for (const int which_idnum : unused) {
        const NameValuePair pair(m_app.idDescription(which_idnum), which_idnum);
        options.append(pair);
    }
    NvpChoiceDialog dlg(m_questionnaire, options, tr("Add ID number"));
    QVariant chosen_idnum_var;
    if (dlg.choose(&chosen_idnum_var) != QDialog::Accepted) {
        return;  // user pressed cancel, or some such
    }
    const int chosen_idnum = chosen_idnum_var.toInt();
    PatientIdNumPtr new_id = PatientIdNumPtr(new PatientIdNum(
                            id(), chosen_idnum, m_app, m_db));  // will save
    m_idnums.append(new_id);
    sortIdNums();
}


void Patient::deleteIdNum(const int which_idnum)
{
    const QString strnum = QString::number(which_idnum);
    const QString text(tr("Really delete ID number") + " " + strnum + " (" +
                       m_app.idDescription(which_idnum) + ")?");
    const QString title(DELETE_ID_NUM + strnum + "?");
    if (!uifunc::confirm(text, title,
                         tr("Yes, delete it"), tr("No, cancel"),
                         m_questionnaire)) {
        return;
    }
    for (int i = 0; i < m_idnums.size(); ++i) {
        PatientIdNumPtr idnum = m_idnums.at(i);
        if (idnum->whichIdNum() == which_idnum) {
            idnum->deleteFromDatabase();
            m_idnums.remove(i);
            sortIdNums();
            return;
        }
    }
}


void Patient::sortIdNums()
{
    qSort(m_idnums.begin(), m_idnums.end(), PatientIdNumSorter());
    if (m_questionnaire) {
        buildPage();
        updateQuestionnaireIndicators();
        m_questionnaire->refreshCurrentPage();
    }
}
