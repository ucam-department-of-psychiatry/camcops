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

#include "cia.h"

#include "common/textconst.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::anyNull;
using mathfunc::sumInt;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int LAST_Q = 16;
const int MIN_QUESTION_SCORE = 0;
const int MAX_QUESTION_SCORE = 3;
const int MIN_GLOBAL_SCORE = 0;
const int MAX_GLOBAL_SCORE = 48;
const int MIN_APPLICABLE = 12;
const QVector<int> OPTIONAL_QUESTIONS{3, 4, 7, 10};

const QString QPREFIX("q");

const QString Cia::CIA_TABLENAME("cia");

void initializeCia(TaskFactory& factory)
{
    static TaskRegistrar<Cia> registered(factory);
}

Cia::Cia(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, CIA_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, LAST_Q), QMetaType::fromType<int>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Cia::shortname() const
{
    return "CIA";
}

QString Cia::longname() const
{
    return tr("Clinical Impairment Assessment questionnaire");
}

QString Cia::description() const
{
    return tr(
        "A 16-item self-report measure of the severity of psychosocial "
        "impairment due to eating disorder features."
    );
}

QStringList Cia::fieldNames() const
{
    return strseq(QPREFIX, FIRST_Q, LAST_Q);
}

QStringList Cia::mandatoryFieldNames() const
{
    QStringList list;
    for (int qnum = FIRST_Q; qnum <= LAST_Q; ++qnum) {
        if (!OPTIONAL_QUESTIONS.contains(qnum)) {
            list.append(strnum(QPREFIX, qnum));
        }
    }
    return list;
}

// ============================================================================
// Instance info
// ============================================================================


bool Cia::isComplete() const
{
    if (anyNull(values(mandatoryFieldNames()))) {
        return false;
    }

    return true;
}

QStringList Cia::summary() const
{
    auto rangeScore = [](const QString& description,
                         const QVariant score,
                         const int min,
                         const int max) {
        if (score.isNull()) {
            return QString("%1: <b>?</b>.").arg(description);
        }

        return QString("%1: <b>%2</b> [%3–%4].")
            .arg(
                description,
                QString::number(score.toDouble(), 'f', 2),
                QString::number(min),
                QString::number(max)
            );
    };

    return QStringList{
        rangeScore(
            TextConst::totalScore(),
            globalScore(),
            MIN_GLOBAL_SCORE,
            MAX_GLOBAL_SCORE
        ),
    };
}

QVariant Cia::globalScore() const
{
    if (!isComplete()) {
        return QVariant();
    }

    int num_applicable = 0;
    int total = 0;

    const QVector<QVariant> responses = values(fieldNames());

    for (int i = 0; i < responses.length(); ++i) {
        const QVariant& value = responses.at(i);

        if (value.isNull()) {
            if (!OPTIONAL_QUESTIONS.contains(i + 1)) {
                return QVariant();
            }
        } else {
            num_applicable++;
            total += value.toInt();
        }
    }

    if (num_applicable < MIN_APPLICABLE) {
        return QVariant();
    }

    const float scale_factor = (float)LAST_Q / num_applicable;

    return scale_factor * total;
}

QStringList Cia::detail() const
{
    QStringList lines = completenessInfo();

    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = fieldNames();

    lines += xstring("grid_title");

    for (int i = 0; i < fieldnames.length(); ++i) {
        const QString& fieldname = fieldnames.at(i);
        lines.append(
            fieldSummary(fieldname, xstring(fieldname), spacer, suffix)
        );
    }

    lines.append("");
    lines += summary();

    return lines;
}

OpenableWidget* Cia::editor(const bool read_only)
{
    NameValueOptions options;

    for (int i = MIN_QUESTION_SCORE; i <= MAX_QUESTION_SCORE; i++) {
        auto name = QString("option_%1").arg(i);

        options.append({xstring(name), i});
    }

    auto instructions = new QuHeading(xstring("instructions"));
    auto grid = buildGrid(FIRST_Q, LAST_Q, options, xstring("grid_title"));

    QVector<QuElement*> elements{
        instructions,
        grid,
    };

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title")));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);

    return questionnaire;
}

QuMcqGrid* Cia::buildGrid(
    int first_qnum,
    int last_qnum,
    const NameValueOptions options,
    const QString title
)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = strnum(QPREFIX, qnum);
        const QString& description = xstring(fieldname);

        FieldRefPtr fieldref = fieldRef(fieldname);

        if (OPTIONAL_QUESTIONS.contains(qnum)) {
            fieldref->setMandatory(false);
        }

        q_field_pairs.append(QuestionWithOneField(description, fieldref));
    }

    auto grid = new QuMcqGrid(q_field_pairs, options);
    grid->setTitle(title);
    // Repeat options every four lines
    QVector<McqGridSubtitle> subtitles{
        {4, title},
        {8, title},
        {12, title},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 2;
    const QVector<int> option_widths = {1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);

    const int min_width_px = 100;
    const QVector<int> min_option_widths_px = {100, 100, 100, 100};
    grid->setMinimumWidthInPixels(min_width_px, min_option_widths_px);

    grid->setQuestionsBold(false);

    return grid;
}
