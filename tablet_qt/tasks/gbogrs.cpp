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

#include "gbogrs.h"
#include "maths/mathfunc.h"
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

const QString GboGrs::GBOGRS_TABLENAME("gbogrs");

const int GOAL_CHILD = 1;
const int GOAL_PARENT_CARER = 2;
const int GOAL_OTHER = 3;

const QString GOAL_CHILD_STR = "Child/young person";
const QString GOAL_PARENT_CARER_STR = "Parent/carer";

void initializeGboGrs(TaskFactory& factory)
{
    static TaskRegistrar<GboGrs> registered(factory);
}


GboGrs::GboGrs(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, GBOGRS_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField("date_only", QVariant::Date);
    addField("goal_1_desc", QVariant::String);
    addField("goal_2_desc", QVariant::String);
    addField("goal_3_desc", QVariant::String);
    addField("goal_other", QVariant::String);
    addField("completed_by", QVariant::Int);
    addField("completed_by_other", QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString GboGrs::shortname() const
{
    return "GBO-GRS";
}


QString GboGrs::longname() const
{
    return tr("Goal Based Outcomes - Goal Record Sheet");
}


QString GboGrs::menusubtitle() const
{
    return tr("Goal progress tracking measurement");
}


// ============================================================================
// Instance info
// ============================================================================

bool GboGrs::isComplete() const
{
    bool required = noneNullOrEmpty(values(QStringList{"date_only",
                                                       "goal_1_desc",
                                                        "completed_by"}));

    bool other = ((value("completed_by") == GOAL_OTHER &&
                   !value("completed_by_other").isNull()));

    return required && other;
}

QStringList GboGrs::summary() const
{
    return QStringList{
        QString("<b>Goals set</b>: %1 %2").arg(goalNumber(), extraGoals()),
    };
}

QStringList GboGrs::detail() const
{
    QStringList detail;

    detail.push_back(QString("<b>Goals set</b>: %1 %2").arg(goalNumber(),
                                                            extraGoals()));
    int i = 0;
    for (auto field : strseq("goal_", 1, 3, "_desc")) {
        ++i;
        if (!valueIsNullOrEmpty(field)) {
            detail.push_back(QString("<b>Goal %1</b>: %2").arg(QString::number(i),
                                                       value(field).toString()));
        }
    }
    if (!valueIsNullOrEmpty("goal_other")) {
        detail.push_back(QString("<b>Extra goals</b>: %1").arg(value("goal_other").toString()));
    }

    detail.push_back(QString("<b>Completed by</b>: %1").arg(completedBy()));

    return detail;
}

OpenableWidget* GboGrs::editor(const bool read_only)
{
    m_completed_by = NameValueOptions{
        { xstring("completed_by_o1"), GOAL_CHILD },
        { xstring("completed_by_o2"), GOAL_PARENT_CARER },
        { xstring("completed_by_o3"), GOAL_OTHER }
    };

    QuPagePtr page(new QuPage{
                            (new QuText(xstring("stem")))->setBold(true),
                            (new QuHorizontalContainer{
                                new QuHeading(xstring("date")),
                               (new QuDateTime(fieldRef("date_only"))
                                   )->setMode(QuDateTime::DefaultDate)
                                    ->setOfferNowButton(true),
                            }),
                            new QuSpacer(),
                            new QuHeading(xstring("goal_1")),
                            new QuTextEdit(fieldRef("goal_1_desc")),
                            new QuHeading(xstring("goal_2")),
                            new QuTextEdit(fieldRef("goal_2_desc", false)),
                            new QuHeading(xstring("goal_3")),
                            new QuTextEdit(fieldRef("goal_3_desc", false)),
                            new QuText(xstring("goal_other")),
                            new QuTextEdit(fieldRef("goal_other", false)),
                            (new QuText(xstring("completed_by")))->setBold(true),
                            (new QuMcq(fieldRef("completed_by"), m_completed_by))
                                            ->setHorizontal(true)
                                            ->setAsTextButton(true),
                            new QuText(xstring("license")),
                            new QuTextEdit(fieldRef("completed_by_other"), false),
                        });

    bool required = valueInt("completed_by") == GOAL_OTHER;
    fieldRef("completed_by_other")->setMandatory(required);

    connect(fieldRef("completed_by").data(), &FieldRef::valueChanged,
            this, &GboGrs::updateMandatory);

    page->setTitle(longname());

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setReadOnly(read_only);
    return m_questionnaire;
}

void GboGrs::updateMandatory() {
   const bool required = valueInt("completed_by")
           == GOAL_OTHER;
    fieldRef("completed_by_other")->setMandatory(required);
    if (!required) {
        fieldRef("completed_by_other")->setValue("");
    }
}

// ============================================================================
// Task-specific calculations
// ============================================================================

QString GboGrs::goalNumber() const {
    int goal_n = 0;
    if (!valueIsNullOrEmpty("goal_1_desc")) {
        ++goal_n;
    }
    if (!valueIsNullOrEmpty("goal_2_desc")) {
        ++goal_n;
    }
    if (!valueIsNullOrEmpty("goal_3_desc")) {
        ++goal_n;
    }
    return QString::number(goal_n);
}

QString GboGrs::extraGoals() const {
    QString extra = "";
    if (!valueIsNullOrEmpty("goal_other")) {
        extra = "<i>(with additional goals set)</i>";
    }
    return extra;
}

QString GboGrs::completedBy() const {
    QString completed_by;

    switch (value("completed_by").toInt()) {
        case GOAL_CHILD:
            completed_by = GOAL_CHILD_STR;
            break;
        case GOAL_PARENT_CARER:
            completed_by = GOAL_PARENT_CARER_STR;
            break;
        default:
            completed_by = value("completed_by_other").toString();
    }

    return completed_by;
}
