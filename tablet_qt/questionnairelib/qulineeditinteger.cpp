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

#include "qulineeditinteger.h"

#include <limits>
#include <QIntValidator>
#include <QLineEdit>

#include "qobjects/strictintvalidator.h"

QuLineEditInteger::QuLineEditInteger(
    FieldRefPtr fieldref, const bool allow_empty, QObject* parent
) :
    QuLineEdit(fieldref, parent),
    m_minimum(std::numeric_limits<int>::min()),
    m_maximum(std::numeric_limits<int>::max()),
    m_allow_empty(allow_empty),
    m_strict_validator(true)
{
    setDefaultHint();
}

QuLineEditInteger::QuLineEditInteger(
    FieldRefPtr fieldref,
    const int minimum,
    const int maximum,
    const bool allow_empty,
    QObject* parent
) :
    QuLineEdit(fieldref, parent),
    m_minimum(minimum),
    m_maximum(maximum),
    m_allow_empty(allow_empty),
    m_strict_validator(true)
{
    setDefaultHint();
}

void QuLineEditInteger::setDefaultHint()
{
    setHint(QString("integer, range %1 to %2").arg(m_minimum).arg(m_maximum));
}

QuLineEditInteger* QuLineEditInteger::setStrictValidator(const bool strict)
{
    m_strict_validator = strict;
    return this;
}

QPointer<QValidator> QuLineEditInteger::getValidator()
{
    if (m_strict_validator) {
        return new StrictIntValidator(
            m_minimum, m_maximum, m_allow_empty, this
        );
    }

    return new QIntValidator(m_minimum, m_maximum, this);
}

Qt::InputMethodHints QuLineEditInteger::getInputMethodHints()
{
    return Qt::ImhFormattedNumbersOnly;
}
