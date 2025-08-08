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

#include "urlvalidator.h"

#include <QString>
#include <QUrl>
#include <QValidator>

UrlValidator::UrlValidator(QObject* parent) :
    QValidator(parent)
{
}

QValidator::State UrlValidator::validate(QString& input, int&) const
{
    qDebug() << Q_FUNC_INFO;
    qDebug() << input;

    const auto url = QUrl(input);

    if (!url.isValid()) {
        qDebug() << "URL not valid";
        return QValidator::Intermediate;
    }

    const QList<QString> valid_schemes = {"http", "https"};

    if (!valid_schemes.contains(url.scheme())) {
        qDebug() << "Scheme not valid";
        return QValidator::Intermediate;
    }

    if (url.host().length() == 0) {
        qDebug() << "Host length zero";
        return QValidator::Intermediate;
    }

    // Port can be empty and then we just won't save it (443 will be the
    // default)

    // Path can be empty too

    return QValidator::Acceptable;
}
