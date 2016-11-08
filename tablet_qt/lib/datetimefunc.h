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
}
