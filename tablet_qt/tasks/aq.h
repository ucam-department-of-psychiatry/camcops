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

#pragma once
#include <QPointer>

#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class Questionnaire;
class QuMcqGrid;

void initializeAq(TaskFactory& factory);

class Aq : public Task
{
    Q_OBJECT

public:
    Aq(CamcopsApp& app,
       DatabaseManager& db,
       int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;

    virtual bool prohibitsCommercial() const override
    {
        return true;
    }

    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    QVariant score() const;
    QVariant socialSkillScore() const;
    QVariant attentionSwitchingScore() const;
    QVariant attentionToDetailScore() const;
    QVariant communicationScore() const;
    QVariant imaginationScore() const;

public:
    static const QString AQ_TABLENAME;

protected:
    QStringList fieldNames() const;

private:
    QuMcqGrid* buildGrid(
        int first_qnum, int last_qnum, QSharedPointer<NameValueOptions> options
    );
    QSharedPointer<NameValueOptions> buildOptions() const;
    QVariant questionsScore(const QVector<int> qnums) const;
    QVariant questionScore(const int qnum) const;
};
