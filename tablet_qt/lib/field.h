#pragma once
#include <QDebug>
#include <QVariant>


class Field
{
public:
    Field();
    Field(const QString& name, QVariant::Type type,
          bool mandatory = false, bool unique = false, bool pk = false);
    Field& setPk(bool pk);
    Field& setUnique(bool unique);
    Field& setMandatory(bool pk);
    Field& setDefaultValue(QVariant value);
    QString name() const;
    bool isPk() const;
    bool isUnique() const;
    bool isMandatory() const;
    QString sqlColumnDef() const;
    QString sqlColumnType() const;
    QVariant value() const;
    bool setValue(const QVariant& value);  // returns: dirty?
    bool nullify();  // returns: dirty?
    bool isNull() const;
    void setFromDatabaseValue(const QVariant& db_value); // SQLite -> C++
    QVariant getDatabaseValue() const; // C++ -> SQLite
    bool isDirty() const;
    void setDirty();
    void clearDirty();
    friend QDebug operator<<(QDebug debug, const Field& f);

protected:
    QString m_name;
    QVariant::Type m_type;
    bool m_pk;
    bool m_unique;
    bool m_mandatory;
    bool m_set;
    bool m_dirty;
    QVariant m_default_value;  // C++, not database
    QVariant m_value;
};
