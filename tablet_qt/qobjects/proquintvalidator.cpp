/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include <QRegularExpression>
#include <QRegularExpressionMatch>
#include <QString>
#include <QUrl>
#include <QValidator>

#include "proquintvalidator.h"


ProquintValidator::ProquintValidator(QObject * parent) : QValidator(parent)
{
}

QValidator::State ProquintValidator::validate(QString &input, int &) const
{

    const QString consonant = "[bdfghjklmnprstvz]";
    const QString vowel = "[aiou]";
    const QString quint = QString("%1%2%3%4%5").arg(
        consonant, vowel, consonant, vowel, consonant
    );
    QRegularExpression proquint_regex(
        QString("%1-%2-%3-%4-%5-%6-%7-%8").arg(
            quint,quint,quint,quint,quint,quint,quint,quint
        )
    );

    QRegularExpressionMatch match = proquint_regex.match(input);

    if (!match.hasMatch()) {
        return QValidator::Intermediate;
    }

    return QValidator::Acceptable;
}
