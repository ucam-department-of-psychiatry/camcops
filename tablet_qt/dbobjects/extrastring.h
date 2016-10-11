#pragma once
#include "db/databaseobject.h"


class ExtraString : public DatabaseObject
{
public:
    // Specimen constructor:
    ExtraString(const QSqlDatabase& db);
    // String loading constructor:
    ExtraString(const QSqlDatabase& db,
                const QString& task,
                const QString& name);
    // String saving constructor:
    ExtraString(const QSqlDatabase& db,
                const QString& task,
                const QString& name,
                const QString& value);
    virtual ~ExtraString();
    QString value() const;
    bool exists() const;
    bool anyExist(const QString& task) const;  // sort-of static function
    void deleteAllExtraStrings();  // sort-of static function
protected:
    void commonConstructor();
    bool m_exists;
};
