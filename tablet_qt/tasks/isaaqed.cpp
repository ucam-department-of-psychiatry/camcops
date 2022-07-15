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

#include "isaaqed.h"
#include "common/textconst.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_Q = 11;
const int LAST_Q = 20;
const int MIN_SCORE = 0;
const int MAX_SCORE = 5;
const QString Q_PREFIX("e");


const QString IsaaqEd::ISAAQED_TABLENAME("isaaqed");


void initializeIsaaqEd(TaskFactory& factory)
{
    static TaskRegistrar<IsaaqEd> registered(factory);
}

IsaaqEd::IsaaqEd(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, ISAAQED_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addFields(strseq(Q_PREFIX, FIRST_Q, LAST_Q), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}
// ============================================================================
// Class info
// ============================================================================

QString IsaaqEd::shortname() const
{
    return "ISAAQ-ED";
}


QString IsaaqEd::longname() const
{
    return tr("Internet Severity and Activities Addiction Questionnaire, Eating Disorders Appendix (ISAAQ-ED)");
}


QString IsaaqEd::description() const
{
    return tr("Internet Severity and Activities Addiction Questionnaire, Eating Disorders Appendix (ISAAQ-ED)");
}


QStringList IsaaqEd::fieldNames() const
{
    return strseq(Q_PREFIX, FIRST_Q, LAST_Q);
}

// ============================================================================
// Instance info
// ============================================================================


bool IsaaqEd::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}


QStringList IsaaqEd::summary() const
{
    // There are no scores or scales
    return QStringList{TextConst::noSummarySeeFacsimile()};
}


QStringList IsaaqEd::detail() const
{
    QStringList lines = completenessInfo();

    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = fieldNames();

    for (int i = 0; i < fieldnames.length(); ++i) {
        const QString& fieldname = fieldnames.at(i);
        lines.append(fieldSummary(fieldname, xstring(fieldname),
                                  spacer, suffix));
    }

    return lines;
}


OpenableWidget* IsaaqEd::editor(const bool read_only)
{
    NameValueOptions freq_options;

    for (int i = 0; i <= MAX_SCORE; i++) {
        auto freq_name = QString("freq_option_%1").arg(i);

        freq_options.append({xstring(freq_name), i});
    }

    const int freq_min_width_px = 100;
    const QVector<int> freq_min_option_widths_px = {100, 100, 100, 100, 100, 100};

    auto heading = new QuHeading(xstring("heading"));
    auto grid = buildGrid(Q_PREFIX, FIRST_Q, LAST_Q, freq_options,
                          xstring("grid_title"));
    grid->setMinimumWidthInPixels(freq_min_width_px, freq_min_option_widths_px);

    QVector<QuElement*> elements{heading, grid};

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title")));

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}


QuMcqGrid* IsaaqEd::buildGrid(const QString prefix,
                              int first_qnum,
                              int last_qnum,
                              const NameValueOptions options,
                              const QString title)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = prefix + QString::number(qnum);
        const QString& description = xstring(fieldname);

        q_field_pairs.append(QuestionWithOneField(description,
                                                  fieldRef(fieldname)));

    }

    auto grid = new QuMcqGrid(q_field_pairs, options);
    grid->setTitle(title);
    // Repeat options every five lines
    QVector<McqGridSubtitle> subtitles{
        {5, title},
        {10, title},
        {15, title},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
