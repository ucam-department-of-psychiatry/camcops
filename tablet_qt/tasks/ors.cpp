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

const int COMPLETED_BY_SELF = 0;
const int COMPLETED_BY_OTHER = 1;

const int VAS_MIN_INT = 0;
const int VAS_MAX_INT = 0;
const int VAS_ABSOLUTE_CM = 10;

void initializeOrs(TaskFactory& factory)
{
    static TaskRegistrar<Ors> registered(factory);
}

Ors::Ors(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, ORS_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField("session_number", QVariant::Int);
    addField("date", QVariant::Date);
    addField("filled_out_by", QVariant::Date);
    addField("filled_out_by_other", QVariant::Date);

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
    m_completed_by = NameValueOptions{
       { xstring("completed_by_self"), COMPLETED_BY_SELF },
       { xstring("completed_by_other"), COMPLETED_BY_OTHER },
     };

    QuPagePtr page(new QuPage{
        new QuHorizontalLine(),
        new QuHorizontalContainer{
            new QuText(xstring("session")),
            new QuLineEditInteger(fieldRef("session_number"), false),
            new QuText(xstring("date")),
            (new QuDateTime(fieldRef("date")))->setMode(QuDateTime::DefaultDate)
                                              ->setOfferNowButton(true),
        },
        (new QuMcq(fieldRef("completed_by"), m_completed_by))
                                        ->setHorizontal(true)
                                        ->setAsTextButton(true),
        new QuTextEdit(fieldRef("completed_by_other"), false),
        new QuHorizontalLine(),
        new QuSpacer(),
        new QuHorizontalLine(),
        new QuText(xstring("instructions_to_subject")),
        new QuHorizontalLine(),
        new QuSpacer(),
        (new QuText(xstring("q1_title")))->setBold(),
        new QuText(xstring("q1_subtitle")),
        (new QuSlider(fieldRef("slider_1"), VAS_MIN_INT, VAS_MAX_INT, 1))
                        ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM),
        (new QuText(xstring("q2_title")))->setBold(),
        new QuText(xstring("q2_subtitle")),
        (new QuSlider(fieldRef("slider_2"), VAS_MIN_INT, VAS_MAX_INT, 1))
                        ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM),
        (new QuText(xstring("q3_title")))->setBold(),
        new QuText(xstring("q3_subtitle")),
        (new QuSlider(fieldRef("slider_3"), VAS_MIN_INT, VAS_MAX_INT, 1))
                        ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM),
        (new QuText(xstring("q4_title")))->setBold(),
        new QuText(xstring("q4_subtitle")),
        (new QuSlider(fieldRef("slider_4"), VAS_MIN_INT, VAS_MAX_INT, 1))
                        ->setAbsoluteLengthCm(VAS_ABSOLUTE_CM),
        new QuSpacer(),
        new QuHorizontalLine(),
        new QuText(xstring("copyright")),
        new QuText(xstring("licensing"))
    });

    bool required = valueInt("completed_by") == COMPLETED_BY_OTHER;
    fieldRef("completed_by_other")->setMandatory(required);

    connect(fieldRef("completed_by").data(), &FieldRef::valueChanged,
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
   const bool required = valueInt("completed_by")
           == COMPLETED_BY_OTHER;
    fieldRef("completed_by_other")->setMandatory(required);
    if (!required) {
        fieldRef("completed_by_other")->setValue("");
    }
}
