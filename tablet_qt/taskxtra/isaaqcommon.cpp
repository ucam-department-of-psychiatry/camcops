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

#include "isaaqcommon.h"

#include "common/textconst.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int MIN_QUESTION_SCORE = 0;
const int MAX_QUESTION_SCORE = 5;

IsaaqCommon::IsaaqCommon(
    CamcopsApp& app, DatabaseManager& db, const QString tableName
) :
    Task(app, db, tableName, false, false, false)  // ... anon, clin, resp
{
}

// ============================================================================
// Instance info
// ============================================================================


bool IsaaqCommon::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}

QStringList IsaaqCommon::summary() const
{
    // There are no scores or scales
    return QStringList{TextConst::noSummarySeeFacsimile()};
}

QStringList IsaaqCommon::detail() const
{
    QStringList lines = completenessInfo();

    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = fieldNames();

    for (int i = 0; i < fieldnames.length(); ++i) {
        const QString& fieldname = fieldnames.at(i);
        lines.append(
            fieldSummary(fieldname, xstring(fieldname), spacer, suffix)
        );
    }

    return lines;
}

OpenableWidget* IsaaqCommon::editor(const bool read_only)
{
    auto elements = buildElements();

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title")));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);

    return questionnaire;
}

QuMcqGrid* IsaaqCommon::buildGrid(
    const QString prefix, int first_qnum, int last_qnum, const QString title
)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = prefix + QString::number(qnum);
        const QString& description = xstring(fieldname);

        q_field_pairs.append(
            QuestionWithOneField(description, fieldRef(fieldname))
        );
    }

    NameValueOptions options;

    for (int i = MIN_QUESTION_SCORE; i <= MAX_QUESTION_SCORE; i++) {
        auto name = QString("freq_option_%1").arg(i);

        options.append({xstring(name), i});
    }

    auto grid = new QuMcqGrid(q_field_pairs, options);
    grid->setTitle(title);
    // Repeat options every five lines
    QVector<McqGridSubtitle> subtitles{
        {5, ""},
        {10, ""},
        {15, ""},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);

    const int min_width_px = 100;
    const QVector<int> min_option_widths_px = {100, 100, 100, 100, 100, 100};

    grid->setMinimumWidthInPixels(min_width_px, min_option_widths_px);
    grid->setQuestionsBold(false);

    return grid;
}
