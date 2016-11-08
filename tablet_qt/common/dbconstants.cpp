#include "dbconstants.h"
#include <QDebug>


namespace DbConst {

    const QString PK_FIELDNAME("id");
    const QString MODIFICATION_TIMESTAMP_FIELDNAME("when_last_modified");
    const QString CREATION_TIMESTAMP_FIELDNAME("when_created");
    const int NONEXISTENT_PK = -1;

    const int NUMBER_OF_IDNUMS = 8;
    const QString BAD_IDNUM_DESC("<bad_idnum>");
    const QString UNKNOWN_IDNUM_DESC("<ID_number_%1>");
    const QString IDDESC_FIELD_FORMAT("iddesc%1");
    const QString IDSHORTDESC_FIELD_FORMAT("idshortdesc%1");
}


bool DbConst::isValidWhichIdnum(int which_idnum)
{
    bool valid = which_idnum >= 1 && which_idnum <= NUMBER_OF_IDNUMS;
    if (!valid) {
        qWarning() << Q_FUNC_INFO << "bad idnum" << which_idnum;
    }
    return valid;
}
