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

// #define HANDLE_ORIENTATION_EVENTS
// The width reported in the QScreen orientationChanged event
// seems incorrect on Android and iOS so don't try to redraw the
// questionnaire on orientation change.
// TODO: See if this is fixed when we move to Qt6.2

#include "wsas.h"

#include <QScreen>

#include "common/appstrings.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionwithonefield.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::noneNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 5;
const int MAX_PER_Q = 8;
const qreal MIN_WIDTH_INCHES_FOR_GRID = 7.0;
const QString QPREFIX("q");
const QString Wsas::WSAS_TABLENAME("wsas");
const QString RETIRED_ETC("retired_etc");
const QString Q1_TAG("q1");

void initializeWsas(TaskFactory& factory)
{
    static TaskRegistrar<Wsas> registered(factory);
}

Wsas::Wsas(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, WSAS_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addField(RETIRED_ETC, QMetaType::fromType<bool>());
    addFields(
        strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QMetaType::fromType<int>()
    );

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Wsas::shortname() const
{
    return "WSAS";
}

QString Wsas::longname() const
{
    return tr("Work and Social Adjustment Scale");
}

QString Wsas::description() const
{
    return tr("5-item self-report scale.");
}

// ============================================================================
// Instance info
// ============================================================================

bool Wsas::isComplete() const
{
    return (valueBool(RETIRED_ETC) || !valueIsNull(strnum(QPREFIX, FIRST_Q)))
        && noneNull(values(strseq(QPREFIX, FIRST_Q + 1, N_QUESTIONS)));
}

QStringList Wsas::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), maxScore())};
}

QStringList Wsas::detail() const
{
    return completenessInfo() + summary();
}

OpenableWidget* Wsas::editor(const bool read_only)
{
    FieldRefPtr fr_retired = fieldRef(RETIRED_ETC, false);

    auto page = (new QuPage())->setTitle(longname());

    rebuildPage(page);

    connect(
        fr_retired.data(), &FieldRef::valueChanged, this, &Wsas::workChanged
    );

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    workChanged();

#ifdef HANDLE_ORIENTATION_EVENTS
    QScreen* screen = uifunc::screen();
    screen->setOrientationUpdateMask(
        Qt::LandscapeOrientation | Qt::PortraitOrientation
        | Qt::InvertedLandscapeOrientation | Qt::InvertedPortraitOrientation
    );

    connect(
        screen, &QScreen::orientationChanged, this, &Wsas::orientationChanged
    );
#endif

    return m_questionnaire;
}

void Wsas::orientationChanged(Qt::ScreenOrientation orientation)
{
    Q_UNUSED(orientation)

    refreshQuestionnaire();
}

void Wsas::refreshQuestionnaire()
{
    if (!m_questionnaire) {
        return;
    }
    QuPage* page = m_questionnaire->currentPagePtr();
    rebuildPage(page);

    m_questionnaire->refreshCurrentPage();
}

void Wsas::rebuildPage(QuPage* page)
{
    const NameValueOptions options{
        {appstring(appstrings::WSAS_A_PREFIX + "0"), 0},
        {appstring(appstrings::WSAS_A_PREFIX + "1"), 1},
        {appstring(appstrings::WSAS_A_PREFIX + "2"), 2},
        {appstring(appstrings::WSAS_A_PREFIX + "3"), 3},
        {appstring(appstrings::WSAS_A_PREFIX + "4"), 4},
        {appstring(appstrings::WSAS_A_PREFIX + "5"), 5},
        {appstring(appstrings::WSAS_A_PREFIX + "6"), 6},
        {appstring(appstrings::WSAS_A_PREFIX + "7"), 7},
        {appstring(appstrings::WSAS_A_PREFIX + "8"), 8},
    };
    QVector<QuestionWithOneField> q1_fields{QuestionWithOneField(
        xstring(strnum("q", FIRST_Q), strnum("Q", FIRST_Q)),
        fieldRef(strnum(QPREFIX, FIRST_Q))
    )};

    QVector<QuestionWithOneField> other_q_fields;
    for (int i = FIRST_Q + 1; i <= N_QUESTIONS; ++i) {
        other_q_fields.append(QuestionWithOneField(
            xstring(strnum("q", i), strnum("Q", i)),
            fieldRef(strnum(QPREFIX, i))
        ));
    }

    QVector<QuElement*> elements;
    elements.append((new QuText(xstring("instruction")))->setBold());
    elements.append(
        new QuBoolean(xstring("q_retired_etc"), fieldRef(RETIRED_ETC, false))
    );

    const qreal width_inches = uifunc::screenWidth() / uifunc::screenDpi();
    const bool use_grid = width_inches > MIN_WIDTH_INCHES_FOR_GRID;

    if (use_grid) {
        elements.append((new QuMcqGrid(q1_fields, options))->addTag(Q1_TAG));
        elements.append(new QuMcqGrid(other_q_fields, options));
    } else {
        for (const auto& field : qAsConst(q1_fields)) {
            // re qAsConst():
            // https://stackoverflow.com/questions/35811053/using-c11-range-based-for-loop-correctly-in-qt
            // https://doc.qt.io/qt-6.5/qtglobal.html#qAsConst
            elements.append(
                (new QuText(field.question()))->setBold()->addTag(Q1_TAG)
            );
            elements.append(
                (new QuMcq(field.fieldref(), options))->addTag(Q1_TAG)
            );
        }
        for (const auto& field : qAsConst(other_q_fields)) {
            elements.append((new QuText(field.question()))->setBold());
            elements.append(new QuMcq(field.fieldref(), options));
        }
    }

    page->clearElements();
    page->addElements(elements);
}

// ============================================================================
// Task-specific calculations
// ============================================================================

int Wsas::totalScore() const
{
    return (valueBool(RETIRED_ETC) ? 0 : valueInt(strnum(QPREFIX, FIRST_Q)))
        + sumInt(values(strseq(QPREFIX, FIRST_Q + 1, N_QUESTIONS)));
}

int Wsas::maxScore() const
{
    return MAX_PER_Q
        * (valueBool(RETIRED_ETC) ? (N_QUESTIONS - 1) : N_QUESTIONS);
}

// ============================================================================
// Task-specific calculations
// ============================================================================

void Wsas::workChanged()
{
    if (!m_questionnaire) {
        return;
    }
    m_questionnaire->setVisibleByTag(Q1_TAG, !valueBool(RETIRED_ETC));
}
