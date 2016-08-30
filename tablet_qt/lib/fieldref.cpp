#define DEBUG_SET_VALUE
// #define DEBUG_SIGNALS

#include "fieldref.h"


FieldRef::FieldRef()
{
    commonConstructor();
}


FieldRef::FieldRef(Field* p_field, bool mandatory)
{
    commonConstructor();
    m_method = FieldRefMethod::Field;
    m_mandatory = mandatory;
    m_p_field = p_field;
}


FieldRef::FieldRef(DatabaseObject* p_dbobject, const QString& fieldname,
                   bool mandatory, bool autosave)
{
    commonConstructor();
    m_method = FieldRefMethod::DatabaseObject;
    m_mandatory = mandatory;
    m_p_dbobject = p_dbobject;
    m_fieldname = fieldname;
    m_autosave = autosave;
}


FieldRef::FieldRef(const GetterFunction& getterfunc,
                   const SetterFunction& setterfunc,
                   bool mandatory)
{
    commonConstructor();
    m_method = FieldRefMethod::Functions;
    m_mandatory = mandatory;
    m_getterfunc = getterfunc;
    m_setterfunc = setterfunc;
}


void FieldRef::commonConstructor()
{
    m_method = FieldRefMethod::Invalid;
    m_mandatory = true;

    m_p_field = nullptr;

    m_p_dbobject = nullptr;
    m_fieldname = "";
    m_autosave = false;

    m_getterfunc = nullptr;
    m_setterfunc = nullptr;
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


void FieldRef::setValue(const QVariant& value, const QObject* originator)
{
    // Try for user feedback before database save.
    // HOWEVER, we have to set the value first, because the signal may lead
    // to other code reading our value.

#ifdef DEBUG_SET_VALUE
    qDebug() << Q_FUNC_INFO << "- value:" << value;
#endif

    // Store value
    switch (m_method) {
    case FieldRefMethod::Invalid:
        qWarning() << Q_FUNC_INFO << "Attempt to set invalid field reference";
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
#ifdef DEBUG_SIGNALS
    qDebug().nospace() << Q_FUNC_INFO << "- emitting valueChanged: this="
                       << this << ", value=" << value;
#endif
    emit valueChanged(this, originator);

    // Delayed save (databases are slow, plus knock-on changes from our
    // valueChanged signal might also alter this record):
    if (m_method == FieldRefMethod::DatabaseObject && m_autosave) {
        m_p_dbobject->save();
    }
}


QVariant FieldRef::value() const
{
    switch (m_method) {
    case FieldRefMethod::Invalid:
        qWarning() << Q_FUNC_INFO << "Attempt to get invalid field reference";
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


bool FieldRef::isNull() const
{
    QVariant v = value();
    return v.isNull();
}


bool FieldRef::mandatory() const
{
    return m_mandatory;
}


bool FieldRef::complete() const
{
    return !value().isNull();
}


bool FieldRef::missingInput() const
{
    return mandatory() && !complete();
}


void FieldRef::setMandatory(bool mandatory, const QObject* originator)
{
    if (mandatory == m_mandatory) {
        return;
    }
    m_mandatory = mandatory;
#ifdef DEBUG_SIGNALS
    qDebug().nospace() << Q_FUNC_INFO << "- emitting setMandatory: this="
                       << this << ", mandatory=" << mandatory;
#endif
    emit mandatoryChanged(this, originator);
}
