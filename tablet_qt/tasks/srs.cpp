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

#include "srs.h"
#include "common/textconst.h"
#include "maths/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quflowcontainer.h"
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

const QString Srs::SRS_TABLENAME("srs");

const int SESSION_MIN = 1;
const int SESSION_MAX = 1000;

const int VAS_MIN_INT = 0;
const int VAS_MAX_INT = 10;
const int VAS_ABSOLUTE_CM = 10;

const int VAS_MAX_TOTAL = VAS_MAX_INT * 4;

const QString FN_SESSION("q_session");
const QString FN_DATE("q_date");
const QString FN_RELATIONSHIP("q_relationship");
const QString FN_GOALS("q_goals");
const QString FN_APPROACH("q_approach");
const QString FN_OVERALL("q_overall");

void initializeSrs(TaskFactory& factory)
{
    static TaskRegistrar<Srs> registered(factory);
}

Srs::Srs(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, SRS_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_SESSION, QVariant::Int);
    addField(FN_DATE, QVariant::Date);
    addField(FN_RELATIONSHIP, QVariant::Int);
    addField(FN_GOALS, QVariant::Int);
    addField(FN_APPROACH, QVariant::Int);
    addField(FN_OVERALL, QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Srs::shortname() const
{
    return "SRS";
}


QString Srs::longname() const
{
    return tr("Session Rating Scale");
}


QString Srs::menusubtitle() const
{
    return tr("Fixed-length visual analogue scales for providing session feedback");
}


// ============================================================================
// Instance info
// ============================================================================

bool Srs::isComplete() const
{
    const QStringList required_always{
        FN_SESSION,
        FN_DATE,
        FN_RELATIONSHIP,
        FN_GOALS,
        FN_APPROACH,
        FN_OVERALL,
    };

    return !anyNullOrEmpty(values(required_always));
}


QStringList Srs::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), VAS_MAX_TOTAL)};
}

QStringList Srs::detail() const
{
    QStringList lines;

    lines.append(xstring("session") + value(FN_SESSION).toString());
    lines.append(xstring("date") + value(FN_DATE).toString());
    lines.append("<b>Scores</b>");
    const QString vas_sep = ": ";
    lines.append(xstring("q1_title") + vas_sep + value(FN_RELATIONSHIP).toString());
    lines.append(xstring("q2_title") + vas_sep + value(FN_GOALS).toString());
    lines.append(xstring("q3_title") + vas_sep + value(FN_APPROACH).toString());
    lines.append(xstring("q4_title") + vas_sep + value(FN_OVERALL).toString());
    lines.append(summary());
    return lines;
}

OpenableWidget* Srs::editor(const bool read_only)
{
    auto vas_relationship = (new QuSlider(fieldRef(FN_RELATIONSHIP), VAS_MIN_INT, VAS_MAX_INT, 1))
                                    ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM)
                                    ->setSymmetric(true);
    auto vas_goals = (new QuSlider(fieldRef(FN_GOALS), VAS_MIN_INT, VAS_MAX_INT, 1))
                                    ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM)
                                    ->setSymmetric(true);
    auto vas_approach = (new QuSlider(fieldRef(FN_APPROACH), VAS_MIN_INT, VAS_MAX_INT, 1))
                                    ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM)
                                    ->setSymmetric(true);
    auto vas_overall = (new QuSlider(fieldRef(FN_OVERALL), VAS_MIN_INT, VAS_MAX_INT, 1))
                                    ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM)
                                    ->setSymmetric(true);

    const Qt::Alignment centre = Qt::AlignHCenter | Qt::AlignVCenter;

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
        new QuHorizontalLine(),
        // ------------------------------------------------------------------------
        // Padding
        // ------------------------------------------------------------------------
        new QuSpacer(),
        (new QuText(xstring("instructions_to_subject")))
                       ->setItalic()
                       ->setAlignment(centre),
        new QuSpacer(),
        new QuHorizontalLine(),
        new QuSpacer(),
        // ------------------------------------------------------------------------
        // Visual-analogue sliders
        // ------------------------------------------------------------------------
        (new QuVerticalContainer{
            (new QuText(xstring("q1_title")))->setAlignment(centre),
            new QuGridContainer{
                QuGridCell((new QuText(xstring("q1_right")))->setAlignment(centre), 0, 0, 3, 1),
                QuGridCell(vas_relationship, 1, 1, 1, 1),
                QuGridCell((new QuText(xstring("q1_right")))->setAlignment(centre), 0, 2, 3, 1),
            },
            (new QuText(xstring("q2_title")))->setAlignment(centre),
            new QuGridContainer{
                QuGridCell((new QuText(xstring("q2_right")))->setAlignment(centre), 0, 0, 3, 1),
                QuGridCell(vas_goals, 1, 1, 1, 1),
                QuGridCell((new QuText(xstring("q2_right")))->setAlignment(centre), 0, 2, 3, 1),
            },
            (new QuText(xstring("q3_title")))->setAlignment(centre),
            new QuGridContainer{
                    QuGridCell((new QuText(xstring("q3_right")))->setAlignment(centre), 0, 0, 3, 1),
                    QuGridCell(vas_approach, 1, 1, 1, 1),
                    QuGridCell((new QuText(xstring("q3_right")))->setAlignment(centre),  0, 2, 3, 1),
            },
            (new QuText(xstring("q4_title")))->setAlignment(centre),
            new QuGridContainer{
                QuGridCell((new QuText(xstring("q4_left")))->setAlignment(centre), 0, 0, 3, 1),
                QuGridCell(vas_overall, 1, 1, 1, 1),
                QuGridCell((new QuText(xstring("q4_right")))->setAlignment(centre), 0, 2, 3, 1),
            }
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

    page->setTitle(longname());

    m_questionnaire = new Questionnaire(m_app, {page});

    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

int Srs::totalScore() const
{
    const QStringList vas_scales{
        FN_RELATIONSHIP,
        FN_GOALS,
        FN_APPROACH,
        FN_OVERALL,
    };

    return sumInt(values(vas_scales));
}
