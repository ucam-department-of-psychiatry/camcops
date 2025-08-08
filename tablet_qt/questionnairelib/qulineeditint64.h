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
#include "questionnairelib/qulineedit.h"

class QuLineEditInt64 : public QuLineEdit
{
    // Offers a one-line text editor, for a 64-bit signed integer
    // (qlonglong = qint64).

    Q_OBJECT

public:
    // Constructor for unconstrained numbers
    QuLineEditInt64(FieldRefPtr fieldref);

    // Constructor for constrained numbers.
    QuLineEditInt64(FieldRefPtr fieldref, qint64 minimum, qint64 maximum);

protected:
    qint64 m_minimum;  // minimum; may be std::numeric_limits<qint64>::min()
    qint64 m_maximum;  // maximum; may be std::numeric_limits<qint64>::max()

    virtual QPointer<QValidator> getValidator() override;
    virtual Qt::InputMethodHints getInputMethodHints() override;
};
