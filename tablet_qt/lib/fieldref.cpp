#define DEBUG_SET_VALUE
// #define DEBUG_SIGNALS
#define DEBUG_CHECK_VALID

#include "fieldref.h"
#include "dbobjects/blob.h"
#include "lib/convert.h"
#include "lib/debugfunc.h"


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
                   bool mandatory, bool autosave, bool blob)
{
    commonConstructor();
    m_method = FieldRefMethod::DatabaseObject;
    m_mandatory = mandatory;
    m_p_dbobject = p_dbobject;
    m_fieldname = fieldname;
    m_autosave = autosave;

    m_blob_redirect = blob;
    if (blob) {
        m_p_dbobject->save();  // ensure it has a PK
        m_method = FieldRefMethod::DatabaseObjectBlobField;
        m_blob = QSharedPointer<Blob>(new Blob(p_dbobject->database(),
                                               p_dbobject->tablename(),
                                               p_dbobject->pkvalue().toInt(),
                                               fieldname));
        if (!m_autosave) {
            qWarning() << Q_FUNC_INFO
                       << "BLOB mode selected; enforcing autosave = true";
            m_autosave = true;
        }
    }
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

    m_blob_redirect = false;
    m_blob = QSharedPointer<Blob>(nullptr);

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
    case FieldRefMethod::DatabaseObjectBlobField:
        return m_p_dbobject != nullptr && m_blob != nullptr;
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

#ifdef DEBUG_CHECK_VALID
    if (!valid()) {
        qDebug() << Q_FUNC_INFO << "Setting an invalid field";
        return;
    }
#endif

#ifdef DEBUG_SET_VALUE
    {
        QDebug debug = qDebug().nospace();
        debug << Q_FUNC_INFO << " - value: ";
        DebugFunc::debugConcisely(debug, value);
    }  // endl on destruction
#endif

    bool changed = true;

    // Store value
    switch (m_method) {
    case FieldRefMethod::Invalid:
        qWarning() << Q_FUNC_INFO << "Attempt to set invalid field reference";
        return;
    case FieldRefMethod::Field:
        changed = m_p_field->setValue(value);
        break;
    case FieldRefMethod::DatabaseObject:
        changed = m_p_dbobject->setValue(m_fieldname, value);
        break;
    case FieldRefMethod::DatabaseObjectBlobField:
        changed = m_blob->setBlob(value, true);
        if (changed) {
            m_blob->save();  // ensure it has a PK
            m_p_dbobject->setValue(m_fieldname, m_blob->pkvalue());
        }
        // ... (a) sets the BLOB, and (b) if the BLOB has changed or is being
        // set for the first time, sets the "original" field to contain the PK
        // of the BLOB entry.
        break;
    case FieldRefMethod::Functions:
        changed = m_setterfunc(value);
        break;
    }

    // Signal
    if (changed) {
#ifdef DEBUG_SIGNALS
        {
            QDebug debugns = qDebug().nospace();
            debugns << Q_FUNC_INFO << " - emitting valueChanged: this="
                    << this << ", value=";
            DebugFunc::debugConcisely(debugns, value);
        }  // endl on destruction
#endif
        emit valueChanged(this, originator);
    }

    // Delayed save (databases are slow, plus knock-on changes from our
    // valueChanged signal might also alter this record):
    if (m_autosave && (m_method == FieldRefMethod::DatabaseObject ||
                       m_method == FieldRefMethod::DatabaseObjectBlobField)) {
        m_p_dbobject->save();
    }
}


void FieldRef::setValue(const QImage& image, const QObject* originator)
{
    setValue(Convert::imageToVariant(image), originator);
}


QVariant FieldRef::value() const
{
#ifdef DEBUG_CHECK_VALID
    if (!valid()) {
        return QVariant();
    }
#endif
    switch (m_method) {
    case FieldRefMethod::Invalid:
        qWarning() << Q_FUNC_INFO << "Attempt to get invalid field reference";
        return QVariant();
    case FieldRefMethod::Field:
        return m_p_field->value();
    case FieldRefMethod::DatabaseObject:
        return m_p_dbobject->value(m_fieldname);
    case FieldRefMethod::DatabaseObjectBlobField:
        return m_blob->blobVariant();
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
