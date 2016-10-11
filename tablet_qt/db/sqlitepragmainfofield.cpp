#include "sqlitepragmainfofield.h"
#include <QDebug>


QDebug operator<<(QDebug debug, const SqlitePragmaInfoField& info)
{
    debug.nospace()
        << "SqlitePragmaInfo(cid=" << info.cid
        << ", name=" << info.name
        << ", type=" << info.type
        << ", notnull=" << info.notnull
        << ", dflt_value=" << info.dflt_value
        << ", pk=" << info.pk << ")";
    return debug;
}
