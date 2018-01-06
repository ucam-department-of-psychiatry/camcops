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
#include <QString>
#include "db/fieldref.h"


class QuestionWithOneField
{
    // Encapsulates a question (text) with a FieldRef.
    // Used by e.g. QuMCQGrid; QuMultipleResponse.

public:
    QuestionWithOneField();  // so it can live in a QVector
    QuestionWithOneField(const QString& question, FieldRefPtr fieldref);
    QuestionWithOneField(FieldRefPtr fieldref, const QString& question);
    // ... for convenience
    QString question() const;
    QString text() const;  // synonym
    FieldRefPtr fieldref() const;
protected:
    QString m_question;
    FieldRefPtr m_fieldref;
};
