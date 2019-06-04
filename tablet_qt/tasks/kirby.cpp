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

#include "kirby.h"
#include "common/textconst.h"
#include "db/ancillaryfunc.h"
#include "lib/version.h"
#include "tasklib/taskfactory.h"
#include "../taskxtra/kirbyrewardpair.h"
#include "../taskxtra/kirbytrial.h"


// ============================================================================
// Constants
// ============================================================================

const QString Kirby::KIRBY_TABLENAME("kirby_mcq");


// ============================================================================
// Factory function
// ============================================================================

void initializeKirby(TaskFactory& factory)
{
    static TaskRegistrar<Kirby> registered(factory);
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
const int TOTAL_N_TRIALS = TRIALS.size();  // 27


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
// Ancillary management
// ============================================================================

QStringList Kirby::ancillaryTables() const
{
    return QStringList{KirbyTrial::KIRBY_TRIAL_TABLENAME};
}


QString Kirby::ancillaryTableFKToTaskFieldname() const
{
    return KirbyTrial::FN_FK_TO_TASK;
}


void Kirby::loadAllAncillary(const int pk)
{
    const OrderBy order_by{{KirbyTrial::FN_TRIAL, true}};
    ancillaryfunc::loadAncillary<KirbyTrial, KirbyTrialPtr>(
                m_trials, m_app, m_db,
                KirbyTrial::FN_FK_TO_TASK, order_by, pk);
}


QVector<DatabaseObjectPtr> Kirby::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>{
        KirbyTrialPtr(new KirbyTrial(m_app, m_db)),
    };
}


QVector<DatabaseObjectPtr> Kirby::getAllAncillary() const
{
    QVector<DatabaseObjectPtr> ancillaries;
    for (const KirbyTrialPtr& trial : m_trials) {
        ancillaries.append(trial);
    }
    return ancillaries;
}


// ============================================================================
// Instance info
// ============================================================================

bool Kirby::isComplete() const
{
    return false; // ***
    // return valueBool(FN_FINISHED);
}


QStringList Kirby::summary() const
{
    return QStringList(); // ***
}


QStringList Kirby::detail() const
{
    return QStringList(); // ***
}


OpenableWidget* Kirby::editor(const bool read_only)
{
    // ***

    // *** see also text at https://www.gem-beta.org/public/DownloadMeasure.aspx?mdocid=472

    Q_UNUSED(read_only);
    return nullptr; // ***
}
