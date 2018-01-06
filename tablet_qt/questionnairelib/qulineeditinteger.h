/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
#include "questionnairelib/qulineedit.h"


class QuLineEditInteger : public QuLineEdit
{
    // Offers a one-line text editor, for an integer.

    Q_OBJECT
public:
    QuLineEditInteger(FieldRefPtr fieldref, bool allow_empty = true);
    QuLineEditInteger(FieldRefPtr fieldref, int minimum, int maximum,
                      bool allow_empty = true);
    QuLineEditInteger* setStrictValidator(bool strict);
protected:
    virtual void extraLineEditCreation(QLineEdit* editor) override;
protected:
    virtual void setDefaultHint();
protected:
    int m_minimum;
    int m_maximum;
    bool m_allow_empty;
    bool m_strict_validator;
};
