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

#include "gbogres.h"
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

const QString GboGReS::GBOGRES_TABLENAME("gbogres");

const int GOAL_CHILD = 1;
const int GOAL_PARENT_CARER = 2;
const int GOAL_OTHER = 3;

const QString GOAL_CHILD_STR = "Child/young person";
const QString GOAL_PARENT_CARER_STR = "Parent/carer";

const QString FN_DATE("date");  // NB SQL keyword too; doesn't matter
const QString FN_GOAL_1_DESC("goal_1_desc");
const QString FN_GOAL_2_DESC("goal_2_desc");
const QString FN_GOAL_3_DESC("goal_3_desc");
const QString FN_GOAL_OTHER("goal_other");
const QString FN_COMPLETED_BY("completed_by");
const QString FN_COMPLETED_BY_OTHER("completed_by_other");

void initializeGboGReS(TaskFactory& factory)
{
    static TaskRegistrar<GboGReS> registered(factory);
}

GboGReS::GboGReS(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, GBOGRES_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_DATE, QVariant::Date);
    addField(FN_GOAL_1_DESC, QVariant::String);
    addField(FN_GOAL_2_DESC, QVariant::String);
    addField(FN_GOAL_3_DESC, QVariant::String);
    addField(FN_GOAL_OTHER, QVariant::String);
    addField(FN_COMPLETED_BY, QVariant::Int);
    addField(FN_COMPLETED_BY_OTHER, QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.

    // Extra initialization:
    if (load_pk == dbconst::NONEXISTENT_PK) {
        setValue(FN_DATE, datetime::nowDate(), false);
    }
}

// ============================================================================
// Class info
// ============================================================================

QString GboGReS::shortname() const
{
    return "GBO-GReS";
}


QString GboGReS::longname() const
{
    return tr("Goal Based Outcomes – Goal Record Sheet");
}


QString GboGReS::menusubtitle() const
{
    return tr("Goal progress tracking measurement");
}


// ============================================================================
// Instance info
// ============================================================================

bool GboGReS::isComplete() const
{

    bool required = noneNullOrEmpty(values({
                                               FN_DATE,
                                               FN_GOAL_1_DESC,
                                               FN_COMPLETED_BY,
                                           }));

    if (value(FN_COMPLETED_BY) == GOAL_OTHER
            && value(FN_COMPLETED_BY_OTHER).isNull()) {
        return false;
    }

    return required;
}

QStringList GboGReS::summary() const
{
    return QStringList{
        QString("<b>Goals set</b>: %1 %2").arg(goalNumber(), extraGoals()),
    };
}

QStringList GboGReS::detail() const
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
    if (!valueIsNullOrEmpty(FN_GOAL_OTHER)) {
        detail.push_back(QString("<b>Extra goals</b>: %1")
                         .arg(value(FN_GOAL_OTHER).toString()));
    }

    detail.push_back(QString("<b>Completed by</b>: %1").arg(completedBy()));

    return detail;
}

OpenableWidget* GboGReS::editor(const bool read_only)
{
    const NameValueOptions completed_by_options = NameValueOptions{
        { xstring("completed_by_o1"), GOAL_CHILD },
        { xstring("completed_by_o2"), GOAL_PARENT_CARER },
        { xstring("completed_by_o3"), GOAL_OTHER }
    };

    QuPagePtr page(new QuPage{
                            (new QuHorizontalContainer{
                                new QuHeading(xstring("date")),
                               (new QuDateTime(fieldRef(FN_DATE))
                                   )->setMode(QuDateTime::DefaultDate)
                                    ->setOfferNowButton(true),
                            }),
                            (new QuText(xstring("stem")))->setBold(true),
                            new QuSpacer(),
                            new QuHeading(xstring("goal_1")),
                            new QuTextEdit(fieldRef(FN_GOAL_1_DESC)),
                            new QuHeading(xstring("goal_2")),
                            new QuTextEdit(fieldRef(FN_GOAL_2_DESC, false)),
                            new QuHeading(xstring("goal_3")),
                            new QuTextEdit(fieldRef(FN_GOAL_3_DESC, false)),
                            new QuText(xstring("goal_other")),
                            new QuTextEdit(fieldRef(FN_GOAL_OTHER, false)),
                            (new QuText(xstring("completed_by")))->setBold(true),
                            (new QuMcq(fieldRef(FN_COMPLETED_BY), completed_by_options))
                                            ->setHorizontal(true)
                                            ->setAsTextButton(true),
                            new QuTextEdit(fieldRef(FN_COMPLETED_BY_OTHER), false),
                            new QuSpacer(),
                            new QuHorizontalLine(),
                            new QuSpacer(),
                            (new QuText(xstring("copyright")))->setItalic()
                        });

    bool required = valueInt(FN_COMPLETED_BY) == GOAL_OTHER;
    fieldRef(FN_COMPLETED_BY_OTHER)->setMandatory(required);

    connect(fieldRef(FN_COMPLETED_BY).data(), &FieldRef::valueChanged,
            this, &GboGReS::updateMandatory);

    page->setTitle(longname());

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setReadOnly(read_only);
    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

void GboGReS::updateMandatory()
{
   const bool required = valueInt(FN_COMPLETED_BY)
           == GOAL_OTHER;
    fieldRef(FN_COMPLETED_BY_OTHER)->setMandatory(required);
    if (!required) {
        fieldRef(FN_COMPLETED_BY_OTHER)->setValue("");
    }
}

QString GboGReS::goalNumber() const
{
    int goal_n = 0;

    for (auto field : {FN_GOAL_1_DESC, FN_GOAL_2_DESC, FN_GOAL_3_DESC}) {
        if (!valueIsNullOrEmpty(field)) {
            ++goal_n;
        }
    }

    return QString::number(goal_n);
}

QString GboGReS::extraGoals() const
{
    QString extra = "";
    if (!valueIsNullOrEmpty(FN_GOAL_OTHER)) {
        extra = "<i>(with additional goals set)</i>";
    }
    return extra;
}

QString GboGReS::completedBy() const
{
    QString completed_by;

    switch (value(FN_COMPLETED_BY).toInt()) {
        case GOAL_CHILD:
            completed_by = GOAL_CHILD_STR;
            break;
        case GOAL_PARENT_CARER:
            completed_by = GOAL_PARENT_CARER_STR;
            break;
        default:
            completed_by = value(FN_COMPLETED_BY_OTHER).toString();
    }

    return completed_by;
}
