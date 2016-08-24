#include "fieldref.h"


FieldRef::FieldRef() :
    m_method(FieldRefMethod::Invalid),
    m_p_field(nullptr),
    m_p_dbobject(nullptr),
    m_fieldname(""),
    m_autosave(false),
    m_getterfunc(nullptr),
    m_setterfunc(nullptr)
{
}


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


bool FieldRef::valid() const
{
    switch (m_method) {
    case FieldRefMethod::Invalid:
        return false;
    case FieldRefMethod::Field:
        return m_p_field != nullptr;
    case FieldRefMethod::DatabaseObject:
        return m_p_dbobject != nullptr;
    case FieldRefMethod::Functions:
        return m_getterfunc != nullptr && m_setterfunc != nullptr;
    }
    // Shouldn't get here
    return false;
}


void FieldRef::setValue(const QVariant& value)
{
    // Try for user feedback before database save.
    // HOWEVER, we have to set the value first, because the signal may lead
    // to other code reading our value.

    // Store value
    switch (m_method) {
    case FieldRefMethod::Invalid:
        qWarning() << "Attempt to set invalid field reference";
        return;
    case FieldRefMethod::Field:
        m_p_field->setValue(value);
        break;
    case FieldRefMethod::DatabaseObject:
        m_p_dbobject->setValue(m_fieldname, value);
        break;
    case FieldRefMethod::Functions:
        m_setterfunc(value);
        break;
    }

    // Signal
    qDebug().nospace() << "FieldRef: emitting valueChanged: this=" << this
                       << ", value=" << value;
    emit valueChanged(value);

    // Delayed save (databases are slow):
    if (m_method == FieldRefMethod::DatabaseObject && m_autosave) {
        m_p_dbobject->save();
    }
}


QVariant FieldRef::value() const
{
    switch (m_method) {
    case FieldRefMethod::Invalid:
        qWarning() << "Attempt to get invalid field reference";
        return QVariant();
    case FieldRefMethod::Field:
        return m_p_field->value();
    case FieldRefMethod::DatabaseObject:
        return m_p_dbobject->value(m_fieldname);
    case FieldRefMethod::Functions:
    default:  // to remove warning
        return m_getterfunc();
    }
}


int FieldRef::valueInt() const
{
    QVariant v = value();
    return v.toInt();
}


qlonglong FieldRef::valueLongLong() const
{
    QVariant v = value();
    return v.toLongLong();
}


double FieldRef::valueDouble() const
{
    QVariant v = value();
    return v.toDouble();
}


bool FieldRef::valueBool() const
{
    QVariant v = value();
    return v.toBool();
}


QDateTime FieldRef::valueDateTime() const
{
    QVariant v = value();
    return v.toDateTime();
}


QDate FieldRef::valueDate() const
{
    QVariant v = value();
    return v.toDate();
}


QString FieldRef::valueString() const
{
    QVariant v = value();
    return v.toString();
}


QByteArray FieldRef::valueByteArray() const
{
    QVariant v = value();
    return v.toByteArray();
}
