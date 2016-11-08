#pragma once
#include <QString>

namespace DbConst {

    extern const QString PK_FIELDNAME;
    extern const QString MODIFICATION_TIMESTAMP_FIELDNAME;
    extern const QString CREATION_TIMESTAMP_FIELDNAME;
    extern const int NONEXISTENT_PK;

    extern const int NUMBER_OF_IDNUMS;
    extern const QString BAD_IDNUM_DESC;
    extern const QString UNKNOWN_IDNUM_DESC;
    extern const QString IDDESC_FIELD_FORMAT;
    extern const QString IDSHORTDESC_FIELD_FORMAT;

    bool isValidWhichIdnum(int which_idnum);
}
