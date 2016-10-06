#include "patient.h"
#include "common/dbconstants.h"

const QString PATIENT_TABLE = "patient";

const QString FORENAME_FIELD = "forename";
const QString SURNAME_FIELD = "surname";
const QString DOB_FIELD = "dob";
const QString SEX_FIELD = "sex";
const QString ADDRESS_FIELD = "address";
const QString GP_FIELD = "gp";
const QString OTHER_FIELD = "other";

const QString IDNUM_FIELD_FORMAT = "idnum%1";
const QString IDDESC_FIELD_FORMAT = "iddesc%1";
const QString IDSHORTDESC_FIELD_FORMAT = "idshortdesc%1";


Patient::Patient(const QSqlDatabase& db, int load_pk) :
    DatabaseObject(db, PATIENT_TABLE, DbConst::PK_FIELDNAME, true, true)
{
    // ------------------------------------------------------------------------
    // Define fields
    // ------------------------------------------------------------------------
    addField(FORENAME_FIELD, QVariant::String);
    addField(SURNAME_FIELD, QVariant::String);
    addField(DOB_FIELD, QVariant::String);
    addField(SEX_FIELD, QVariant::String);
    addField(ADDRESS_FIELD, QVariant::String);
    addField(GP_FIELD, QVariant::String);
    addField(OTHER_FIELD, QVariant::String);
    for (int n = 1; n <= DbConst::NUMBER_OF_IDNUMS; ++n) {
        addField(IDNUM_FIELD_FORMAT.arg(n), QVariant::ULongLong);
        // Information for these two comes from the server:
        addField(IDSHORTDESC_FIELD_FORMAT.arg(n), QVariant::String);
        addField(IDDESC_FIELD_FORMAT.arg(n), QVariant::String);
    }

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ***
