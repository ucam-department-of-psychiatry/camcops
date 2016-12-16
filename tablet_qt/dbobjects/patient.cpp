/*
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
#include "common/camcopsapp.h"
#include "common/dbconstants.h"
#include "lib/datetimefunc.h"
#include "lib/idpolicy.h"
#include "lib/uifunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/qucontainergrid.h"
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


Patient::Patient(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    DatabaseObject(db, TABLENAME, DbConst::PK_FIELDNAME, true, false),
    m_app(app),
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
    for (int n = 1; n <= DbConst::NUMBER_OF_IDNUMS; ++n) {
        addField(IDNUM_FIELD_FORMAT.arg(n), QVariant::LongLong);
        // Information for these two comes from the server, and is ONLY stored
        // here at the moment of upload (copied from the CamcopsApp's info).
        addField(DbConst::IDSHORTDESC_FIELD_FORMAT.arg(n), QVariant::String);
        addField(DbConst::IDDESC_FIELD_FORMAT.arg(n), QVariant::String);
    }

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


int Patient::id() const
{
    QVariant pk = pkvalue();
    return pk.isNull() ? DbConst::NONEXISTENT_PK : pk.toInt();
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
    return DateTime::textDate(value(DOB_FIELD));
}


int Patient::ageYears() const
{
    return DateTime::ageYears(value(DOB_FIELD));
}


bool Patient::hasIdnum(int which_idnum) const
{
    return !idnumVariant(which_idnum).isNull();
}


QVariant Patient::idnumVariant(int which_idnum) const
{
    if (!DbConst::isValidWhichIdnum(which_idnum)) {
        return QVariant();
    }
    return value(IDNUM_FIELD_FORMAT.arg(which_idnum));
}


qlonglong Patient::idnumInteger(int which_idnum) const
{
    if (!DbConst::isValidWhichIdnum(which_idnum)) {
        return 0;
    }
    return valueULongLong(IDNUM_FIELD_FORMAT.arg(which_idnum));
}


OpenableWidget* Patient::editor(bool read_only)
{
    QuPagePtr page(new QuPage());
    page->setTitle(tr("Edit patient"));

    QuContainerGrid* grid = new QuContainerGrid();
    grid->setColumnStretch(0, 1);
    grid->setColumnStretch(1, 2);
    int row = 0;
    Qt::Alignment align = Qt::AlignRight | Qt::AlignTop;

    grid->addCell(QuGridCell(new QuText(tr("Surname")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(new QuLineEdit(fieldRef(FORENAME_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Forename")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(new QuLineEdit(fieldRef(SURNAME_FIELD, false)),
                             row++, 1));
    grid->addCell(QuGridCell(new QuText(tr("Sex")), row, 0, 1, 1, align));
    grid->addCell(QuGridCell(
        (new QuMCQ(fieldRef(SEX_FIELD),  // properly mandatory
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
    for (int n = 1; n <= DbConst::NUMBER_OF_IDNUMS; ++n) {
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
    page->addElement((new QuImage(UiFunc::iconFilename(UiConst::CBS_OK),
                                  UiConst::ICONSIZE))
                     ->addTag(TAG_POLICY_APP_OK));
    page->addElement((new QuImage(UiFunc::iconFilename(UiConst::ICON_STOP),
                                  UiConst::ICONSIZE))
                     ->addTag(TAG_POLICY_APP_FAIL));
    page->addElement(new QuHeading(tr("Minimum ID required for upload to server:")));
    page->addElement(new QuText(m_app.uploadPolicy().pretty()));
    page->addElement((new QuImage(UiFunc::iconFilename(UiConst::CBS_OK),
                                  UiConst::ICONSIZE))
                     ->addTag(TAG_POLICY_UPLOAD_OK));
    page->addElement((new QuImage(UiFunc::iconFilename(UiConst::ICON_STOP),
                                  UiConst::ICONSIZE))
                     ->addTag(TAG_POLICY_UPLOAD_FAIL));
    page->addElement(new QuHeading(tr("Minimum ID required to finalize on server:")));
    page->addElement(new QuText(m_app.finalizePolicy().pretty()));
    page->addElement((new QuImage(UiFunc::iconFilename(UiConst::CBS_OK),
                                  UiConst::ICONSIZE))
                     ->addTag(TAG_POLICY_FINALIZE_OK));
    page->addElement((new QuImage(UiFunc::iconFilename(UiConst::ICON_STOP),
                                  UiConst::ICONSIZE))
                     ->addTag(TAG_POLICY_FINALIZE_FAIL));

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
    for (int n = 1; n <= DbConst::NUMBER_OF_IDNUMS; ++n) {
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
    for (int n = 1; n <= DbConst::NUMBER_OF_IDNUMS; ++n) {
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
    for (int n = 1; n <= DbConst::NUMBER_OF_IDNUMS; ++n) {
        fieldRef(IDNUM_FIELD_FORMAT.arg(n))->setMandatory(!app);
    }

    bool upload = m_app.uploadPolicy().complies(attributes);
    m_questionnaire->setVisibleByTag(TAG_POLICY_UPLOAD_OK, upload);
    m_questionnaire->setVisibleByTag(TAG_POLICY_UPLOAD_FAIL, !upload);

    bool finalize = m_app.finalizePolicy().complies(attributes);
    m_questionnaire->setVisibleByTag(TAG_POLICY_FINALIZE_OK, finalize);
    m_questionnaire->setVisibleByTag(TAG_POLICY_FINALIZE_FAIL, !finalize);
}
