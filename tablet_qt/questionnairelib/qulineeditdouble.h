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

class QuLineEditDouble : public QuLineEdit
{
    // - Offers a one-line text editor, for a floating-point number.
    // - The default maximum number of decimal places, 1000, matches
    //   QDoubleValidator; see
    //   https://doc.qt.io/qt-6.5/qdoublevalidator.html#decimals-prop

    Q_OBJECT

public:
    // Constructor for unconstrained numbers
    QuLineEditDouble(
        FieldRefPtr fieldref,
        bool allow_empty = true,
        QObject* parent = nullptr
    );

    // Constructor for constrained numbers.
    // - decimals: maximum number of decimal places; see above.
    // - allow_empty: OK to be blank?
    QuLineEditDouble(
        FieldRefPtr fieldref,
        double minimum,
        double maximum,
        int decimals = 1000,
        bool allow_empty = true,
        QObject* parent = nullptr
    );

protected:
    virtual QPointer<QValidator> getValidator() override;
    virtual Qt::InputMethodHints getInputMethodHints() override;

protected:
    double m_minimum;  // minimum; may be std::numeric_limits<double>::lowest()
    double m_maximum;  // maximum; may be std::numeric_limits<double>::max()
    int m_decimals;
    // ... maximum number of decimal places
    bool m_allow_empty;  // allow an empty field?
};
