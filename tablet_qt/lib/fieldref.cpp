#include "fieldref.h"


FieldRef::FieldRef(Field* p_field) :
    m_method(FieldRefMethod::Field),
    m_p_field(p_field),
    m_p_dbobject(nullptr),
    m_fieldname(""),
    m_getterfunc(nullptr),
    m_setterfunc(nullptr)
{
}


FieldRef::FieldRef(DatabaseObject* p_dbobject, const QString& fieldname) :
    m_method(FieldRefMethod::DatabaseObject),
    m_p_field(nullptr),
    m_p_dbobject(p_dbobject),
    m_fieldname(fieldname),
    m_getterfunc(nullptr),
    m_setterfunc(nullptr)
{
}


FieldRef::FieldRef(const GetterFunction& getterfunc,
                   const SetterFunction& setterfunc) :
    m_method(FieldRefMethod::Functions),
    m_p_field(nullptr),
    m_p_dbobject(nullptr),
    m_fieldname(""),
    m_getterfunc(getterfunc),
    m_setterfunc(setterfunc)
{
}


QVariant FieldRef::get() const
{
    switch (m_method) {
    case FieldRefMethod::Field:
        return m_p_field->value();
    case FieldRefMethod::DatabaseObject:
        return m_p_dbobject->getValue(m_fieldname);
    case FieldRefMethod::Functions:
    default:  // to remove warning
        return m_getterfunc();
    }
}

void FieldRef::set(const QVariant& value)
{
    switch (m_method) {
    case FieldRefMethod::Field:
        m_p_field->setValue(value);
    case FieldRefMethod::DatabaseObject:
        m_p_dbobject->setValue(m_fieldname, value);
    case FieldRefMethod::Functions:
        m_setterfunc(value);
    }
}
