/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

// #define DEBUG_DATA_FLOW

#include "bmi.h"

#include "common/textconst.h"
#include "lib/convert.h"
#include "maths/mathfunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheight.h"
#include "questionnairelib/qumass.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "questionnairelib/quwaist.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using convert::toDp;
using mathfunc::noneNull;

const QString Bmi::BMI_TABLENAME("bmi");

const QString FN_MASS_KG("mass_kg");
const QString FN_HEIGHT_M("height_m");
const QString FN_WAIST_CM("waist_cm");
const QString FN_COMMENT("comment");

// const int BMI_DP = 2;


void initializeBmi(TaskFactory& factory)
{
    static TaskRegistrar<Bmi> registered(factory);
}

Bmi::Bmi(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, BMI_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_MASS_KG, QMetaType::fromType<double>());
    addField(FN_HEIGHT_M, QMetaType::fromType<double>());
    addField(FN_WAIST_CM, QMetaType::fromType<double>());
    addField(FN_COMMENT, QMetaType::fromType<QString>());

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

QString Bmi::description() const
{
    return tr("Mass, height, BMI; also waist circumference.");
}

// ============================================================================
// Instance info
// ============================================================================

bool Bmi::isComplete() const
{
    // Waist circumference optional
    return noneNull(values({FN_MASS_KG, FN_HEIGHT_M}));
}

QStringList Bmi::summary() const
{
    QStringList lines;

    lines.append(QString("%1 kg, %2 m; BMI = %3 kg/m^2; %4.")
                     .arg(
                         prettyValue(FN_MASS_KG),
                         prettyValue(FN_HEIGHT_M),
                         bmiString(),
                         category()
                     ));

    if (!valueIsNullOrEmpty(FN_WAIST_CM)) {
        lines.append(
            QString("%1 %2 cm.")
                .arg(tr("Waist circumference:"), prettyValue(FN_WAIST_CM))
        );
    }

    if (!valueIsNullOrEmpty(FN_COMMENT)) {
        lines.append(
            QString("%1 %2").arg(tr("Comments:"), valueString(FN_COMMENT))
        );
    }

    return lines;
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

    auto height_units = new QuUnitSelector(CommonOptions::heightUnits());
    auto height_edit = new QuHeight(fieldRef(FN_HEIGHT_M), height_units);
    auto mass_units = new QuUnitSelector(CommonOptions::massUnits());
    auto mass_edit = new QuMass(fieldRef(FN_MASS_KG), mass_units);
    auto waist_units = new QuUnitSelector(CommonOptions::waistUnits());
    auto waist_edit = new QuWaist(
        fieldRef(FN_WAIST_CM),
        waist_units,
        false
    );  // Not mandatory

    // Comments
    FieldRefPtr fr_comment = fieldRef(FN_COMMENT, false);

    QuPagePtr page(
        (new QuPage{
             // ---------------------------------------------------------------
             // Height
             // ---------------------------------------------------------------
             heading("title_1"),
             height_units,
             heading("title_2"),
             height_edit,
             // ---------------------------------------------------------------
             // Mass
             // ---------------------------------------------------------------
             heading("title_3"),
             mass_units,
             heading("title_4"),
             mass_edit,
             // ---------------------------------------------------------------
             // Waist circumference
             // ---------------------------------------------------------------
             new QuText(xstring("optional")),
             heading("title_5"),
             waist_units,
             heading("title_6"),
             waist_edit,
             // ---------------------------------------------------------------
             // Comments
             // ---------------------------------------------------------------
             (new QuText(TextConst::comments()))->setBold(true),
             new QuTextEdit(fr_comment),
         })
            ->setTitle(longname())
    );

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Clinician);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

QVariant Bmi::bmiVariant() const
{
    if (!isCompleteCached()) {
        return QVariant();
    }
    const double mass_kg = valueDouble(FN_MASS_KG);
    const double height_m = valueDouble(FN_HEIGHT_M);

    if (abs(height_m) < 0.0001) {
        // It is possible that a platform may not handle division by zero. We
        // could also limit height to a sensible range. It's probably better to
        // allow a patient to skip this task altogether rather than end up with
        // silly small height values.
        return QVariant();
    }

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
