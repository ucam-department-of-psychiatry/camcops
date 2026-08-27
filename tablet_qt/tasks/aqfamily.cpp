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

#include "aqfamily.h"

#include "lib/convert.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qupage.h"

using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_OPTION = 0;
const int LAST_OPTION = 3;
const QVector<int> AGREE_OPTIONS = {0, 1};  // definitely agree, slightly agree
const QVector<int> DISAGREE_OPTIONS = {2, 3};
// ... slightly disagree, definitely disagree
const QString Q_PREFIX("q");


AqFamily::AqFamily(
    CamcopsApp& app,
    DatabaseManager& db,
    const QString& tablename,
    const int last_q,
    const QVector<int> agree_scoring_questions,
    QObject* parent
) :
    Task(app, db, tablename, false, false, false, parent)
// ... anon, clin, resp
{
    m_last_q = last_q;
    m_agree_scoring_questions = agree_scoring_questions;

    // Subclasses should add fields and call load(load_pk).
}

QStringList AqFamily::fieldNames() const
{
    return strseq(Q_PREFIX, m_first_q, m_last_q);
}

// ============================================================================
// Instance info
// ============================================================================


bool AqFamily::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}

QVariant AqFamily::score() const
{
    QVector<int> all_questions(m_last_q);
    std::iota(all_questions.begin(), all_questions.end(), m_first_q);

    return questionsScore(all_questions);
}

QVariant AqFamily::questionsScore(const QVector<int> qnums) const
{
    int total = 0;
    QVariant v;

    for (int qnum : qnums) {
        v = questionScore(qnum);
        if (v.isNull()) {
            return v;
        }
        total += v.toInt();
    }

    return total;
}

QVariant AqFamily::questionScore(const int qnum) const
{
    const QString fieldname = Q_PREFIX + QString::number(qnum);
    const QVariant v = value(fieldname);
    if (v.isNull()) {
        return v;
    }
    const int answer = v.toInt();

    if (m_agree_scoring_questions.contains(qnum)) {
        // Questions where agreement indicates autistic-like traits
        if (AGREE_OPTIONS.contains(answer)) {
            return 1;
        } else if (DISAGREE_OPTIONS.contains(answer)) {
            return 0;
        } else {
            // Shouldn't happen, but for defensiveness:
            return QVariant();
        }
    } else {
        // Questions where disagreement indicates autistic-like traits
        if (AGREE_OPTIONS.contains(answer)) {
            return 0;
        } else if (DISAGREE_OPTIONS.contains(answer)) {
            return 1;
        } else {
            // Shouldn't happen, but for defensiveness:
            return QVariant();
        }
    }
}

QString AqFamily::rangeScore(
    const QString& description,
    const QVariant score,
    const int min,
    const int max
) const
{
    return QString("%1: <b>%2</b> [%3–%4].")
        .arg(
            description,
            convert::prettyValue(score),
            QString::number(min),
            QString::number(max)
        );
}

QStringList AqFamily::detail() const
{
    QStringList lines = completenessInfo();

    const QString altname = "";
    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = fieldNames();

    QSharedPointer<NameValueOptions> options = buildOptions();

    for (int i = 0; i < fieldnames.length(); ++i) {
        const QString& fieldname = fieldnames.at(i);
        lines.append(fieldSummaryNameValueOptions(
            fieldname, *options, altname, spacer, suffix
        ));
    }

    lines.append("");
    lines += summary();

    return lines;
}

OpenableWidget* AqFamily::editor(const bool read_only)
{
    auto options = buildOptions();

    const int min_width_px = 100;
    const QVector<int> min_option_widths_px = {50, 50, 50, 50};

    auto instructions = new QuHeading(xstring("instructions"));
    auto grid = buildGrid(options);
    grid->setMinimumWidthInPixels(min_width_px, min_option_widths_px);

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

QSharedPointer<NameValueOptions> AqFamily::buildOptions() const
{
    QSharedPointer<NameValueOptions> options
        = QSharedPointer<NameValueOptions>(new NameValueOptions());

    for (int i = FIRST_OPTION; i <= LAST_OPTION; ++i) {
        auto name = QString("option_%1").arg(i);

        options->append({xstring(name), i});
    }

    return options;
}

QuMcqGrid* AqFamily::buildGrid(QSharedPointer<NameValueOptions> options)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = m_first_q; qnum <= m_last_q; qnum++) {
        const QString& qnumstr = QString::number(qnum);
        const QString& fieldname = Q_PREFIX + qnumstr;
        const QString& description = qnumstr + ". " + xstring(fieldname);
        // const lvalue references prolong the lifespan of temporary objects;
        // https://pvs-studio.com/en/blog/posts/cpp/1006/

        q_field_pairs.append(
            QuestionWithOneField(description, fieldRef(fieldname))
        );
    }

    auto grid = new QuMcqGrid(q_field_pairs, *options);
    // Repeat options every five lines
    QVector<McqGridSubtitle> subtitles = {};
    for (int s = 5; s < m_last_q; s += 5) {
        subtitles.append({s, ""});
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
