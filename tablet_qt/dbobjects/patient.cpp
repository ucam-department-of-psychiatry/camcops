/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
#include "common/dbconstants.h"
#include "common/design_defines.h"
#include "db/dbfunc.h"
#include "db/dbtransaction.h"
#include "lib/datetime.h"
#include "lib/idpolicy.h"
#include "lib/uifunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/questionnaire.h"
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
const QString IDNUM_FIELD_FORMAT("idnum%1");

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


Patient::Patient(CamcopsApp& app, DatabaseManager& db, int load_pk) :
    DatabaseObject(app, db, TABLENAME, dbconst::PK_FIELDNAME, true, false),
    m_questionnaire(nullptr)
{
    // ------------------------------------------------------------------------
    // Define fields
    // ------------------------------------------------------------------------
    addField(FORENAME_FIELD, QVariant::String);
    addField(SURNAME_FIELD, QVariant::String);
    addField(SEX_FIELD, QVariant::String);
    addField(DOB_FIELD, QVariant::String);
    addField(ADDRESS_FIELD, QVariant::String);
    addField(GP_FIELD, QVariant::String);
    addField(OTHER_FIELD, QVariant::String);
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        addField(IDNUM_FIELD_FORMAT.arg(n), QVariant::LongLong);
#ifdef DUPLICATE_ID_DESCRIPTIONS_INTO_PATIENT_TABLE
        // Information for these two comes from the server, and is ONLY stored
        // here at the moment of upload (copied from the CamcopsApp's info).
        addField(dbconst::IDSHORTDESC_FIELD_FORMAT.arg(n), QVariant::String);
        addField(dbconst::IDDESC_FIELD_FORMAT.arg(n), QVariant::String);
#endif
    }

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


int Patient::id() const
{
    return pkvalueInt();
}


QString Patient::forename() const
{
    QString forename = valueString(FORENAME_FIELD);
    return forename.isEmpty() ? "?" : forename;
}


QString Patient::surname() const
{
    QString surname = valueString(SURNAME_FIELD);
    return surname.isEmpty() ? "?" : surname;
}


QString Patient::surnameUpperForename() const
{
    return QString("%1, %2").arg(surname().toUpper()).arg(forename());
}


QString Patient::sex() const
{
    QString sex = valueString(SEX_FIELD);
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


QVariant Patient::idnumVariant(int which_idnum) const
{
    if (!dbconst::isValidWhichIdnum(which_idnum)) {
        return QVariant();
    }
    return value(IDNUM_FIELD_FORMAT.arg(which_idnum));
}


qlonglong Patient::idnumInteger(int which_idnum) const
{
    if (!dbconst::isValidWhichIdnum(which_idnum)) {
        return 0;
    }
    return valueULongLong(IDNUM_FIELD_FORMAT.arg(which_idnum));
}


OpenableWidget* Patient::editor(bool read_only)
{
    QuPagePtr page(new QuPage());
    page->setTitle(tr("Edit patient"));

    QuGridContainer* grid = new QuGridContainer();
    grid->setColumnStretch(0, 1);
    grid->setColumnStretch(1, 2);
    int row = 0;
    Qt::Alignment align = Qt::AlignRight | Qt::AlignTop;

    grid->addCell(QuGridCell(new QuText(tr("Surname")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(new QuLineEdit(fieldRef(SURNAME_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Forename")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(new QuLineEdit(fieldRef(FORENAME_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Sex")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(
        (new QuMcq(fieldRef(SEX_FIELD),  // properly mandatory
                   CommonOptions::sexes()))->setHorizontal(true),
        row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Date of birth")),
                             row, 0, 1, 1, align));
    grid->addCell(QuGridCell(
        (new QuDateTime(fieldRef(DOB_FIELD,
                                 false)))->setMode(QuDateTime::DefaultDate),
        row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Address")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(new QuTextEdit(fieldRef(ADDRESS_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("General practitioner (GP)")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(new QuTextEdit(fieldRef(GP_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Other details")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(new QuTextEdit(fieldRef(OTHER_FIELD, false)),
                             row++, 1));
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        QString iddesc = m_app.idDescription(n);
        QString idfield = IDNUM_FIELD_FORMAT.arg(n);
        grid->addCell(QuGridCell(new QuText(iddesc), row, 0, 1, 1, align));
        QuLineEditLongLong* num_editor = new QuLineEditLongLong(
                    fieldRef(idfield, false),
                    MIN_ID_NUM_VALUE,
                    MAX_ID_NUM_VALUE);
        grid->addCell(QuGridCell(num_editor, row++, 1));
    }
    page->addElement(grid);

    page->addElement(new QuHeading(tr("Minimum ID required for app:")));
    page->addElement(new QuText(TABLET_ID_POLICY.pretty()));
    page->addElement((new QuImage(uifunc::iconFilename(uiconst::CBS_OK),
                                  uiconst::ICONSIZE))
                     ->addTag(TAG_POLICY_APP_OK));
    page->addElement((new QuImage(uifunc::iconFilename(uiconst::ICON_STOP),
                                  uiconst::ICONSIZE))
                     ->addTag(TAG_POLICY_APP_FAIL));

    page->addElement(new QuHeading(tr("Minimum ID required for upload to server:")));
    page->addElement(new QuText(m_app.uploadPolicy().pretty()));
    page->addElement((new QuImage(uifunc::iconFilename(uiconst::CBS_OK),
                                  uiconst::ICONSIZE))
                     ->addTag(TAG_POLICY_UPLOAD_OK));
    page->addElement((new QuImage(uifunc::iconFilename(uiconst::ICON_STOP),
                                  uiconst::ICONSIZE))
                     ->addTag(TAG_POLICY_UPLOAD_FAIL));

    page->addElement(new QuHeading(tr("Minimum ID required to finalize on server:")));
    page->addElement(new QuText(m_app.finalizePolicy().pretty()));
    page->addElement((new QuImage(uifunc::iconFilename(uiconst::CBS_OK),
                                  uiconst::ICONSIZE))
                     ->addTag(TAG_POLICY_FINALIZE_OK));
    page->addElement((new QuImage(uifunc::iconFilename(uiconst::ICON_STOP),
                                  uiconst::ICONSIZE))
                     ->addTag(TAG_POLICY_FINALIZE_FAIL));

    page->addElement(new QuHeading(tr("ID numbers must not clash with another patient:")));
    page->addElement((new QuText("?"))->addTag(TAG_IDCLASH_DETAIL));
    page->addElement((new QuImage(uifunc::iconFilename(uiconst::CBS_OK),
                                  uiconst::ICONSIZE))
                     ->addTag(TAG_IDCLASH_OK));
    page->addElement((new QuImage(uifunc::iconFilename(uiconst::ICON_STOP),
                                  uiconst::ICONSIZE))
                     ->addTag(TAG_IDCLASH_FAIL));

    for (auto fieldname : policyAttributes().keys()) {
        FieldRefPtr fr = fieldRef(fieldname);
        connect(fr.data(), &FieldRef::valueChanged,
                this, &Patient::updateQuestionnaireIndicators);
    }

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setReadOnly(read_only);
    updateQuestionnaireIndicators();
    return m_questionnaire;
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
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        map[IDNUM_FIELD_FORMAT.arg(n)] = hasIdnum(n);
    }
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
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        if (hasIdnum(n)) {
            details.append(QString("%1 %2")
                           .arg(m_app.idShortDescription(n))
                           .arg(idnumInteger(n)));
        }
    }
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

    bool app = TABLET_ID_POLICY.complies(attributes);
    m_questionnaire->setVisibleByTag(TAG_POLICY_APP_OK, app);
    m_questionnaire->setVisibleByTag(TAG_POLICY_APP_FAIL, !app);
    fieldRef(SURNAME_FIELD)->setMandatory(!app);
    fieldRef(FORENAME_FIELD)->setMandatory(!app);
    fieldRef(SEX_FIELD)->setMandatory(!app);
    fieldRef(DOB_FIELD)->setMandatory(!app);
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        fieldRef(IDNUM_FIELD_FORMAT.arg(n))->setMandatory(!app);
    }

    bool upload = m_app.uploadPolicy().complies(attributes);
    m_questionnaire->setVisibleByTag(TAG_POLICY_UPLOAD_OK, upload);
    m_questionnaire->setVisibleByTag(TAG_POLICY_UPLOAD_FAIL, !upload);

    bool finalize = m_app.finalizePolicy().complies(attributes);
    m_questionnaire->setVisibleByTag(TAG_POLICY_FINALIZE_OK, finalize);
    m_questionnaire->setVisibleByTag(TAG_POLICY_FINALIZE_FAIL, !finalize);

    bool id_ok = true;
    QStringList clashing_ids;
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        if (othersClashOnIdnum(n)) {
            clashing_ids.append(m_app.idShortDescription(n));
            id_ok = false;
        }
    }
    QString idclash_text = id_ok
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


bool Patient::othersClashOnIdnum(int which_idnum) const
{
    using dbfunc::delimit;
    if (which_idnum < 1 || which_idnum > dbconst::NUMBER_OF_IDNUMS) {
        uifunc::stopApp("Bug: Bad which_idnum to Patient::othersClashOnIdnum");
    }
    QString id_fieldname = IDNUM_FIELD_FORMAT.arg(which_idnum);
    QVariant idvar = idnumVariant(which_idnum);
    if (idvar.isNull()) {
        return false;
    }
    qlonglong idnum = idnumInteger(which_idnum);
    int patient_pk = id();
    SqlArgs sqlargs(
        QString("SELECT COUNT(*) FROM %1 WHERE %2 = ? AND %3 <> ?")
            .arg(delimit(TABLENAME),
                 delimit(id_fieldname),
                 delimit(dbconst::PK_FIELDNAME)),
        ArgList{idnum, patient_pk}
    );
    int c = m_db.fetchInt(sqlargs);
    return c > 0;
}


bool Patient::anyIdClash() const
{
    // Single SQL statement
    using dbfunc::delimit;
    ArgList args;
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
    args.append(id());
    QString sql = QString("SELECT COUNT(*) FROM %1 WHERE (%2) AND %3 <> ?")
            .arg(delimit(TABLENAME),
                 idnum_criteria.join(" OR "),
                 delimit(dbconst::PK_FIELDNAME));
    SqlArgs sqlargs(sql, args);
    int c = m_db.fetchInt(sqlargs);
    return c > 0;
}


int Patient::numTasks() const
{
    int n = 0;
    int patient_id = id();
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
    int patient_id = id();
    if (patient_id == dbconst::NONEXISTENT_PK) {
        return;
    }
    DbTransaction trans(m_db);
    TaskFactory* factory = m_app.taskFactory();
    for (auto p_task : factory->fetchAllForPatient(patient_id)) {
        p_task->deleteFromDatabase();
    }
    // Delete ourself
    DatabaseObject::deleteFromDatabase();
}
