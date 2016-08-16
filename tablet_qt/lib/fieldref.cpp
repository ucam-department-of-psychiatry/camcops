#include "fieldref.h"


FieldRef::FieldRef(Field* p_field) :
    m_method(FieldRefMethod::Field),
    m_p_field(p_field),
    m_p_dbobject(nullptr),
    m_fieldname(""),
    m_autosave(false),
    m_getterfunc(nullptr),
    m_setterfunc(nullptr)
{
}


FieldRef::FieldRef(DatabaseObject* p_dbobject, const QString& fieldname,
                   bool autosave) :
    m_method(FieldRefMethod::DatabaseObject),
    m_p_field(nullptr),
    m_p_dbobject(p_dbobject),
    m_fieldname(fieldname),
    m_autosave(autosave),
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
    m_autosave(false),
    m_getterfunc(getterfunc),
    m_setterfunc(setterfunc)
{
}


void FieldRef::set(const QVariant& value)
{
    switch (m_method) {
    case FieldRefMethod::Field:
        m_p_field->setValue(value);
        break;
    case FieldRefMethod::DatabaseObject:
        m_p_dbobject->setValue(m_fieldname, value);
        if (m_autosave) {
            m_p_dbobject->save();
        }
        break;
    case FieldRefMethod::Functions:
        m_setterfunc(value);
        break;
    }
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


int FieldRef::getInt() const
{
    QVariant value = get();
    return value.toInt();
}


qlonglong FieldRef::getLongLong() const
{
    QVariant value = get();
    return value.toLongLong();
}


double FieldRef::getDouble() const
{
    QVariant value = get();
    return value.toDouble();
}


bool FieldRef::getBool() const
{
    QVariant value = get();
    return value.toBool();
}


QDateTime FieldRef::getDateTime() const
{
    QVariant value = get();
    return value.toDateTime();
}


QDate FieldRef::getDate() const
{
    QVariant value = get();
    return value.toDate();
}


QString FieldRef::getString() const
{
    QVariant value = get();
    return value.toString();
}
