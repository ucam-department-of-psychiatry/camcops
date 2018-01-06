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

#include "bmi.h"
#include "common/textconst.h"
#include "lib/convert.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"
using convert::toDp;
using mathfunc::noneNull;

const QString Bmi::BMI_TABLENAME("bmi");

const QString FN_MASS_KG("mass_kg");
const QString FN_HEIGHT_M("height_m");
const QString FN_COMMENT("comment");

const QString TAG_MASS_METRIC("mass_metric");
const QString TAG_MASS_IMPERIAL("mass_imperial");
const QString TAG_HEIGHT_METRIC("height_metric");
const QString TAG_HEIGHT_IMPERIAL("height_imperial");
const int BMI_DP = 2;
const int METRIC = 0;
const int IMPERIAL = 1;
const int BOTH = 2;


void initializeBmi(TaskFactory& factory)
{
    static TaskRegistrar<Bmi> registered(factory);
}


Bmi::Bmi(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, BMI_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr),
    m_height_units(METRIC),
    m_mass_units(METRIC),
    m_fr_height_m(nullptr),
    m_fr_height_ft(nullptr),
    m_fr_height_in(nullptr),
    m_fr_mass_kg(nullptr),
    m_fr_mass_st(nullptr),
    m_fr_mass_lb(nullptr),
    m_fr_mass_oz(nullptr)
{
    addField(FN_MASS_KG, QVariant::Double);
    addField(FN_HEIGHT_M, QVariant::Double);
    addField(FN_COMMENT, QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Bmi::shortname() const
{
    return "BMI";
}


QString Bmi::longname() const
{
    return tr("Body mass index");
}


QString Bmi::menusubtitle() const
{
    return tr("Mass, height.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Bmi::isComplete() const
{
    return noneNull(values({FN_MASS_KG, FN_HEIGHT_M}));
}


QStringList Bmi::summary() const
{
    QString commenttext;
    if (!valueIsNullOrEmpty(FN_COMMENT)) {
        commenttext = QString(" (%1 %2)")
                .arg(tr("Comments:"),
                     valueString(FN_COMMENT));
    }
    const QString s = QString("%1 kg, %2 m; BMI = %3 kg/m^2; %4%5")
            .arg(prettyValue(FN_MASS_KG),
                 prettyValue(FN_HEIGHT_M),
                 bmiString(),
                 category(),
                 commenttext);
    return QStringList{s};
}


QStringList Bmi::detail() const
{
    return completenessInfo() + summary();
}


OpenableWidget* Bmi::editor(const bool read_only)
{
    auto heading = [this](const QString& xstringname) -> QuElement* {
        return (new QuText(xstring(xstringname)))->setBold(true);
    };
    auto choose_units = [this](FieldRefPtr fieldref,
                               const NameValueOptions& options) -> QuElement* {
        return (new QuMcq(fieldref, options))
                ->setHorizontal(true)
                ->setAsTextButton(true);
    };

    // Internal plumbing:
    // - We want imperial units to update when metric values are changed, and
    //   vice versa.
    // - We can't set up an infinite loop, though, e.g.
    //      metres.valueChanged() -> feet.valueChanged()
    //      feet.valueChanged() -> metres.valueChanged()
    // - The other obvious way is to hold onto a member copy of the fieldrefs,
    //   and manually cause them to emit valueChanged() at approriate times.
    //
    // BEWARE the consequences of floating-point error, e.g.
    // - 7 st 12 lb 0 oz -> 49.8951 kg
    // - 49.8951 kg -> 7 st 11 lb 0.999779 oz
    // ... the potential change in OTHER units means that all parts must be
    // updated, OR, a little more elegantly, internal records of the imperial
    // units kept.

    // Height
    const NameValueOptions options_height_units{
        {xstring("metric_height"), METRIC},
        {xstring("imperial_height"), IMPERIAL},
        {xstring("units_both"), BOTH},
    };
    FieldRef::GetterFunction get_height_units = std::bind(&Bmi::getHeightUnits, this);
    FieldRef::GetterFunction get_m = std::bind(&Bmi::getHeightM, this);
    FieldRef::GetterFunction get_ft = std::bind(&Bmi::getHeightFt, this);
    FieldRef::GetterFunction get_in = std::bind(&Bmi::getHeightIn, this);
    FieldRef::SetterFunction set_height_units = std::bind(&Bmi::setHeightUnits, this, std::placeholders::_1);
    FieldRef::SetterFunction set_m = std::bind(&Bmi::setHeightM, this, std::placeholders::_1);
    FieldRef::SetterFunction set_ft = std::bind(&Bmi::setHeightFt, this, std::placeholders::_1);
    FieldRef::SetterFunction set_in = std::bind(&Bmi::setHeightIn, this, std::placeholders::_1);
    FieldRefPtr fr_height_units(new FieldRef(get_height_units, set_height_units, true));
    m_fr_height_m = FieldRefPtr(new FieldRef(get_m, set_m, true));
    m_fr_height_ft = FieldRefPtr(new FieldRef(get_ft, set_ft, true));
    m_fr_height_in = FieldRefPtr(new FieldRef(get_in, set_in, true));

    // Mass
    const NameValueOptions options_mass_units{
        {xstring("metric_mass"), METRIC},
        {xstring("imperial_mass"), IMPERIAL},
        {xstring("units_both"), BOTH},
    };
    FieldRef::GetterFunction get_mass_units = std::bind(&Bmi::getMassUnits, this);
    FieldRef::GetterFunction get_kg = std::bind(&Bmi::getMassKg, this);
    FieldRef::GetterFunction get_st = std::bind(&Bmi::getMassSt, this);
    FieldRef::GetterFunction get_lb = std::bind(&Bmi::getMassLb, this);
    FieldRef::GetterFunction get_oz = std::bind(&Bmi::getMassOz, this);
    FieldRef::SetterFunction set_mass_units = std::bind(&Bmi::setMassUnits, this, std::placeholders::_1);
    FieldRef::SetterFunction set_kg = std::bind(&Bmi::setMassKg, this, std::placeholders::_1);
    FieldRef::SetterFunction set_st = std::bind(&Bmi::setMassSt, this, std::placeholders::_1);
    FieldRef::SetterFunction set_lb = std::bind(&Bmi::setMassLb, this, std::placeholders::_1);
    FieldRef::SetterFunction set_oz = std::bind(&Bmi::setMassOz, this, std::placeholders::_1);
    FieldRefPtr fr_mass_units(new FieldRef(get_mass_units, set_mass_units, true));
    m_fr_mass_kg = FieldRefPtr(new FieldRef(get_kg, set_kg, true));
    m_fr_mass_st = FieldRefPtr(new FieldRef(get_st, set_st, true));
    m_fr_mass_lb = FieldRefPtr(new FieldRef(get_lb, set_lb, true));
    m_fr_mass_oz = FieldRefPtr(new FieldRef(get_oz, set_oz, true));

    // Comments
    FieldRefPtr fr_comment = fieldRef(FN_COMMENT, false);

    QuPagePtr page((new QuPage{
        // --------------------------------------------------------------------
        // Height
        // --------------------------------------------------------------------
        heading("title_1"),
        choose_units(fr_height_units, options_height_units),
        heading("title_2"),
        questionnairefunc::defaultGridRawPointer({
            {
                xstring("m"),
                new QuLineEditDouble(m_fr_height_m, 0, 5, 3),
            },
        }, 1, 1)->addTag(TAG_HEIGHT_METRIC),
        questionnairefunc::defaultGridRawPointer({
            {
                xstring("ft"),
                new QuLineEditInteger(m_fr_height_ft, 0, 15),
            },
            {
                xstring("in"),
                new QuLineEditDouble(m_fr_height_in, 0, convert::INCHES_PER_FOOT, 2),
            },
        }, 1, 1)->addTag(TAG_HEIGHT_IMPERIAL),
        // --------------------------------------------------------------------
        // Mass
        // --------------------------------------------------------------------
        heading("title_3"),
        choose_units(fr_mass_units, options_mass_units),
        heading("title_4"),
        questionnairefunc::defaultGridRawPointer({
            {
                xstring("kg"),
                new QuLineEditDouble(m_fr_mass_kg, 0, 1000, 3),
            },
        }, 1, 1)->addTag(TAG_MASS_METRIC),
        questionnairefunc::defaultGridRawPointer({
            {
                xstring("st"),
                new QuLineEditInteger(m_fr_mass_st, 0, 150),
            },
            {
                xstring("lb"),
                new QuLineEditInteger(m_fr_mass_lb, 0, convert::POUNDS_PER_STONE),
            },
            {
                xstring("oz"),
                new QuLineEditDouble(m_fr_mass_oz, 0, convert::OUNCES_PER_POUND, 2),
            },
        }, 1, 1)->addTag(TAG_MASS_IMPERIAL),
        // --------------------------------------------------------------------
        // Comments
        // --------------------------------------------------------------------
        (new QuText(textconst::COMMENTS))->setBold(true),
        new QuTextEdit(fr_comment),
    })->setTitle(longname()));

    connect(fr_mass_units.data(), &FieldRef::valueChanged,
            this, &Bmi::massUnitsChanged);
    connect(fr_height_units.data(), &FieldRef::valueChanged,
            this, &Bmi::heightUnitsChanged);

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Clinician);
    m_questionnaire->setReadOnly(read_only);
    updateImperialHeight();
    updateImperialMass();
    massUnitsChanged();
    heightUnitsChanged();
    return m_questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

QVariant Bmi::bmiVariant() const
{
    if (!isComplete()) {
        return QVariant();
    }
    const double mass_kg = valueDouble(FN_MASS_KG);
    const double height_m = valueDouble(FN_HEIGHT_M);
    const double bmi = mass_kg / (height_m * height_m);
    return QVariant(bmi);
}


QString Bmi::bmiString(const int dp) const
{
    const QVariant bmi = bmiVariant();
    if (bmi.isNull()) {
        return "?";
    }
    return toDp(bmi.toDouble(), dp);
}


QString Bmi::category() const
{
    const QVariant bmiv = bmiVariant();
    if (bmiv.isNull()) {
        return "?";
    }
    const double bmi = bmiv.toDouble();
    if (bmi >= 40) {
        return xstring("obese_3");
    }
    if (bmi >= 35) {
        return xstring("obese_2");
    }
    if (bmi >= 30) {
        return xstring("obese_1");
    }
    if (bmi >= 25) {
        return xstring("overweight");
    }
    if (bmi >= 18.5) {
        return xstring("normal");
    }
    if (bmi >= 17.5) {
        return xstring("underweight_17.5_18.5");
    }
    if (bmi >= 17) {
        return xstring("underweight_17_17.5");
    }
    if (bmi >= 16) {
        return xstring("underweight_16_17");
    }
    if (bmi >= 15) {
        return xstring("underweight_15_16");
    }
    if (bmi >= 13) {
        return xstring("underweight_13_15");
    }
    return xstring("underweight_under_13");
}


// ============================================================================
// Signal handlers
// ============================================================================

void Bmi::massUnitsChanged()
{
    if (!m_questionnaire) {
        return;
    }
    const bool imperial = m_mass_units == IMPERIAL || m_mass_units == BOTH;
    const bool metric = m_mass_units == METRIC || m_mass_units == BOTH;
    m_questionnaire->setVisibleByTag(TAG_MASS_IMPERIAL, imperial, false);
    m_questionnaire->setVisibleByTag(TAG_MASS_METRIC, metric, false);
}


void Bmi::heightUnitsChanged()
{
    if (!m_questionnaire) {
        return;
    }
    const bool imperial = m_height_units == IMPERIAL || m_height_units == BOTH;
    const bool metric = m_height_units == METRIC || m_height_units == BOTH;
    Q_ASSERT(imperial || metric);
    m_questionnaire->setVisibleByTag(TAG_HEIGHT_IMPERIAL, imperial, false);
    m_questionnaire->setVisibleByTag(TAG_HEIGHT_METRIC, metric, false);
}


// ============================================================================
// Getters/setters
// ============================================================================

QVariant Bmi::getHeightUnits() const
{
    return m_height_units;
}


QVariant Bmi::getHeightM() const
{
    return value(FN_HEIGHT_M);
}


QVariant Bmi::getHeightFt() const
{
    return m_height_ft;
}


QVariant Bmi::getHeightIn() const
{
    return m_height_in;
}


bool Bmi::setHeightUnits(const QVariant& value)  // returns: changed?
{
    int height_units = value.toInt();
    if (height_units != METRIC && height_units != IMPERIAL &&
            height_units != BOTH) {
        height_units = METRIC;
    }
    const bool changed = height_units != m_height_units;
    m_height_units = height_units;
    return changed;
}


bool Bmi::setHeightM(const QVariant& value)
{
    const bool changed = setValue(FN_HEIGHT_M, value);
    if (changed) {
        updateImperialHeight();
    }
    return changed;
}


bool Bmi::setHeightFt(const QVariant& value)
{
    Q_ASSERT(m_fr_height_m);
    const bool changed = value != m_height_ft;
    if (changed) {
        m_height_ft = value;
        updateMetricHeight();
    }
    return changed;
}


bool Bmi::setHeightIn(const QVariant& value)
{
    Q_ASSERT(m_fr_height_m);
    const bool changed = value != m_height_in;
    if (changed) {
        m_height_in = value;
        updateMetricHeight();
    }
    return changed;
}


void Bmi::updateMetricHeight()
{
    Q_ASSERT(m_fr_height_m);
    if (m_height_ft.isNull() && m_height_in.isNull()) {
        setValue(FN_HEIGHT_M, m_height_ft);
    } else {
        const int feet = m_height_ft.toInt();
        const double inches = m_height_in.toDouble();
        setValue(FN_HEIGHT_M, convert::metresFromFeetInches(feet, inches));
    }
    m_fr_height_m->emitValueChanged();
}


void Bmi::updateImperialHeight()
{
    Q_ASSERT(m_fr_height_ft);
    Q_ASSERT(m_fr_height_in);
    const QVariant height_m_var = value(FN_HEIGHT_M);
    if (height_m_var.isNull()) {
        m_height_ft.clear();
        m_height_in.clear();
    } else {
        const double height_m = height_m_var.toDouble();
        int feet;
        double inches;
        convert::feetInchesFromMetres(height_m, feet, inches);
        m_height_ft = feet;
        m_height_in = inches;
    }
    m_fr_height_ft->emitValueChanged();
    m_fr_height_in->emitValueChanged();
}


QVariant Bmi::getMassUnits() const
{
    return m_mass_units;
}


QVariant Bmi::getMassKg() const
{
    return value(FN_MASS_KG);
}


QVariant Bmi::getMassSt() const
{
    return m_mass_st;
}


QVariant Bmi::getMassLb() const
{
    return m_mass_lb;
}


QVariant Bmi::getMassOz() const
{
    return m_mass_oz;
}


bool Bmi::setMassUnits(const QVariant& value)
{
    int mass_units = value.toInt();
    if (mass_units != METRIC && mass_units != IMPERIAL && mass_units != BOTH) {
        mass_units = METRIC;
    }
    const bool changed = mass_units != m_mass_units;
    m_mass_units = mass_units;
    return changed;
}


bool Bmi::setMassKg(const QVariant& value)
{
    const bool changed = setValue(FN_MASS_KG, value);
    if (changed) {
        updateImperialMass();
    }
    return changed;
}


bool Bmi::setMassSt(const QVariant& value)
{
    const bool changed = value != m_mass_st;
    if (changed) {
        m_mass_st = value;
        updateMetricMass();
    }
    return changed;
}


bool Bmi::setMassLb(const QVariant& value)
{
    Q_ASSERT(m_fr_mass_kg);
    const bool changed = value != m_mass_lb;
    if (changed) {
        m_mass_lb = value;
        updateMetricMass();
    }
    return changed;
}


bool Bmi::setMassOz(const QVariant& value)
{
    Q_ASSERT(m_fr_mass_kg);
    const bool changed = value != m_mass_oz;
    if (changed) {
        m_mass_oz = value;
        updateMetricMass();
    }
    return changed;
}


void Bmi::updateMetricMass()
{
    Q_ASSERT(m_fr_mass_kg);
    if (m_mass_st.isNull() && m_mass_lb.isNull() && m_mass_oz.isNull()) {
        setValue(FN_MASS_KG, m_mass_st);
    } else {
        const int stones = m_mass_st.toInt();
        const int pounds = m_mass_lb.toInt();
        const double ounces = m_mass_oz.toDouble();
        setValue(FN_MASS_KG, convert::kilogramsFromStonesPoundsOunces(
                     stones, pounds, ounces));
    }
    m_fr_mass_kg->emitValueChanged();
}


void Bmi::updateImperialMass()
{
    Q_ASSERT(m_fr_mass_st);
    Q_ASSERT(m_fr_mass_lb);
    Q_ASSERT(m_fr_mass_oz);
    QVariant mass_kg_var = value(FN_MASS_KG);
    if (mass_kg_var.isNull()) {
        m_mass_st.clear();
        m_mass_lb.clear();
        m_mass_oz.clear();
    } else {
        const double mass_kg = mass_kg_var.toDouble();
        int stones, pounds;
        double ounces;
        convert::stonesPoundsOuncesFromKilograms(mass_kg, stones, pounds, ounces);
        m_mass_st = stones;
        m_mass_lb = pounds;
        m_mass_oz = ounces;
    }
    m_fr_mass_st->emitValueChanged();
    m_fr_mass_lb->emitValueChanged();
    m_fr_mass_oz->emitValueChanged();
}
