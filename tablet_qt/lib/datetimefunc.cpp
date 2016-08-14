#include "datetimefunc.h"
#include <QTimeZone>

const QString SHORT_DATETIME_FORMAT = "yyyy-MM-dd HH:mm";


// http://stackoverflow.com/questions/21976264/qt-isodate-formatted-date-time-including-timezone

QString datetimeToIsoMs(const QDateTime& dt)
{
    // An ISO-8601 format preserving millisecond accuracy and timezone.
    // Equivalent in moment.js: thing.format("YYYY-MM-DDTHH:mm:ss.SSSZ")
    // Example: '2016-06-02T10:04:03.588+01:00'
    // Here we also allow 'Z' for UTC.

    // In Qt, BEWARE:
    //      dt;  // QDateTime(2016-06-02 10:28:06.708 BST Qt::TimeSpec(LocalTime))
    //      dt.toString(Qt::ISODate);  // "2016-06-02T10:28:06" -- DROPS timezone
    if (!dt.isValid()) {
        return "";
    }
    QString localtime = dt.toString("yyyy-MM-ddTHH:mm:ss.zzz");
    int offset_from_utc_s = dt.offsetFromUtc();
    // FOR TESTING: offsetFromUtcSec = -(3600 * 2.5);
    QString tzinfo;
    if (offset_from_utc_s == 0) {
        tzinfo = "Z";
    } else {
        QString sign = offset_from_utc_s < 0 ? "-" : "+";
        offset_from_utc_s = abs(offset_from_utc_s);
        int hours = offset_from_utc_s / 3600;
        int minutes = (offset_from_utc_s % 3600) / 60;
        tzinfo += QString("%1%2:%3").arg(sign)
            .arg(hours, 2, 10, QChar('0'))
            .arg(minutes, 2, 10, QChar('0'));
        // http://stackoverflow.com/questions/2618414/convert-an-int-to-a-qstring-with-zero-padding-leading-zeroes
    }
    return localtime + tzinfo;
}


QString datetimeToIsoMsUtc(const QDateTime& dt)
{
    QDateTime utc_dt = dt.toTimeSpec(Qt::UTC);
    return datetimeToIsoMs(utc_dt);
}


QDateTime isoToDateTime(const QString& iso)
{
    return QDateTime::fromString(iso, Qt::ISODate);
}


QDateTime now()
{
    return QDateTime::currentDateTime();
}


QString shortDateTime(const QDateTime& dt)
{
    return dt.toString(SHORT_DATETIME_FORMAT);
}
