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

#include "ocir.h"

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
using mathfunc::meanOrNull;
using mathfunc::sumOrNull;
using stringfunc::strnumlist;
using stringfunc::strseq;


const int FIRST_Q = 1;
const int LAST_Q = 18;
const int FIRST_OPTION = 0;
const int LAST_OPTION = 4;
const int MIN_MEAN = 0;
const int MAX_MEAN = 4;
const int MAX_SCORE = LAST_Q * LAST_OPTION;

const QVector<int> WASHING_QUESTIONS = {5, 11, 17};
const QVector<int> CHECKING_QUESTIONS = {6, 12, 18};
const QVector<int> ORDERING_QUESTIONS = {1, 7, 13};
const QVector<int> OBSESSING_QUESTIONS = {3, 9, 15};
const QVector<int> HOARDING_QUESTIONS = {2, 8, 14};
const QVector<int> NEUTRALISING_QUESTIONS = {4, 10, 16};

const QString Q_PREFIX("q");
const QString Ocir::OCIR_TABLENAME("ocir");

void initializeOcir(TaskFactory& factory)
{
    static TaskRegistrar<Ocir> registered(factory);
}

Ocir::Ocir(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, OCIR_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(Q_PREFIX, FIRST_Q, LAST_Q), QMetaType::fromType<int>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Ocir::shortname() const
{
    return "OCI-R";
}

QString Ocir::longname() const
{
    return tr("Obsessive-Compulsive Inventory (OCI)");
}

QString Ocir::description() const
{
    return tr(
        "An 18-item self-report measure to assess symptoms of "
        "obsessive–compulsive disorder (OCD)."
    );
}

QStringList Ocir::fieldNames() const
{
    return strseq(Q_PREFIX, FIRST_Q, LAST_Q);
}

// ============================================================================
// Instance info
// ============================================================================


bool Ocir::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}

QVector<int> Ocir::allQuestions() const
{
    QVector<int> all_questions(LAST_Q);
    std::iota(all_questions.begin(), all_questions.end(), FIRST_Q);

    return all_questions;
}

QVariant Ocir::score() const
{
    return questionsScore(allQuestions());
}

QVariant Ocir::mean() const
{
    return questionsMean(allQuestions());
}

QVariant Ocir::washingMean() const
{
    return questionsMean(WASHING_QUESTIONS);
}

QVariant Ocir::checkingMean() const
{
    return questionsMean(CHECKING_QUESTIONS);
}

QVariant Ocir::orderingMean() const
{
    return questionsMean(ORDERING_QUESTIONS);
}

QVariant Ocir::obsessingMean() const
{
    return questionsMean(OBSESSING_QUESTIONS);
}

QVariant Ocir::hoardingMean() const
{
    return questionsMean(HOARDING_QUESTIONS);
}

QVariant Ocir::neutralisingMean() const
{
    return questionsMean(NEUTRALISING_QUESTIONS);
}

QVariant Ocir::questionsMean(const QVector<int> qnums) const
{
    return meanOrNull(answers(qnums));
}

QVariant Ocir::questionsScore(const QVector<int> qnums) const
{
    return sumOrNull(answers(qnums));
}

QVector<QVariant> Ocir::answers(const QVector<int> qnums) const
{
    return values(strnumlist(Q_PREFIX, qnums));
}

QStringList Ocir::summary() const
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
        rangeScore(xstring("washing_mean"), washingMean(), MIN_MEAN, MAX_MEAN),
        rangeScore(
            xstring("checking_mean"), checkingMean(), MIN_MEAN, MAX_MEAN
        ),
        rangeScore(
            xstring("ordering_mean"), orderingMean(), MIN_MEAN, MAX_MEAN
        ),
        rangeScore(
            xstring("obsessing_mean"), obsessingMean(), MIN_MEAN, MAX_MEAN
        ),
        rangeScore(
            xstring("hoarding_mean"), hoardingMean(), MIN_MEAN, MAX_MEAN
        ),
        rangeScore(
            xstring("neutralising_mean"),
            neutralisingMean(),
            MIN_MEAN,
            MAX_MEAN
        ),
        rangeScore(xstring("mean"), mean(), MIN_MEAN, MAX_MEAN),
        rangeScore(xstring("total"), score(), 0, MAX_SCORE),
    };
}

QStringList Ocir::detail() const
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

OpenableWidget* Ocir::editor(const bool read_only)
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

QSharedPointer<NameValueOptions> Ocir::buildOptions() const
{
    QSharedPointer<NameValueOptions> options
        = QSharedPointer<NameValueOptions>(new NameValueOptions());

    for (int i = FIRST_OPTION; i <= LAST_OPTION; ++i) {
        auto name = QString("option_%1").arg(i);

        options->append({xstring(name), i});
    }

    return options;
}

QuMcqGrid* Ocir::buildGrid(
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
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
