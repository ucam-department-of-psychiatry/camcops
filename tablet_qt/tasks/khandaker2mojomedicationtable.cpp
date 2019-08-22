/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#include "khandaker2mojomedicationtable.h"
#include "common/cssconst.h"
#include "common/textconst.h"
#include "lib/convert.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionwithonefield.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"


const QString Khandaker2MojoMedicationTable::KHANDAKER2MOJOMEDICATIONTABLE_TABLENAME(
    "khandaker_2_mojomedicationtable");

const QString Q_XML_PREFIX = "q_";

// Section 1: General Information
const QString FN_DIAGNOSIS("diagnosis");
const QString FN_DIAGNOSIS_DATE("diagnosis_date");
const QString FN_DIAGNOSIS_DATE_APPROXIMATE("diagnosis_date_approximate");
const QString FN_HAS_FIBROMYALGIA("has_fibromyalgia");
const QString FN_IS_PREGNANT("is_pregnant");
const QString FN_HAS_INFECTION_PAST_MONTH("has_infection_past_month");
const QString FN_HAD_INFECTION_TWO_MONTHS_PRECEDING("had_infection_two_months_preceding");
const QString FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE("has_alcohol_substance_dependence");
const QString FN_SMOKING_STATUS("smoking_status");
const QString FN_ALCOHOL_UNITS_PER_WEEK("alcohol_units_per_week");

// Section 2: Medical History
const QString FN_DEPRESSION("depression");
const QString FN_BIPOLAR_DISORDER("bipolar_disorder");
const QString FN_SCHIZOPHRENIA("schizophrenia");
const QString FN_AUTISM("autism");
const QString FN_PTSD("ptsd");
const QString FN_ANXIETY("anxiety");
const QString FN_PERSONALITY_DISORDER("personality_disorder");
const QString FN_INTELLECTUAL_DISABILITY("intellectual_disability");
const QString FN_OTHER_MENTAL_ILLNESS("other_mental_illness");
const QString FN_OTHER_MENTAL_ILLNESS_DETAILS("other_mental_illness_details");
const QString FN_HOSPITALISED_IN_LAST_YEAR("hospitalised_in_last_year");
const QString FN_HOSPITALISATION_DETAILS("hospitalisation_details");

// Section 3: Family history
const QString FN_FAMILY_DEPRESSION("family_depression");
const QString FN_FAMILY_BIPOLAR_DISORDER("family_bipolar_disorder");
const QString FN_FAMILY_SCHIZOPHRENIA("family_schizophrenia");
const QString FN_FAMILY_AUTISM("family_autism");
const QString FN_FAMILY_PTSD("family_ptsd");
const QString FN_FAMILY_ANXIETY("family_anxiety");
const QString FN_FAMILY_PERSONALITY_DISORDER("family_personality_disorder");
const QString FN_FAMILY_INTELLECTUAL_DISABILITY("family_intellectual_disability");
const QString FN_FAMILY_OTHER_MENTAL_ILLNESS("family_other_mental_illness");
const QString FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS("family_other_mental_illness_details");

const QStringList MANDATORY_FIELDNAMES{
    FN_DIAGNOSIS,
    FN_DIAGNOSIS_DATE,
    FN_HAS_FIBROMYALGIA,
    FN_IS_PREGNANT,
    FN_HAS_INFECTION_PAST_MONTH,
    FN_HAD_INFECTION_TWO_MONTHS_PRECEDING,
    FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE,
    FN_SMOKING_STATUS,
    FN_ALCOHOL_UNITS_PER_WEEK,

    FN_DEPRESSION,
    FN_BIPOLAR_DISORDER,
    FN_SCHIZOPHRENIA,
    FN_AUTISM,
    FN_PTSD,
    FN_ANXIETY,
    FN_PERSONALITY_DISORDER,
    FN_INTELLECTUAL_DISABILITY,
    FN_OTHER_MENTAL_ILLNESS,
    FN_HOSPITALISED_IN_LAST_YEAR,

    FN_FAMILY_DEPRESSION,
    FN_FAMILY_BIPOLAR_DISORDER,
    FN_FAMILY_SCHIZOPHRENIA,
    FN_FAMILY_AUTISM,
    FN_FAMILY_PTSD,
    FN_FAMILY_ANXIETY,
    FN_FAMILY_PERSONALITY_DISORDER,
    FN_FAMILY_INTELLECTUAL_DISABILITY,
    FN_FAMILY_OTHER_MENTAL_ILLNESS,
};

void initializeKhandaker2MojoMedicationTable(TaskFactory& factory)
{
    static TaskRegistrar<Khandaker2MojoMedicationTable> registered(factory);
}


Khandaker2MojoMedicationTable::Khandaker2MojoMedicationTable(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, KHANDAKER2MOJOMEDICATIONTABLE_TABLENAME,
         false, false, false)  // ... anon, clin, resp
{
    // TODO: Add fields

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}



// ============================================================================
// Class info
// ============================================================================

QString Khandaker2MojoMedicationTable::shortname() const
{
    return "Khandaker_2_Mojomedicationtable";
}


QString Khandaker2MojoMedicationTable::longname() const
{
    return tr("Khandaker GM — 2 MOJO Study — Medications and Treatment");
}


QString Khandaker2MojoMedicationTable::description() const
{
    return tr("Medications and Treatment Table for MOJO Study.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Khandaker2MojoMedicationTable::isComplete() const
{
    // TODO

    return true;
}


QStringList Khandaker2MojoMedicationTable::summary() const
{
    return QStringList{TextConst::noSummarySeeFacsimile()};
}


QStringList Khandaker2MojoMedicationTable::detail() const
{
    QStringList lines;

    // TODO

    return completenessInfo() + lines;
}


OpenableWidget* Khandaker2MojoMedicationTable::editor(const bool read_only)
{
    QuPagePtr page(new QuPage);

    // TODO: Widgets

    QVector<QuPagePtr> pages{page};

    auto questionnaire = new Questionnaire(m_app, pages);
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);

    return questionnaire;
}

QString Khandaker2MojoMedicationTable::getOptionName(
    const QString &fieldname, const int index) const
{
    return xstring(QString("%1_%2").arg(fieldname).arg(index));
}
