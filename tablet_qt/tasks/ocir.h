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

#include <QString>

#include "tasklib/task.h"

class CamcopsApp;
class DatabaseManager;
class OpenableWidget;
class Questionnaire;
class QuMcqGrid;

void initializeOcir(TaskFactory& factory);

class Ocir : public Task
{
    Q_OBJECT

public:
    Ocir(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK
    );
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;

    virtual TaskImplementationType implementationType() const override
    {
        return TaskImplementationType::UpgradableSkeleton;
    }

    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;

    static const QString OCIR_TABLENAME;

protected:
    QStringList fieldNames() const;

private:
    QuMcqGrid* buildGrid(
        int first_qnum, int last_qnum, QSharedPointer<NameValueOptions> options
    );
    QSharedPointer<NameValueOptions> buildOptions() const;
    QVariant questionsMean(const QVector<int> qnums) const;
    QVariant questionsScore(const QVector<int> qnums) const;
    QVector<int> allQuestions() const;
    QVector<QVariant> answers(const QVector<int> qnums) const;
    QVariant score() const;
    QVariant mean() const;
    QVariant washingMean() const;
    QVariant checkingMean() const;
    QVariant orderingMean() const;
    QVariant obsessingMean() const;
    QVariant hoardingMean() const;
    QVariant neutralisingMean() const;

};
