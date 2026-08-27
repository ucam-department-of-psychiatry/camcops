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

#include "aqfamily.h"
#include "db/databaseobject.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using stringfunc::strseq;

const int MIN_SCORE = 0;
const int MAX_SCORE = 50;
const int MIN_AREA_SCORE = 0;
const int MAX_AREA_SCORE = 10;

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

const QString Aq::AQ_TABLENAME("aq");

void initializeAq(TaskFactory& factory)
{
    static TaskRegistrar<Aq> registered(factory);
}

Aq::Aq(
    CamcopsApp& app, DatabaseManager& db, const int load_pk, QObject* parent
) :
    // ... see aq.py re error re Q1 in published Baron-Cohen et al. (2001).
    AqFamily(
        app,
        db,
        AQ_TABLENAME,
        50,
        {
            2,  4,  5,  6,  7,  9,  12, 13, 16, 18, 19, 20,
            21, 22, 23, 26, 33, 35, 39, 41, 42, 43, 45, 46,
        },
        parent
    )
{
    addFields(
        strseq(m_q_prefix, m_first_q, m_last_q), QMetaType::fromType<int>()
    );

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
    return tr("Autism Spectrum Quotient (Adult)");
}

QString Aq::description() const
{
    return tr(
        "A 50-item self-report measure used to assess traits of autism in "
        "adults and adolescents aged 16 years and over."
    );
}

// ============================================================================
// Instance info
// ============================================================================

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

QStringList Aq::summary() const
{
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
