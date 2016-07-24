#pragma once
#include <QDateTime>

QString datetimeToIsoMs(const QDateTime& dt);
QString datetimeToIsoMsUtc(const QDateTime& dt);
QDateTime isoToDateTime(const QString& iso);
QDateTime now();
