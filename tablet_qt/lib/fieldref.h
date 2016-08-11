#pragma once
#include <functional>
#include "field.h"
#include "databaseobject.h"


enum class FieldRefMethod {
    Field,
    DatabaseObject,
    Functions,
};


class FieldRef
{
public:
    typedef std::function<const QVariant&()> GetterFunction;
    typedef std::function<void(const QVariant&)> SetterFunction;
public:
    FieldRef(Field* p_field);
    FieldRef(DatabaseObject* p_dbobject, const QString& fieldname);
    FieldRef(const GetterFunction& getterfunc,
             const SetterFunction& setterfunc);
    QVariant get() const;
    void set(const QVariant& value);

protected:
    FieldRefMethod m_method;
    Field* m_p_field;
    DatabaseObject* m_p_dbobject;
    QString m_fieldname;
    GetterFunction m_getterfunc;
    SetterFunction m_setterfunc;
};
