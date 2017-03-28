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

#include "stringfunc.h"


namespace stringfunc {

// ============================================================================
// Basic string formatting
// ============================================================================

QString strnum(const QString& prefix, int num, const QString& suffix)
{
    return prefix + QString::number(num) + suffix;
}

QStringList strnumlist(const QString& prefix, const QList<int>& numbers,
                       const QString& suffix)
{
    QStringList strings;
    for (auto num : numbers) {
        strings.append(strnum(prefix, num, suffix));
    }
    return strings;
}


// ============================================================================
// Make sequences of strings
// ============================================================================

QStringList strseq(const QString& prefix, int first, int last)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    for (int i = first; i <= last; ++i) {
        list.append(strnum(prefix, i));
    }
    return list;
}


QStringList strseq(const QString& prefix, int first, int last,
                   const QStringList& suffixes)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    for (int i = first; i <= last; ++i) {
        for (auto suffix : suffixes) {
            list.append(strnum(prefix, i, suffix));
        }
    }
    return list;
}


QStringList strseq(const QString& prefix, int first, int last,
                   const QString& suffix)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    for (int i = first; i <= last; ++i) {
        list.append(strnum(prefix, i, suffix));
    }
    return list;
}


QStringList strseq(const QStringList& prefixes, int first, int last)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    for (auto prefix : prefixes) {
        for (int i = first; i <= last; ++i) {
            list.append(strnum(prefix, i));
        }
    }
    return list;
}


QStringList strseq(const QStringList& prefixes, int first, int last,
                   const QStringList& suffixes)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    for (auto prefix : prefixes) {
        for (int i = first; i <= last; ++i) {
            for (auto suffix : suffixes) {
                list.append(strnum(prefix, i, suffix));
            }
        }
    }
    return list;
}


// ============================================================================
// HTML processing
// ============================================================================

QString bold(const QString& str)
{
    return QString("<b>%1</b>").arg(str);
}


QString bold(int x)
{
    return QString("<b>%1</b>").arg(x);
}


QString joinHtmlLines(const QStringList& lines)
{
    return lines.join("<br>");
}


QString& toHtmlLinebreaks(QString& str, bool convert_embedded_literals)
{
    str.replace("\n", "<br>");
    if (convert_embedded_literals) {
        str.replace("\\n", "<br>");
    }
    return str;
}


QString standardResult(const QString& name,
                       const QString& value,
                       const QString& separator,
                       const QString& suffix)
{
    return QString("%1%2<b>%3</b>%4").arg(name, separator, value, suffix);
}


// ============================================================================
// Other string processing
// ============================================================================

QString& replaceFirst(QString& str, const QString& from, const QString& to)
{
    // Replaces in situ
    return str.replace(str.indexOf(from), from.length(), to);
}


}  // namespace stringfunc
