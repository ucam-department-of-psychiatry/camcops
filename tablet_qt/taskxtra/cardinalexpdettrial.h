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


class CardinalExpDetTrial : public DatabaseObject
{
    Q_OBJECT
public:
    CardinalExpDetTrial(CamcopsApp& app, const QSqlDatabase& db,
                        int load_pk = dbconst::NONEXISTENT_PK);
    CardinalExpDetTrial(
            int task_pk,
            int block, int group, int cue, int raw_cue,
            int target_modality, int target_number, bool target_present,
            double iti_s,
            CamcopsApp& app, const QSqlDatabase& db);
    void setTrialNum(int trial_num);
    int trialNum() const;
public:
    static const QString TRIAL_TABLENAME;
    static const QString FN_FK_TO_TASK;
    static const QString FN_TRIAL;
protected:
};
