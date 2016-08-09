#pragma once
#include "lib/databaseobject.h"

extern const QString PATIENT_FK_FIELDNAME;


class TaskMainRecord : public DatabaseObject
{
public:
    TaskMainRecord(const QString& tablename,
                   const QSqlDatabase db,
                   bool is_anonymous,
                   bool has_clinician,
                   bool has_respondent);
};
