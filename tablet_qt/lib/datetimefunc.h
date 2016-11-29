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

#pragma once
#include <QDateTime>
class QVariant;

namespace DateTime {

    extern const QString SHORT_DATETIME_FORMAT;
    extern const QString SHORT_DATE_FORMAT;
    extern const QString TEXT_DATE_FORMAT;
    extern const QString UNKNOWN;

    QString datetimeToIsoMs(const QDateTime& dt);
    QString datetimeToIsoMsUtc(const QDateTime& dt);
    QDateTime isoToDateTime(const QString& iso);
    QDateTime now();
    QDate nowDate();
    QString shortDateTime(const QDateTime& dt);
    QString shortDate(const QDate& d);
    QString textDate(const QDate& d);
    QString textDate(const QVariant& date);
    int ageYearsFrom(const QDate& from, const QDate& to);
    int ageYears(const QVariant& dob, int default_years = -1);
    double doubleSecondsFrom(const QDateTime& from, const QDateTime& to);
}
