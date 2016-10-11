#pragma once
#include "db/databaseobject.h"


class Patient : public DatabaseObject
{
public:
    Patient(const QSqlDatabase& db,
            int load_pk = DbConst::NONEXISTENT_PK);
    // ***
};
