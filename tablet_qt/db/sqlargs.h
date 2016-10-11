#pragma once
#include <QList>
#include <QString>
#include <QVariant>

using ArgList = QList<QVariant>;

struct SqlArgs {
public:
    SqlArgs(const QString& sql, const ArgList& args = ArgList()) :
        sql(sql), args(args) {}
public:
    QString sql;
    ArgList args;
};
