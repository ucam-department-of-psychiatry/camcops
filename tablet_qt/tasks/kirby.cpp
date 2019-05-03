/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#if 0

#include "kirby.h"
#include "common/textconst.h"
#include "lib/version.h"
#include "tasklib/taskfactory.h"


const QString Kirby::KIRBY_TABLENAME("kirby");
const QString CURRENCY("£");  // Make configurable? Read local currency?


// ============================================================================
// Pair class
// ============================================================================

class KirbyRewardPair
{
public:
    KirbyRewardPair(int sir, int ldr, int delay_days);

    // Implied value of k if indifferent, according to V = A(1 + kD)
    // where A is amount and D is delay. The units of k are days ^ -1.
    double kIndifference() const;

    // Return the question.
    QString question() const;

    int sir;  // small immediate reward
    int ldr;  // large delayed reward
    int delay_days;
};


KirbyRewardPair::KirbyRewardPair(const int sir, const int ldr,
                                 const int delay_days) :
    sir(sir),
    ldr(ldr),
    delay_days(delay_days)
{
}


double KirbyRewardPair::kIndifference() const
{
    const double a1 = sir;  // amount A1, which is immediate i.e. delay D1 = 0
    const double a2 = ldr;  // amount A2; A2 > A1
    const double d2 = delay_days;  // delay D2
    // Values:
    //      V1 = A1/(1 + kD1) = A1
    //      V2 = A2/(1 + kD2)
    // At indifference,
    //      V1 = V2
    // so
    //      A1      = A2/(1 + kD2)
    //      A2 / A1 = 1 + kD2
    // k = ((A2 / A1) - 1) / D2
    return ((a2 / a1) - 1) / d2;
}


QString KirbyRewardPair::question() const
{
    return QString("Would you prefer %1%2 today, or %1%3 in %4 days?")
            .arg(CURRENCY, QString::number(sir),
                 CURRENCY, QString::number(ldr),
                 QString::number(delay_days));
}


// ============================================================================
// Standard sequence
// ============================================================================

const QVector<KirbyRewardPair> TRIALS{
    {54, 55, 117},  // e.g. "Would you prefer £54 now, or £55 in 117 days?"
    {55, 75, 61},
    {19, 25, 53},
    {31, 85, 7},
    {14, 25, 19},

    {47, 50, 160},
    {15, 35, 13},
    {25, 60, 14},
    {78, 80, 162},
    {40, 55, 62},

    {11, 30, 7},
    {67, 75, 119},
    {34, 35, 186},
    {27, 50, 21},
    {69, 85, 91},

    {49, 60, 89},
    {80, 85, 157},
    {24, 35, 29},
    {33, 80, 14},
    {28, 30, 179},

    {34, 50, 30},
    {25, 30, 80},
    {41, 75, 20},
    {54, 60, 111},
    {54, 80, 30},

    {22, 25, 136},
    {20, 55, 7},
};


// ============================================================================
// Factory function
// ============================================================================

void initializeKirby(TaskFactory& factory)
{
    static TaskRegistrar<Kirby> registered(factory);
}


// ============================================================================
// Main class: constructor
// ============================================================================

Kirby::Kirby(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, KIRBY_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // *** add fields

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Kirby::shortname() const
{
    return "Kirby";
}


QString Kirby::longname() const
{
    return "Kirby Monetary Choice Questionnaire";
}


QString Kirby::description() const
{
    return "Series of hypothetical choices to measure delay discounting.";
}


Version Kirby::minimumServerVersion() const
{
    return Version(2, 3, 3);
}


// ============================================================================
// Instance info
// ============================================================================

bool Kirby::isComplete() const
{
    // ***
}


QStringList Kirby::summary() const
{
    return QStringList{textconst::NO_SUMMARY_SEE_FACSIMILE()};
}


QStringList Kirby::detail() const
{
    // ***
}


OpenableWidget* Kirby::editor(const bool read_only)
{
    // ***

    // *** see also text at https://www.gem-beta.org/public/DownloadMeasure.aspx?mdocid=472

}

#endif
