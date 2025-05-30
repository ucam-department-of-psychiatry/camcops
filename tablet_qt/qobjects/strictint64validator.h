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
#include <QValidator>

// Validator for qint64 numbers. Checks against the range [bottom, top].

class StrictInt64Validator : public QValidator
{
    Q_OBJECT
    Q_PROPERTY(int bottom READ bottom WRITE setBottom NOTIFY bottomChanged)
    Q_PROPERTY(int top READ top WRITE setTop NOTIFY topChanged)

public:
    StrictInt64Validator(bool allow_empty = false, QObject* parent = nullptr);
    StrictInt64Validator(
        qint64 bottom,
        qint64 top,
        bool allow_empty = false,
        QObject* parent = nullptr
    );
    virtual ~StrictInt64Validator();

    QValidator::State validate(QString& input, int& pos) const override;

    void setBottom(qint64 bottom);
    void setTop(qint64 top);
    virtual void setRange(qint64 bottom, qint64 top);

    qint64 bottom() const
    {
        return m_b;
    }

    qint64 top() const
    {
        return m_t;
    }

signals:
    void bottomChanged(qint64 bottom);
    void topChanged(qint64 top);

private:
    Q_DISABLE_COPY(StrictInt64Validator)

private:
    qint64 m_b;
    qint64 m_t;
    bool m_allow_empty;
};
