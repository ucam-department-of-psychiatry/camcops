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

#include "aq.h"

#include "db/databaseobject.h"
#include "lib/convert.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int LAST_Q = 50;
const int FIRST_OPTION = 0;
const int LAST_OPTION = 3;
const int MIN_SCORE = 0;
const int MAX_SCORE = 50;
const int MIN_AREA_SCORE = 0;
const int MAX_AREA_SCORE = 10;

const QVector<int> AGREE_OPTIONS = {0, 1};  // definitely agree, slightly agree
const QVector<int> DISAGREE_OPTIONS = {2, 3};
// ... slightly disagree, definitely disagree
const QVector<int> AGREE_SCORING_QUESTIONS = {
    2,  4,  5,  6,  7,  9,  12, 13, 16, 18, 19, 20,
    21, 22, 23, 26, 33, 35, 39, 41, 42, 43, 45, 46,
};
// ... see aq.py re error re Q1 in published Baron-Cohen et al. (2001).

const QVector<int> SOCIAL_SKILL_QUESTIONS
    = {1, 11, 13, 15, 22, 36, 44, 45, 47, 48};
const QVector<int> ATTENTION_SWITCHING_QUESTIONS
    = {2, 4, 10, 16, 25, 32, 34, 37, 43, 46};
const QVector<int> ATTENTION_TO_DETAIL_QUESTIONS
    = {5, 6, 9, 12, 19, 23, 28, 29, 30, 49};
const QVector<int> COMMUNICATION_QUESTIONS
    = {7, 17, 18, 26, 27, 31, 33, 35, 38, 39};
const QVector<int> IMAGINATION_QUESTIONS
    = {3, 8, 14, 20, 21, 24, 40, 41, 42, 50};

const QString Q_PREFIX("q");
const QString Aq::AQ_TABLENAME("aq");

void initializeAq(TaskFactory& factory)
{
    static TaskRegistrar<Aq> registered(factory);
}

Aq::Aq(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, AQ_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(Q_PREFIX, FIRST_Q, LAST_Q), QMetaType::fromType<int>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Aq::shortname() const
{
    return "AQ";
}

QString Aq::longname() const
{
    return tr("Adult Autism Spectrum Quotient");
}

QString Aq::description() const
{
    return tr(
        "A 50-item self-report measure used to assess traits of autism in "
        "adults and adolescents aged 16 years and over."
    );
}

QStringList Aq::fieldNames() const
{
    return strseq(Q_PREFIX, FIRST_Q, LAST_Q);
}

// ============================================================================
// Instance info
// ============================================================================


bool Aq::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}

QVariant Aq::score() const
{
    QVector<int> all_questions(LAST_Q);
    std::iota(all_questions.begin(), all_questions.end(), FIRST_Q);

    return questionsScore(all_questions);
}

QVariant Aq::socialSkillScore() const
{
    return questionsScore(SOCIAL_SKILL_QUESTIONS);
}

QVariant Aq::attentionSwitchingScore() const
{
    return questionsScore(ATTENTION_SWITCHING_QUESTIONS);
}

QVariant Aq::attentionToDetailScore() const
{
    return questionsScore(ATTENTION_TO_DETAIL_QUESTIONS);
}

QVariant Aq::communicationScore() const
{
    return questionsScore(COMMUNICATION_QUESTIONS);
}

QVariant Aq::imaginationScore() const
{
    return questionsScore(IMAGINATION_QUESTIONS);
}

QVariant Aq::questionsScore(const QVector<int> qnums) const
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

QVariant Aq::questionScore(const int qnum) const
{
    const QString fieldname = Q_PREFIX + QString::number(qnum);
    const QVariant v = value(fieldname);
    if (v.isNull()) {
        return v;
    }
    const int answer = v.toInt();

    if (AGREE_SCORING_QUESTIONS.contains(qnum)) {
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

QStringList Aq::summary() const
{
    auto rangeScore = [](const QString& description,
                         const QVariant score,
                         const int min,
                         const int max) {
        return QString("%1: <b>%2</b> [%3–%4].")
            .arg(
                description,
                convert::prettyValue(score),
                QString::number(min),
                QString::number(max)
            );
    };

    return QStringList{
        rangeScore(
            xstring("social_skill_score"),
            socialSkillScore(),
            MIN_AREA_SCORE,
            MAX_AREA_SCORE
        ),
        rangeScore(
            xstring("attention_switching_score"),
            attentionSwitchingScore(),
            MIN_AREA_SCORE,
            MAX_AREA_SCORE
        ),
        rangeScore(
            xstring("attention_to_detail_score"),
            attentionToDetailScore(),
            MIN_AREA_SCORE,
            MAX_AREA_SCORE
        ),
        rangeScore(
            xstring("communication_score"),
            communicationScore(),
            MIN_AREA_SCORE,
            MAX_AREA_SCORE
        ),
        rangeScore(
            xstring("imagination_score"),
            imaginationScore(),
            MIN_AREA_SCORE,
            MAX_AREA_SCORE
        ),
        rangeScore(xstring("score"), score(), MIN_SCORE, MAX_SCORE),
    };
}

QStringList Aq::detail() const
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

OpenableWidget* Aq::editor(const bool read_only)
{
    auto options = buildOptions();

    const int min_width_px = 100;
    const QVector<int> min_option_widths_px = {50, 50, 50, 50};

    auto instructions = new QuHeading(xstring("instructions"));
    auto grid = buildGrid(FIRST_Q, LAST_Q, options);
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

QSharedPointer<NameValueOptions> Aq::buildOptions() const
{
    QSharedPointer<NameValueOptions> options
        = QSharedPointer<NameValueOptions>(new NameValueOptions());

    for (int i = FIRST_OPTION; i <= LAST_OPTION; ++i) {
        auto name = QString("option_%1").arg(i);

        options->append({xstring(name), i});
    }

    return options;
}

QuMcqGrid* Aq::buildGrid(
    int first_qnum, int last_qnum, QSharedPointer<NameValueOptions> options
)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
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
    QVector<McqGridSubtitle> subtitles{
        {5, ""},
        {10, ""},
        {15, ""},
        {20, ""},
        {25, ""},
        {30, ""},
        {35, ""},
        {40, ""},
        {45, ""},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
