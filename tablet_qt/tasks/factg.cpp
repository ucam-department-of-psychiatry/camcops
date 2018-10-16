/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#include "factg.h"

#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"

const QString Factg::FACTG_TABLENAME("factg");

const QString SUBTITLE_PHYSICAL("Physical Well-Being");
const QString SUBTITLE_SOCIAL("Social/Family Well-Being");
const QString SUBTITLE_EMOTIONAL("Emotional Well-Being");
const QString SUBTITLE_FUNCTIONAL("Functional Well-Being");

const QString PREFIX_PHYSICAL("p_q");
const QString PREFIX_SOCIAL("s_q");
const QString PREFIX_EMOTIONAL("e_q");
const QString PREFIX_FUNCTIONAL("f_q");

const int FIRST_Q = 1;
const int LAST_Q_PHYSICAL = 7;
const int LAST_Q_SOCIAL = 7;
const int LAST_Q_EMOTIONAL = 6;
const int LAST_Q_FUNCTIONAL = 7;

const int N_PHYSICAL = 7;
const int N_SOCIAL = 7;
const int N_EMOTIONAL = 6;
const int N_FUNCTIONAL= 7;

const int MAX_SCORE_PHYSICAL = 28;
const int MAX_SCORE_SOCIAL = 28;
const int MAX_SCORE_EMOTIONAL = 24;
const int MAX_SCORE_FUNCTIONAL = 28;

const int MAX_SCORE =    MAX_SCORE_PHYSICAL
                       + MAX_SCORE_SOCIAL
                       + MAX_SCORE_EMOTIONAL
                       + MAX_SCORE_FUNCTIONAL;

const QString IGNORE_Q7("ignore_q7");
const QString OPTIONAL_Q(PREFIX_SOCIAL + "7");

using stringfunc::strseq;
using mathfunc::anyNull;
using mathfunc::countNotNull;
using mathfunc::scorePhrase;
using mathfunc::sumDouble;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;

void initializeFactg(TaskFactory& factory)
{
    static TaskRegistrar<Factg> registered(factory);
}

Factg::Factg(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, FACTG_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_in_tickbox_change(false)
{
    for (auto field : strseq(PREFIX_PHYSICAL, FIRST_Q, LAST_Q_PHYSICAL)) {
        addField(field, QVariant::Int);
    }

    for (auto field : strseq(PREFIX_SOCIAL, FIRST_Q, LAST_Q_SOCIAL)) {
        addField(field, QVariant::Int);
    }

    for (auto field : strseq(PREFIX_EMOTIONAL, FIRST_Q, LAST_Q_EMOTIONAL)) {
        addField(field, QVariant::Int);
    }

    for (auto field : strseq(PREFIX_FUNCTIONAL, FIRST_Q, LAST_Q_FUNCTIONAL)) {
        addField(field, QVariant::Int);
    }

    addField(IGNORE_Q7, QVariant::Bool);

    if (load_pk == dbconst::NONEXISTENT_PK) {
        setValue(IGNORE_Q7, false, false);
    }

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Factg::shortname() const
{
    return "FACT-G";
}


QString Factg::longname() const
{
    return tr("Functional Assessment of Cancer Therapy—General");
}


QString Factg::menusubtitle() const
{
    return tr("A 27-item general cancer quality-of-life (QL) measure - "
              "version 4.");
}

// ============================================================================
// Instance info
// ============================================================================

QVector<QVariant> Factg::getScores() const
{
    QVector<QVariant> vals = values(strseq(PREFIX_PHYSICAL, FIRST_Q,
                                           LAST_Q_PHYSICAL));

    double score_phys, score_soc, score_emo, score_func;

    int answered = countNotNull(vals);
    score_phys = (answered > 0) ?
                (sumInt(vals) * N_PHYSICAL) / answered
            : 0;

    vals = values(strseq(PREFIX_SOCIAL, FIRST_Q, LAST_Q_SOCIAL));
    answered = countNotNull(vals);
    score_soc = (answered > 0) ?
                (sumInt(vals) * N_SOCIAL) / answered
            : 0;

    vals = values(strseq(PREFIX_EMOTIONAL, FIRST_Q, LAST_Q_EMOTIONAL));
    answered = countNotNull(vals);
    score_emo = (answered > 0) ?
                (sumInt(vals) * N_EMOTIONAL) / answered
            : 0;

    vals = values(strseq(PREFIX_FUNCTIONAL, FIRST_Q, LAST_Q_FUNCTIONAL));
    answered = countNotNull(vals);
    score_func = (answered > 0) ?
                (sumInt(vals) * N_FUNCTIONAL) / answered
            : 0;

    return {score_phys, score_soc, score_emo, score_func};
}

QStringList Factg::summary() const
{
    return QStringList{totalScorePhrase(sumDouble(getScores()), MAX_SCORE)};
}

QStringList Factg::detail() const
{
    QVector<QVariant> scores = getScores();

    return QStringList{
        totalScorePhrase(sumDouble(scores), MAX_SCORE),
        scorePhrase(SUBTITLE_PHYSICAL, scores.at(0).toDouble(),
                    MAX_SCORE_EMOTIONAL),
        scorePhrase(SUBTITLE_SOCIAL, scores.at(1).toDouble(),
                    MAX_SCORE_SOCIAL),
        scorePhrase(SUBTITLE_EMOTIONAL, scores.at(2).toDouble(),
                    MAX_SCORE_EMOTIONAL),
        scorePhrase(SUBTITLE_FUNCTIONAL, scores.at(3).toDouble(),
                    MAX_SCORE_FUNCTIONAL)
    };
}

bool Factg::isComplete() const
{
    int last_q_social = LAST_Q_SOCIAL;

    if (value(IGNORE_Q7).toBool()) {
        --last_q_social;
    }

    return
        !(anyNull(values(strseq(PREFIX_PHYSICAL, FIRST_Q, LAST_Q_PHYSICAL))) ||
        anyNull(values(strseq(PREFIX_SOCIAL, FIRST_Q, last_q_social)))       ||
        anyNull(values(strseq(PREFIX_EMOTIONAL, FIRST_Q, LAST_Q_EMOTIONAL))) ||
        anyNull(values(strseq(PREFIX_FUNCTIONAL, FIRST_Q, LAST_Q_FUNCTIONAL))));
}

void Factg::updateQ7(const FieldRef* fieldref)
{
    if (m_in_tickbox_change) {
        // avoid circular signal
        return;
    }
    m_in_tickbox_change = true;
    bool prefer_no_answer = fieldref->valueBool();

    FieldRefPtr fr_q7 = fieldRef(OPTIONAL_Q);
    fr_q7->setMandatory(!prefer_no_answer);

    if (prefer_no_answer) {
        fr_q7->setValue(QVariant());
    }

    fieldRef(IGNORE_Q7)->setValue(prefer_no_answer);

    m_in_tickbox_change = false;
}

void Factg::untickBox()
{
    fieldRef(IGNORE_Q7)->setValue(false);
}

OpenableWidget* Factg::editor(const bool read_only)
{   
    const NameValueOptions options_normal{
        {xstring("a0"), 0},
        {xstring("a1"), 1},
        {xstring("a2"), 2},
        {xstring("a3"), 3},
        {xstring("a4"), 4},
    };

    const NameValueOptions options_reversed{
        {xstring("a0"), 4},
        {xstring("a1"), 3},
        {xstring("a2"), 2},
        {xstring("a3"), 1},
        {xstring("a4"), 0},
    };

    const int question_width = 50;
    const QVector<int> option_widths{10, 10, 10, 10, 10};

    // ========================================================================
    // Physical
    // ========================================================================
    QVector<QuestionWithOneField> fields;
    for (auto field : strseq(PREFIX_PHYSICAL, FIRST_Q, LAST_Q_PHYSICAL)) {
        fields.append(QuestionWithOneField(xstring(field), fieldRef(field)));
    }
    QuPagePtr p1((new QuPage{
                     (new QuText(xstring("instruction")))->setBold(true),
                     (new QuMcqGrid({fields}, options_reversed))
                      ->setExpand(true)
                      ->setWidth(question_width, option_widths)
                 })->setTitle(xstring("title_main")));

    // ========================================================================
    // Social
    // ========================================================================
    fields.clear();
    for (auto field : strseq(PREFIX_SOCIAL, FIRST_Q, LAST_Q_SOCIAL - 1)) {
        fields.append(QuestionWithOneField(xstring(field), fieldRef(field)));
    }

    QuMcqGrid *g1, *g2;

    g1 = (new QuMcqGrid({fields}, options_normal))
            ->setExpand(true)
            ->setWidth(question_width, option_widths);

    FieldRefPtr ignore_q7 = fieldRef(IGNORE_Q7);
    connect(ignore_q7.data(), &FieldRef::valueChanged, this,
            &Factg::updateQ7);

    QuBoolean *no_answer = (new QuBoolean(
                            xstring("prefer_no_answer"),
                            ignore_q7))
            ->setFalseAppearsBlank();

    FieldRefPtr fr_q7 = fieldRef(PREFIX_SOCIAL + "7");
    fr_q7->setMandatory(!ignore_q7->valueBool());

    connect(fr_q7.data(), &FieldRef::valueChanged, this,
            &Factg::untickBox);

    g2 = (new QuMcqGrid({
            QuestionWithOneField(xstring(OPTIONAL_Q),
                                 fr_q7)}, options_normal))
            ->showTitle(false)
            ->setExpand(true)
            ->setWidth(question_width, option_widths);

    QuPagePtr p2((new QuPage{
                      g1,
                      no_answer,
                      g2
                  })->setTitle(xstring("title_main")));

    // ========================================================================
    // Emotional
    // ========================================================================
    g1 = (new QuMcqGrid({
            QuestionWithOneField(xstring(PREFIX_EMOTIONAL + "1"),
                                 fieldRef(PREFIX_EMOTIONAL + "1"))
                                  }, options_reversed))
            ->setExpand(true)
            ->setWidth(question_width, option_widths);


    g2 = (new QuMcqGrid({
            QuestionWithOneField(xstring(PREFIX_EMOTIONAL + "2"),
                                 fieldRef(PREFIX_EMOTIONAL + "2"))
                                  }, options_normal))
            ->showTitle(false)
            ->setExpand(true)
            ->setWidth(question_width, option_widths);

    fields.clear();
    for (auto field : strseq(PREFIX_EMOTIONAL, 3, LAST_Q_EMOTIONAL)) {
        fields.append(QuestionWithOneField(xstring(field), fieldRef(field)));
    }
    QuPagePtr p3((new QuPage{
                     g1,
                     g2,
                    (new QuMcqGrid({fields}, options_reversed))
                        ->showTitle(false)
                        ->setExpand(true)
                      ->setWidth(question_width, option_widths)
                 })->setTitle(xstring("title_main")));

    // ========================================================================
    // Functional
    // ========================================================================
    fields.clear();
    for (auto field : strseq(PREFIX_FUNCTIONAL, FIRST_Q, LAST_Q_FUNCTIONAL)) {
        fields.append(QuestionWithOneField(xstring(field), fieldRef(field)));
    }
    QuPagePtr p4((new QuPage{
                      (new QuMcqGrid({fields}, options_normal))
                        ->setExpand(true),
                      new QuSpacer(),
                      (new QuText(xstring("thanks")))->setBold(true),
                  })->setTitle(xstring("title_main")));

    auto q = new Questionnaire(m_app, {p1, p2, p3, p4});
    q->setReadOnly(read_only);
    return q;
}
