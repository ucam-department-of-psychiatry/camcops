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

#include "uint64validator.h"

#include <QValidator>

UInt64Validator::UInt64Validator(QObject* parent) :
    UInt64Validator(
        std::numeric_limits<quint64>::min(),
        std::numeric_limits<qint64>::max(),
        parent
    )
{
}

UInt64Validator::UInt64Validator(
    quint64 minimum, quint64 maximum, QObject* parent
) :
    QValidator(parent)
{
    m_bottom = minimum;
    m_top = maximum;
}

QValidator::State UInt64Validator::validate(QString& input, int&) const
{
    if (input.isEmpty()) {
        return Intermediate;
    }

    if (input[0] == '-') {
        return Invalid;
    }

    const bool starts_with_plus(input[0] == '+');
    if (input.length() == 1 && starts_with_plus) {
        return Intermediate;
    }

    bool ok;
    qulonglong entered = locale().toULongLong(input, &ok);
    if (!ok) {
        return Invalid;
    }

    if (entered >= m_bottom && entered <= m_top) {
        return Acceptable;
    }

    return Intermediate;
}

void UInt64Validator::setRange(quint64 bottom, quint64 top)
{
    bool range_changed = false;
    if (m_bottom != bottom) {
        m_bottom = bottom;
        range_changed = true;
        emit bottomChanged(m_bottom);
    }

    if (m_top != top) {
        m_top = top;
        range_changed = true;
        emit topChanged(m_top);
    }

    if (range_changed) {
        emit changed();
    }
}

void UInt64Validator::setBottom(quint64 bottom)
{
    setRange(bottom, top());
}

void UInt64Validator::setTop(quint64 top)
{
    setRange(bottom(), top);
}
