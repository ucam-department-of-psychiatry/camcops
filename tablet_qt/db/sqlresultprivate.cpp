/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

/****************************************************************************
**
** Copyright (C) 2016 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the QtSql module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:LGPL$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** GNU Lesser General Public License Usage
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 3 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL3 included in the
** packaging of this file. Please review the following information to
** ensure the GNU Lesser General Public License version 3 requirements
** will be met: https://www.gnu.org/licenses/lgpl-3.0.html.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 2.0 or (at your option) the GNU General
** Public license version 3 or any later version approved by the KDE Free
** Qt Foundation. The licenses are as published by the Free Software
** Foundation and appearing in the file LICENSE.GPL2 and LICENSE.GPL3
** included in the packaging of this file. Please review the following
** information to ensure the GNU General Public License requirements will
** be met: https://www.gnu.org/licenses/gpl-2.0.html and
** https://www.gnu.org/licenses/gpl-3.0.html.
**
** $QT_END_LICENSE$
**
****************************************************************************/

#if 0
#include "sqlresultprivate.h"


QString SqlResultPrivate::holderAt(int index) const
{
    return holders.size() > index ? holders.at(index).holderName : fieldSerial(index);
}


// return a unique id for bound names
QString SqlResultPrivate::fieldSerial(int i) const
{
    ushort arr[] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    ushort *end = &arr[(sizeof(arr)/sizeof(*arr))];
    ushort *ptr = end;

    while (i > 0) {
        *(--ptr) = 'a' + i % 16;
        i >>= 4;
    }

    const int nb = end - ptr;
    *(--ptr) = 'a' + nb;
    *(--ptr) = ':';

    return QString::fromUtf16(ptr, int(end - ptr));
}


static bool qIsAlnum(QChar ch)
{
    uint u = uint(ch.unicode());
    // matches [a-zA-Z0-9_]
    return u - 'a' < 26 || u - 'A' < 26 || u - '0' < 10 || u == '_';
}


QString SqlResultPrivate::positionalToNamedBinding(const QString &query) const
{
    int n = query.size();

    QString result;
    result.reserve(n * 5 / 4);
    QChar closingQuote;
    int count = 0;
    bool ignoreBraces = (sqldriver->dbmsType() == QSqlDriver::PostgreSQL);

    for (int i = 0; i < n; ++i) {
        QChar ch = query.at(i);
        if (!closingQuote.isNull()) {
            if (ch == closingQuote) {
                if (closingQuote == QLatin1Char(']')
                    && i + 1 < n && query.at(i + 1) == closingQuote) {
                    // consume the extra character. don't close.
                    ++i;
                    result += ch;
                } else {
                    closingQuote = QChar();
                }
            }
            result += ch;
        } else {
            if (ch == QLatin1Char('?')) {
                result += fieldSerial(count++);
            } else {
                if (ch == QLatin1Char('\'') || ch == QLatin1Char('"') || ch == QLatin1Char('`'))
                    closingQuote = ch;
                else if (!ignoreBraces && ch == QLatin1Char('['))
                    closingQuote = QLatin1Char(']');
                result += ch;
            }
        }
    }
    result.squeeze();
    return result;
}


QString SqlResultPrivate::namedToPositionalBinding(const QString &query)
{
    int n = query.size();

    QString result;
    result.reserve(n);
    QChar closingQuote;
    int count = 0;
    int i = 0;
    bool ignoreBraces = (sqldriver->dbmsType() == QSqlDriver::PostgreSQL);

    while (i < n) {
        QChar ch = query.at(i);
        if (!closingQuote.isNull()) {
            if (ch == closingQuote) {
                if (closingQuote == QLatin1Char(']')
                        && i + 1 < n && query.at(i + 1) == closingQuote) {
                    // consume the extra character. don't close.
                    ++i;
                    result += ch;
                } else {
                    closingQuote = QChar();
                }
            }
            result += ch;
            ++i;
        } else {
            if (ch == QLatin1Char(':')
                    && (i == 0 || query.at(i - 1) != QLatin1Char(':'))
                    && (i + 1 < n && qIsAlnum(query.at(i + 1)))) {
                int pos = i + 2;
                while (pos < n && qIsAlnum(query.at(pos)))
                    ++pos;
                QString holder(query.mid(i, pos - i));
                indexes[holder].append(count++);
                holders.append(QHolder(holder, i));
                result += QLatin1Char('?');
                i = pos;
            } else {
                if (ch == QLatin1Char('\'') || ch == QLatin1Char('"') || ch == QLatin1Char('`'))
                    closingQuote = ch;
                else if (!ignoreBraces && ch == QLatin1Char('['))
                    closingQuote = QLatin1Char(']');
                result += ch;
                ++i;
            }
        }
    }
    result.squeeze();
    values.resize(holders.size());
    return result;
}
#endif
