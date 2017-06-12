/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#pragma once
#include "db/databaseobject.h"


class CardinalExpDetThresholdTrial : public DatabaseObject
{
    Q_OBJECT
public:
    CardinalExpDetThresholdTrial(CamcopsApp& app, const QSqlDatabase& db,
                                 int load_pk = dbconst::NONEXISTENT_PK);
    CardinalExpDetThresholdTrial(
            int task_pk, int trial_num,
            const QVariant& trial_num_ignoring_catch_trials,
            bool target_presented, qreal intensity,
            CamcopsApp& app, const QSqlDatabase& db);
    bool wasCaughtOutReset() const;
    int trialNum() const;
    int trialNumIgnoringCatchTrials() const;
    bool targetPresented() const;
    qreal intensity() const;
    bool yes() const;
    void setCaughtOutReset();
    void recordChoiceTime();
    void recordResponse(bool yes);
    QString summary() const;
    void setTrialNumInCalcSeq(const QVariant& value);
public:
    static const QString TRIAL_TABLENAME;
    static const QString FN_FK_TO_TASK;
    static const QString FN_TRIAL;
protected:
};
