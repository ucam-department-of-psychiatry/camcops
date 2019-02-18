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

#include "gbogprs.h"
#include "maths/mathfunc.h"
#include "lib/datetime.h"
#include "lib/stringfunc.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quflowcontainer.h"
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
#include "questionnairelib/questionnairefunc.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"

using mathfunc::noneNullOrEmpty;
using stringfunc::strseq;

const QString GboGPrS::GBOGPRS_TABLENAME("gbogprs");

const int MIN_SESSION = 1;
const int MAX_SESSION = 1000;

const int COMPLETED_BY_PATIENT = 1;
const int COMPLETED_BY_PARENT_CARER = 2;
const int COMPLETED_BY_OTHER = 3;

const QString FN_DATE("q_date");
const QString FN_SESSION("q_session");
const QString FN_GOAL("q_goal");
const QString FN_PROGRESS("q_progress");
const QString FN_WHO("q_who");
const QString FN_WHO_OTHER("q_who_other");

void initializeGboGPrS(TaskFactory& factory)
{

    static TaskRegistrar<GboGPrS> registered(factory);
}

GboGPrS::GboGPrS(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, GBOGPRS_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_DATE, QVariant::Date);
    addField(FN_SESSION, QVariant::Int);
    addField(FN_GOAL, QVariant::String);
    addField(FN_PROGRESS, QVariant::Int);
    addField(FN_WHO, QVariant::Int);
    addField(FN_WHO_OTHER, QVariant::String);
    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.

    if (load_pk == dbconst::NONEXISTENT_PK) {
        setValue(FN_DATE, datetime::nowDate(), false);
    }
}

// ============================================================================
// Class info
// ============================================================================

QString GboGPrS::shortname() const
{
    return "GBO-GPrS";
}


QString GboGPrS::longname() const
{
    return tr("Goal-Based Outcomes – Goal Progress Sheet");
}


QString GboGPrS::menusubtitle() const
{
    return tr("Goal progress tracking measurement");
}


// ============================================================================
// Instance info
// ============================================================================

bool GboGPrS::isComplete() const
{
    bool required = noneNullOrEmpty(values({
                                               FN_DATE,
                                               FN_SESSION,
                                               FN_GOAL,
                                               FN_PROGRESS,
                                               FN_WHO,
                                           }));

    if (value(FN_WHO) == COMPLETED_BY_OTHER && value(FN_WHO_OTHER).isNull()) {
        return false;
    }

    return required;
}

QStringList GboGPrS::summary() const
{
    return QStringList{};
}

QStringList GboGPrS::detail() const
{
    QStringList detail;

    detail.append(summary());

    return detail;
}

OpenableWidget* GboGPrS::editor(const bool read_only)
{
    const NameValueOptions whose_goal_options = NameValueOptions{
        { xstring("whose_goal_o1"), COMPLETED_BY_PATIENT},
        { xstring("whose_goal_o2"), COMPLETED_BY_PARENT_CARER },
        { xstring("whose_goal_o3"), COMPLETED_BY_OTHER },
    };

    const NameValueOptions goal_progress_options = NameValueOptions{
        {"0", 0}, {"1", 1}, {"2", 2}, {"3", 3}, {"4", 4},
        {"5", 5}, {"6", 6}, {"7", 7}, {"8", 8}, {"9", 9}, {"10", 10},
    };

    const int q_width = 34;
    const QVector<int> o_widths(11, 6);

    QuPagePtr page(new QuPage{
        new QuVerticalContainer{
            (new QuFlowContainer{
                new QuHeading(xstring("date")),
                (new QuDateTime(fieldRef(FN_DATE)))
                    ->setMode(QuDateTime::DefaultDate)
                    ->setOfferNowButton(true),
            }),
           (new QuFlowContainer{
               new QuHeading(xstring("session")),
               new QuLineEditInteger(fieldRef(FN_SESSION), MIN_SESSION, MAX_SESSION)
           }),
           (new QuFlowContainer{
               new QuHeading(xstring("goal")),
               new QuTextEdit(fieldRef(FN_GOAL)),
           }),
            (new QuMcqGrid(
                {
                    QuestionWithOneField(xstring("progress"), fieldRef(FN_PROGRESS)),
                }, goal_progress_options
            ))->setWidth(q_width, o_widths)->setExpand(true),
            (new QuText(xstring("explanation")))
                            ->setItalic(),
            (new QuMcq(fieldRef(FN_WHO), whose_goal_options))
                ->setHorizontal(true)
                ->setAsTextButton(true),
            new QuTextEdit(fieldRef(FN_WHO_OTHER)),
        }
    });

    connect(fieldRef(FN_WHO).data(), &FieldRef::valueChanged,
            this, &GboGPrS::updateMandatory);

    page->setTitle(longname());

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setReadOnly(read_only);
    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

void GboGPrS::updateMandatory()
{
   const bool required = valueInt(FN_WHO) == COMPLETED_BY_OTHER;
    fieldRef(FN_WHO_OTHER)->setMandatory(required);
    if (!required) {
        fieldRef(FN_WHO_OTHER)->setValue("");
    }
}
