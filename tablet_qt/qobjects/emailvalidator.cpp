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

#include "emailvalidator.h"

#include <QRegularExpression>
#include <QString>
#include <QValidator>


const QString EMAIL_RE_STR(
    // Regex for an e-mail address.
    // From colander.__init__.py, in turn from
    // https://html.spec.whatwg.org/multipage/input.html#e-mail-state-(type=email)
    // Note that C++ raw strings start R"( and end )"

    R"(^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9])"
    R"((?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9])"
    R"((?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$)"
);

const QString BLANK_RE_STR(
    // Regex for an empty string.
    // https://stackoverflow.com/questions/19127384/what-is-a-regex-to-match-only-an-empty-string

    R"(^(?![\s\S]))"
);

const QString EMAIL_OR_BLANK_RE_STR(
    // Regex to match an e-mail address (as above) or a blank string.

    QString("(?:%1)|(?:%2)").arg(EMAIL_RE_STR, BLANK_RE_STR)
);

EmailValidator::EmailValidator(QObject* parent, const bool allow_blank) :
    QRegularExpressionValidator(
        allow_blank ? QRegularExpression(EMAIL_OR_BLANK_RE_STR)
                    : QRegularExpression(EMAIL_RE_STR),
        parent
    )
{
}
