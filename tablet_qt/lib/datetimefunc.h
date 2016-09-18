#pragma once
#include <QDateTime>

namespace DateTime {

    extern const QString SHORT_DATETIME_FORMAT;

    QString datetimeToIsoMs(const QDateTime& dt);
    QString datetimeToIsoMsUtc(const QDateTime& dt);
    QDateTime isoToDateTime(const QString& iso);
    QDateTime now();
    QString shortDateTime(const QDateTime& dt);
}
