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

// From qvalidator.h:
// Copyright (C) 2016 The Qt Company Ltd.
// Copyright (C) 2012 Klarälvdalens Datakonsult AB, a KDAB Group company,
// info@kdab.com, author Giuseppe D'Angelo <giuseppe.dangelo@kdab.com>
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR
// GPL-2.0-only OR GPL-3.0-only


#pragma once
#include <QValidator>

class Int64Validator : public QValidator
{
    Q_OBJECT
    Q_PROPERTY(qint64 bottom READ bottom WRITE setBottom NOTIFY bottomChanged)
    Q_PROPERTY(qint64 top READ top WRITE setTop NOTIFY topChanged)

public:
    explicit Int64Validator(QObject* parent = nullptr);
    Int64Validator(qint64 bottom, qint64 top, QObject* parent = nullptr);

    QValidator::State validate(QString&, int&) const override;

    void setBottom(qint64);
    void setTop(qint64);
    void setRange(qint64 bottom, qint64 top);

    qint64 bottom() const
    {
        return m_bottom;
    }

    qint64 top() const
    {
        return m_top;
    }

Q_SIGNALS:
    void bottomChanged(qint64 bottom);
    void topChanged(qint64 top);

private:
    Q_DISABLE_COPY(Int64Validator)

    qint64 m_bottom;
    qint64 m_top;
};
