/*
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


// ============================================================================
// Make sequences of strings
// ============================================================================

QStringList StringFunc::strseq(const QString& prefix, int first, int last)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2";
    for (int i = first; i <= last; ++i) {
        list.append(format.arg(prefix).arg(i));
    }
    return list;
}


QStringList StringFunc::strseq(const QString& prefix, int first, int last,
                               const QStringList& suffixes)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2%3";
    for (int i = first; i <= last; ++i) {
        for (auto suffix : suffixes) {
            list.append(format.arg(prefix).arg(i).arg(suffix));
        }
    }
    return list;
}


QStringList StringFunc::strseq(const QString& prefix, int first, int last,
                               const QString& suffix)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2%3";
    for (int i = first; i <= last; ++i) {
        list.append(format.arg(prefix).arg(i).arg(suffix));
    }
    return list;
}


QStringList StringFunc::strseq(const QStringList& prefixes, int first,
                               int last)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2";
    for (auto prefix : prefixes) {
        for (int i = first; i <= last; ++i) {
            list.append(format.arg(prefix).arg(i));
        }
    }
    return list;
}


QStringList StringFunc::strseq(const QStringList& prefixes, int first,
                               int last, const QStringList& suffixes)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2%3";
    for (auto prefix : prefixes) {
        for (int i = first; i <= last; ++i) {
            for (auto suffix : suffixes) {
                list.append(format.arg(prefix).arg(i).arg(suffix));
            }
        }
    }
    return list;
}


// ============================================================================
// Other string formatting
// ============================================================================

QString StringFunc::strnum(const QString& prefix, int num)
{
    return QString("%1%2").arg(prefix).arg(num);
}


// ============================================================================
// HTML processing
// ============================================================================

QString StringFunc::bold(const QString& str)
{
    return QString("<b>%1</b>").arg(str);
}


QString StringFunc::bold(int x)
{
    return QString("<b>%1</b>").arg(x);
}


QString StringFunc::joinHtmlLines(const QStringList& lines)
{
    return lines.join("<br>");
}


QString& StringFunc::toHtmlLinebreaks(QString& str,
                                      bool convert_embedded_literals)
{
    str.replace("\n", "<br>");
    if (convert_embedded_literals) {
        str.replace("\\n", "<br>");
    }
    return str;
}


// ============================================================================
// Other string processing
// ============================================================================

QString& StringFunc::replaceFirst(QString& str, const QString& from,
                                  const QString& to)
{
    // Replaces in situ
    return str.replace(str.indexOf(from), from.length(), to);
}
