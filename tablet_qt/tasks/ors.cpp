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

const QString Ors::ORS_TABLENAME("ors");

const int SESSION_MIN = 1;
const int SESSION_MAX = 1000;

const int COMPLETED_BY_SELF = 0;
const int COMPLETED_BY_OTHER = 1;

const int VAS_MIN_INT = 0;
const int VAS_MAX_INT = 10;
const int VAS_ABSOLUTE_CM = 10;

void initializeOrs(TaskFactory& factory)
{
    static TaskRegistrar<Ors> registered(factory);
}

Ors::Ors(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, ORS_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField("session", QVariant::Int);
    addField("date", QVariant::Date);
    addField("who_q", QVariant::Int);
    addField("who_other_q", QVariant::String);

    addField("slider_1", QVariant::Int);
    addField("slider_2", QVariant::Int);
    addField("slider_3", QVariant::Int);
    addField("slider_4", QVariant::Int);

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
    return tr("");
}


// ============================================================================
// Instance info
// ============================================================================

bool Ors::isComplete() const
{
    return false;
}


QStringList Ors::summary() const
{
    return QStringList{};
}


QStringList Ors::detail() const
{
    QStringList lines;
    return lines;
}


OpenableWidget* Ors::editor(const bool read_only)
{
    const Qt::Alignment centre = Qt::AlignHCenter | Qt::AlignVCenter;

    m_completed_by = NameValueOptions{
       { xstring("who_a1"), COMPLETED_BY_SELF },
       { xstring("who_a2"), COMPLETED_BY_OTHER },
     };

    auto who_q = new QuMcq(fieldRef("who_q"), m_completed_by);
    who_q->setHorizontal(true)->setAsTextButton(true);

    QuPagePtr page(new QuPage{
        new QuHorizontalLine(),
        (new QuGridContainer{
                QuGridCell(new QuText(xstring("session")), 0, 0),
                QuGridCell(new QuLineEditInteger(fieldRef("session"), SESSION_MIN, SESSION_MAX), 0, 1)
        })->setExpandHorizontally(false),
        (new QuGridContainer{
            QuGridCell(new QuText(xstring("date")), 0, 0),
            QuGridCell((new QuDateTime(fieldRef("date")))->setMode(QuDateTime::DefaultDate)
                                              ->setOfferNowButton(true), 0, 1)
        })->setExpandHorizontally(false),
        (new QuGridContainer{
            QuGridCell(new QuText(xstring("who_q")), 0, 0),
            QuGridCell(who_q, 0, 1)
         })->setExpandHorizontally(false),
        new QuText(xstring("who_other_q")),
        new QuTextEdit(fieldRef("who_other_q"), false),
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
            (new QuSlider(fieldRef("slider_1"), VAS_MIN_INT, VAS_MAX_INT, 1))
                                        ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM),
            new QuText(xstring("q2_title")) ,
            new QuText(xstring("q2_subtitle")),
            (new QuSlider(fieldRef("slider_2"), VAS_MIN_INT, VAS_MAX_INT, 1))
                            ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM),
            new QuText(xstring("q3_title")),
            new QuText(xstring("q3_subtitle")),
            (new QuSlider(fieldRef("slider_3"), VAS_MIN_INT, VAS_MAX_INT, 1))
                            ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM),
            new QuText(xstring("q4_title")),
            new QuText(xstring("q4_subtitle")),
            (new QuSlider(fieldRef("slider_4"), VAS_MIN_INT, VAS_MAX_INT, 1))
                            ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM),
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

    bool required = valueInt("who_q") == COMPLETED_BY_OTHER;
    fieldRef("who_other_q")->setMandatory(required);

    connect(fieldRef("who_q").data(), &FieldRef::valueChanged,
            this, &Ors::updateMandatory);

    page->setTitle(longname());

    QuPagePtr tpage(new QuPage{
        (new QuVerticalContainer{
            new QuText("a"),
            new QuText("b"),
        })->setWidgetAlignment(centre)});

    m_questionnaire = new Questionnaire(m_app, {tpage, page});

    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

void Ors::updateMandatory() {
   const bool required = valueInt("who_q")
           == COMPLETED_BY_OTHER;
    fieldRef("who_other_q")->setMandatory(required);
    if (!required) {
        fieldRef("who_other_q")->setValue("");
    }
}
