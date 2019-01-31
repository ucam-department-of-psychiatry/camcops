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

#include "ors.h"
#include "common/textconst.h"
#include "maths/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quhorizontalcontainer.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "questionnairelib/quverticalcontainer.h"
#include "tasklib/taskfactory.h"

using mathfunc::anyNullOrEmpty;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;

const QString Ors::ORS_TABLENAME("ors");

const int SESSION_MIN = 1;
const int SESSION_MAX = 1000;

const int COMPLETED_BY_SELF = 0;
const int COMPLETED_BY_OTHER = 1;

const int VAS_MIN_INT = 0;
const int VAS_MAX_INT = 10;
const int VAS_ABSOLUTE_CM = 10;

const int VAS_MAX_TOTAL = VAS_MAX_INT * 4;

const QString FN_SESSION("q_session");
const QString FN_DATE("q_date");
const QString FN_WHO("q_who");
const QString FN_WHO_OTHER("q_who_other");
const QString FN_INDIVIDUALLY("q_individually");
const QString FN_INTERPERSONALLY("q_interpersonally");
const QString FN_SOCIALLY("q_socially");
const QString FN_OVERALL("q_overall");

void initializeOrs(TaskFactory& factory)
{
    static TaskRegistrar<Ors> registered(factory);
}

Ors::Ors(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, ORS_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_SESSION, QVariant::Int);
    addField(FN_DATE, QVariant::Date);
    addField(FN_WHO, QVariant::Int);
    addField(FN_WHO_OTHER, QVariant::String);
    addField(FN_INDIVIDUALLY, QVariant::Int);
    addField(FN_INTERPERSONALLY, QVariant::Int);
    addField(FN_SOCIALLY, QVariant::Int);
    addField(FN_OVERALL, QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Ors::shortname() const
{
    return "ORS";
}


QString Ors::longname() const
{
    return tr("Outcome Rating Scale");
}


QString Ors::menusubtitle() const
{
    return tr("Fixed-length visual analogue scales measuring well-being");
}


// ============================================================================
// Instance info
// ============================================================================

bool Ors::isComplete() const
{
    const QStringList required_always{
        FN_SESSION,
        FN_DATE,
        FN_WHO,
        FN_INDIVIDUALLY,
        FN_INTERPERSONALLY,
        FN_SOCIALLY,
        FN_OVERALL,
    };

    if (anyNullOrEmpty(values(required_always))) {
        return false;
    }

    if (value(FN_WHO).toInt() == COMPLETED_BY_OTHER &&
         valueIsNullOrEmpty(FN_WHO_OTHER)) {
        return false;
    }

    return true;
}


QStringList Ors::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), VAS_MAX_TOTAL)};
}

int Ors::totalScore() const
{
    const QStringList vas_scales{
        FN_INDIVIDUALLY,
        FN_INTERPERSONALLY,
        FN_SOCIALLY,
        FN_OVERALL,
    };

    return sumInt(values(vas_scales));
}


QStringList Ors::detail() const
{
    QStringList lines;
    const QString sep = ": ";

    lines.append(xstring("session") + sep + value(FN_SESSION).toString());
    lines.append(xstring("date") + sep + value(FN_DATE).toString());
    lines.append("<b>Scores</b>");
    lines.append(xstring("q1_title") + sep + value(FN_INDIVIDUALLY).toString());
    lines.append(xstring("q2_title") + sep + value(FN_INTERPERSONALLY).toString());
    lines.append(xstring("q3_title") + sep + value(FN_SOCIALLY).toString());
    lines.append(xstring("q4_title") + sep + value(FN_OVERALL).toString());
    lines.append(summary());
    return lines;
}


OpenableWidget* Ors::editor(const bool read_only)
{
    const Qt::Alignment centre = Qt::AlignHCenter | Qt::AlignVCenter;

    m_completed_by = NameValueOptions{
       { xstring("who_a1"), COMPLETED_BY_SELF },
       { xstring("who_a2"), COMPLETED_BY_OTHER },
     };

    auto who_q = new QuMcq(fieldRef(FN_WHO), m_completed_by);
    who_q->setHorizontal(true)->setAsTextButton(true);

    QuPagePtr page(new QuPage{
        new QuHorizontalLine(),
        (new QuGridContainer{
                QuGridCell(new QuText(xstring("session")), 0, 0),
                QuGridCell(new QuLineEditInteger(fieldRef(FN_SESSION), SESSION_MIN, SESSION_MAX), 0, 1)
        })->setExpandHorizontally(false),
        (new QuGridContainer{
            QuGridCell(new QuText(xstring("date")), 0, 0),
            QuGridCell((new QuDateTime(fieldRef(FN_DATE)))->setMode(QuDateTime::DefaultDate)
                                              ->setOfferNowButton(true), 0, 1)
        })->setExpandHorizontally(false),
        (new QuGridContainer{
            QuGridCell(new QuText(xstring("who_q")), 0, 0),
            QuGridCell(who_q, 0, 1)
         })->setExpandHorizontally(false),
        new QuText(xstring("who_other_q")),
        new QuTextEdit(fieldRef(FN_WHO_OTHER), false),
        new QuHorizontalLine(),
        // ------------------------------------------------------------------------
        // Padding
        // ------------------------------------------------------------------------
        new QuSpacer(),
        new QuSpacer(),
        new QuSpacer(),
        new QuText(xstring("instructions_to_subject")),
        new QuSpacer(),
        // ------------------------------------------------------------------------
        // Visual-analogue sliders
        // ------------------------------------------------------------------------
        (new QuVerticalContainer{
            new QuText(xstring("q1_title")),
            new QuText(xstring("q1_subtitle")),
            (new QuSlider(fieldRef(FN_INDIVIDUALLY), VAS_MIN_INT, VAS_MAX_INT, 1))
                            ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM)
                            ->setSymmetric(true),
            new QuText(xstring("q2_title")) ,
            new QuText(xstring("q2_subtitle")),
            (new QuSlider(fieldRef(FN_INTERPERSONALLY), VAS_MIN_INT, VAS_MAX_INT, 1))
                            ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM)
                            ->setSymmetric(true),
            new QuText(xstring("q3_title")),
            new QuText(xstring("q3_subtitle")),
            (new QuSlider(fieldRef(FN_SOCIALLY), VAS_MIN_INT, VAS_MAX_INT, 1))
                            ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM)
                            ->setSymmetric(true),
            new QuText(xstring("q4_title")),
            new QuText(xstring("q4_subtitle")),
            (new QuSlider(fieldRef(FN_OVERALL), VAS_MIN_INT, VAS_MAX_INT, 1))
                            ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM)
                            ->setSymmetric(true),
         })->setWidgetAlignment(centre),
        // ------------------------------------------------------------------------
        // Padding
        // ------------------------------------------------------------------------
        new QuSpacer(),
        new QuSpacer(),
        new QuHorizontalLine(),
        new QuSpacer(),
        // ------------------------------------------------------------------------
        // Footer
        // ------------------------------------------------------------------------
        (new QuVerticalContainer{
            new QuText(xstring("copyright")),
            new QuText(xstring("licensing"))
        })->setWidgetAlignment(centre)

    });

    bool required = valueInt(FN_WHO) == COMPLETED_BY_OTHER;
    fieldRef(FN_WHO_OTHER)->setMandatory(required);

    connect(fieldRef(FN_WHO).data(), &FieldRef::valueChanged,
            this, &Ors::updateMandatory);

    page->setTitle(longname());

    m_questionnaire = new Questionnaire(m_app, {page});

    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

void Ors::updateMandatory() {
   const bool required = valueInt(FN_WHO)
           == COMPLETED_BY_OTHER;
    fieldRef(FN_WHO_OTHER)->setMandatory(required);
    if (!required) {
        fieldRef(FN_WHO_OTHER)->setValue("");
    }
}
