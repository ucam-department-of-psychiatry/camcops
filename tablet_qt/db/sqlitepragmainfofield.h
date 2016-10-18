#pragma once
#include <QString>
#include <QVariant>


class SqlitePragmaInfoField {
public:
    // http://www.stroustrup.com/C++11FAQ.html#member-init
    int cid = -1;  // column ID
    QString name;
    QString type;
    bool notnull = false;
    QVariant dflt_value;
    bool pk = false;
public:
    friend QDebug operator<<(QDebug debug, const SqlitePragmaInfoField& info);
};
