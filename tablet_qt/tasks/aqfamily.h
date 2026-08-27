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

#include "tasklib/task.h"

class QuMcqGrid;

class AqFamily : public Task
{
    // This is an abstract class (it doesn't implement all of Task's pure
    // virtual methods). It supports the AQ and AQ-10 tasks.
    Q_OBJECT

public:
    AqFamily(
        CamcopsApp& app,
        DatabaseManager& db,
        const QString& tablename,
        const int last_q,
        const QVector<int> agree_scoring_questions,
        QObject* parent = nullptr
    );

    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual bool prohibitsCommercial() const override
    {
        return true;
    }

    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    QVariant score() const;

protected:
    const int m_first_q = 1;
    int m_last_q;
    const QString m_q_prefix = "q";
    QVector<int> m_agree_scoring_questions;

    QStringList fieldNames() const;

    QuMcqGrid* buildGrid(QSharedPointer<NameValueOptions> options);
    QSharedPointer<NameValueOptions> buildOptions() const;
    QString rangeScore(
        const QString& description,
        const QVariant score,
        const int min,
        const int max
    ) const;
    QVariant questionsScore(const QVector<int> qnums) const;
    QVariant questionScore(const int qnum) const;
};
