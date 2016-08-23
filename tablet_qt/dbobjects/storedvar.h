#pragma once
#include "lib/databaseobject.h"


class StoredVar : public DatabaseObject
{
public:
    StoredVar(const QSqlDatabase& db,
              const QString& name = "",  // empty for a specimen
              QVariant::Type type = QVariant::Int,
              QVariant default_value = QVariant());
    virtual ~StoredVar();
    void setValue(const QVariant& value);
    QVariant value() const;
protected:
    // http://stackoverflow.com/questions/411103/function-with-same-name-but-different-signature-in-derived-class
    // http://stackoverflow.com/questions/1628768/why-does-an-overridden-function-in-the-derived-class-hide-other-overloads-of-the
    using DatabaseObject::setValue;
    using DatabaseObject::value;
protected:
    QString m_name;
    QVariant::Type m_type;
    QString m_value_fieldname;
};
