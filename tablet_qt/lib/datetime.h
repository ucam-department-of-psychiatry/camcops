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
#include <QDateTime>
class QVariant;

namespace datetime {

extern const QString LONG_DATE_FORMAT;
extern const QString TIMESTAMP_FORMAT;
extern const QString SHORT_DATETIME_FORMAT;
extern const QString SHORT_DATE_FORMAT;
extern const QString TEXT_DATE_FORMAT;
extern const QString TEXT_DATETIME_FORMAT;
extern const QString UNKNOWN;

QString dateToIso(const QDate& d);
QString datetimeToIsoMs(const QDateTime& dt, bool use_z_timezone = false);
QString datetimeToIsoMsUtc(const QDateTime& dt, bool use_z_timezone = false);
QDate isoToDate(const QString& iso);
QDateTime isoToDateTime(const QString& iso);

QDateTime now();
QDate nowDate();
QString nowTimestamp();

QString timestampDateTime(const QDateTime& dt);
QString timestampDateTime(const QVariant& dt);
QString shortDateTime(const QDateTime& dt);
QString shortDateTime(const QVariant& dt);
QString textDateTime(const QDateTime& dt);
QString textDateTime(const QVariant& dt);

QString shortDate(const QDate& d);
QString shortDate(const QVariant& d);
QString textDate(const QDate& d);
QString textDate(const QVariant& d);

int ageYearsFrom(const QDate& from, const QDate& to);
int ageYears(const QVariant& dob, int default_years = -1);
double doubleSecondsFrom(const QDateTime& from, const QDateTime& to);

double msToSec(double ms);
int secToIntMs(double sec);
double secToMin(double sec);

}  // namespace datetime
