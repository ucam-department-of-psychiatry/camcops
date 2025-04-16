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

#include "empsa.h"

#include "common/uiconst.h"
#include "lib/convert.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::anyNull;
using mathfunc::meanOrNull;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int LAST_Q = 12;
const int MIN_SCORE = 1;
const int MAX_SCORE = 10;

const QString Q_PREFIX("q");
const QString ABILITY_SUFFIX("_ability");
const QString MOTIVATION_SUFFIX("_motivation");
const QString COMMENTS_SUFFIX("_comments");
const QString NOTE_SUFFIX("_note");

const QString Empsa::EMPSA_TABLENAME("empsa");

void initializeEmpsa(TaskFactory& factory)
{
    static TaskRegistrar<Empsa> registered(factory);
}

QStringList Empsa::abilityFieldNames() const
{
    return strseq(Q_PREFIX, FIRST_Q, LAST_Q, ABILITY_SUFFIX);
}

QStringList Empsa::motivationFieldNames() const
{
    return strseq(Q_PREFIX, FIRST_Q, LAST_Q, MOTIVATION_SUFFIX);
}

QStringList Empsa::commentsFieldNames() const
{
    return strseq(Q_PREFIX, FIRST_Q, LAST_Q, COMMENTS_SUFFIX);
}


Empsa::Empsa(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, EMPSA_TABLENAME, false, false, false)
// ... anon, clin, resp
{
    addFields(abilityFieldNames(), QMetaType::fromType<int>());
    addFields(motivationFieldNames(), QMetaType::fromType<int>());
    addFields(commentsFieldNames(), QMetaType::fromType<QString>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Empsa::shortname() const
{
    return "EMPSA";
}

QString Empsa::longname() const
{
    return tr("Eating & Meal Preparation Skills Assessment");
}

QString Empsa::description() const
{
    return tr(
        "The purpose of this questionnaire is to help people with eating "
        "disorders to measure how able and motivated they are to perform "
        "twelve tasks related to preparing and eating normal portion-sized "
        "cooked meals with dessert. This will highlight what they need to "
        "work on in treatment and measure if treatment has been effective."
    );
}

// ============================================================================
// Instance info
// ============================================================================


bool Empsa::isComplete() const
{
    if (anyNull(values(abilityFieldNames()))) {
        return false;
    }

    if (anyNull(values(motivationFieldNames()))) {
        return false;
    }

    return true;
}

QStringList Empsa::detail() const
{
    QStringList lines = completenessInfo();

    auto html = QString("<table>");
    html.append("<tr>");
    html.append("<th></th>");
    html.append("<th></th>");
    html.append(QString("<th>%1</th>").arg(xstring("ability")));
    html.append(QString("<th>%1</th>").arg(xstring("motivation")));
    html.append("</tr>");

    for (int q = FIRST_Q; q <= LAST_Q; ++q) {
        const QString q_str = QString("%1%2").arg(Q_PREFIX).arg(q);
        const QString ability_field_name = q_str + ABILITY_SUFFIX;
        const QString motivation_field_name = q_str + MOTIVATION_SUFFIX;

        html.append("<tr>");
        html.append(QString("<td>%1</td>").arg(q));
        html.append(QString("<td>%1</td>").arg(xstring(q_str)));
        html.append(QString("<td>%1</td>").arg(valueInt(ability_field_name)));
        html.append(QString("<td>%1</td>").arg(valueInt(motivation_field_name))
        );
        html.append("</tr>");
    }
    html.append("</table>");

    lines.append(html);
    lines.append("");
    lines += summary();

    return lines;
}

QStringList Empsa::summary() const
{
    auto rangeScore = [](const QString& description,
                         const QVariant score,
                         const int min,
                         const int max) {
        return QString("%1: <b>%2</b> [%3–%4].")
            .arg(
                description,
                convert::prettyValue(score, 2),
                QString::number(min),
                QString::number(max)
            );
    };

    return QStringList{
        rangeScore(
            xstring("ability"), abilitySubscale(), MIN_SCORE, MAX_SCORE
        ),
        rangeScore(
            xstring("motivation"), motivationSubscale(), MIN_SCORE, MAX_SCORE
        ),

    };
}

QVariant Empsa::abilitySubscale() const
{
    return meanOrNull(values(abilityFieldNames()));
}

QVariant Empsa::motivationSubscale() const
{
    return meanOrNull(values(motivationFieldNames()));
}

OpenableWidget* Empsa::editor(const bool read_only)
{
    auto subtitle = new QuText(xstring("subtitle"));
    auto instructions_1 = new QuText(xstring("instructions_1"));
    auto instructions_2 = new QuText(xstring("instructions_2"));

    auto instructions_grid = new QuGridContainer();
    instructions_grid->setStyleSheet(
        "background-color: #fefec2; padding: 10px;"
    );

    int row = 0;
    instructions_grid->addCell(QuGridCell(
        (new QuText(xstring("instructions_3")))
            ->setBold()
            ->setTextAndWidgetAlignment(Qt::AlignHCenter),
        row,
        0,
        1,
        2,
        Qt::AlignHCenter
    ));

    row++;

    instructions_grid->addCell(QuGridCell(
        (new QuText(xstring("zero")))
            ->setBold()
            ->setTextAndWidgetAlignment(Qt::AlignLeft),
        row,
        0,
        1,
        1,
        Qt::AlignLeft
    ));
    instructions_grid->addCell(QuGridCell(
        (new QuText(xstring("ten")))
            ->setBold()
            ->setTextAndWidgetAlignment(Qt::AlignRight),
        row,
        1,
        1,
        1,
        Qt::AlignRight
    ));

    auto grid = new QuGridContainer();
    grid->setColumnStretch(0, 1);
    grid->setColumnStretch(1, 9);
    grid->setColumnStretch(2, 2);
    grid->setColumnStretch(3, 2);
    grid->setColumnStretch(4, 9);

    row = 0;

    grid->addCell(QuGridCell(new QuText(""), row, 0));
    grid->addCell(QuGridCell((new QuText(xstring("task")))->setBold(), row, 1)
    );
    grid->addCell(
        QuGridCell((new QuText(xstring("ability")))->setBold(), row, 2)
    );
    grid->addCell(
        QuGridCell((new QuText(xstring("motivation")))->setBold(), row, 3)
    );
    grid->addCell(
        QuGridCell((new QuText(xstring("comments")))->setBold(), row, 4)
    );

    row++;

    for (int q = FIRST_Q; q <= LAST_Q; ++q) {
        const QString q_str = QString("%1%2").arg(Q_PREFIX).arg(q);
        const QString ability_field_name = q_str + ABILITY_SUFFIX;
        const QString motivation_field_name = q_str + MOTIVATION_SUFFIX;
        const QString comments_field_name = q_str + COMMENTS_SUFFIX;
        const QString note_name = q_str + NOTE_SUFFIX;
        const QString label
            = QString("%1 %2").arg(xstring(q_str)).arg(xstring(note_name));

        grid->addCell(QuGridCell(new QuText(QString::number(q)), row, 0));
        grid->addCell(QuGridCell(new QuText(label), row, 1));

        auto ability_edit = new QuLineEditInteger(
            fieldRef(ability_field_name), MIN_SCORE, MAX_SCORE
        );
        //: Range for integer input
        ability_edit->setHint(
            QString(tr("%1 to %2")).arg(MIN_SCORE).arg(MAX_SCORE)
        );
        grid->addCell(QuGridCell(ability_edit, row, 2));

        auto motivation_edit = new QuLineEditInteger(
            fieldRef(motivation_field_name), MIN_SCORE, MAX_SCORE
        );
        motivation_edit->setHint(
            QString(tr("%1 to %2")).arg(MIN_SCORE).arg(MAX_SCORE)
        );
        grid->addCell(QuGridCell(motivation_edit, row, 3));

        grid->addCell(QuGridCell(
            new QuLineEdit(fieldRef(comments_field_name, false)), row, 4
        ));

        row++;
    }


    QVector<QuElement*> elements{
        subtitle,
        new QuSpacer(QSize(uiconst::MEDIUMSPACE, uiconst::MEDIUMSPACE)),
        instructions_1,
        new QuSpacer(QSize(uiconst::MEDIUMSPACE, uiconst::MEDIUMSPACE)),
        instructions_2,
        new QuSpacer(QSize(uiconst::MEDIUMSPACE, uiconst::MEDIUMSPACE)),
        instructions_grid,
        new QuSpacer(QSize(uiconst::MEDIUMSPACE, uiconst::MEDIUMSPACE)),
        grid,
    };

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title")));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);

    return questionnaire;
}
