/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

// #define DEBUG_SET_VALUE
// #define DEBUG_SIGNALS
#define DEBUG_CHECK_VALID  // may be sensible to leave this on

#include "core/camcopsapp.h"
#include "common/globals.h"
#include "db/fieldref.h"
#include "dbobjects/blob.h"
#include "lib/convert.h"
#include "lib/debugfunc.h"
#include "lib/uifunc.h"


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
                   bool mandatory, bool autosave, bool blob,
                   CamcopsApp* p_app)
{
    commonConstructor();
    m_method = FieldRefMethod::DatabaseObject;
    m_mandatory = mandatory;
    m_p_dbobject = p_dbobject;
    m_fieldname = fieldname;
    m_autosave = autosave;

    if (blob) {
        if (p_app == nullptr) {
            uifunc::stopApp("Must pass p_app to FieldRef for BLOBs");
        }
        m_p_dbobject->save();  // ensure it has a PK
        m_method = FieldRefMethod::DatabaseObjectBlobField;
        m_blob = QSharedPointer<Blob>(new Blob(*p_app,
                                               p_dbobject->database(),
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


FieldRef::FieldRef(QSharedPointer<Blob> blob, bool mandatory)  // for widget testing only; specimen BLOB
{
    commonConstructor();
    m_method = FieldRefMethod::IsolatedBlobFieldForTesting;
    m_blob = blob;
    m_mandatory = mandatory;
    qWarning() << "FieldRef constructed with reference to specimen BLOB; FOR TESTING ONLY";
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
    QVariant temp = m_getterfunc();
}


FieldRef::FieldRef(CamcopsApp* app, const QString& storedvar_name,
                   bool mandatory, bool cached)
{
    commonConstructor();
    m_method = cached ? FieldRefMethod::CachedStoredVar
                      : FieldRefMethod::StoredVar;
    m_app = app;
    m_storedvar_name = storedvar_name;
    m_mandatory = mandatory;
}


void FieldRef::commonConstructor()
{
    m_method = FieldRefMethod::Invalid;
    m_mandatory = true;

    m_p_field = nullptr;

    m_p_dbobject = nullptr;
    m_fieldname = "";
    m_autosave = false;

    m_blob.clear();

    m_getterfunc = nullptr;
    m_setterfunc = nullptr;

    m_app = nullptr;
    m_storedvar_name = "";
}


bool FieldRef::valid() const
{
    switch (m_method) {

    case FieldRefMethod::Invalid:
        return false;

    case FieldRefMethod::Field:
        return m_p_field;

    case FieldRefMethod::DatabaseObject:
        return m_p_dbobject;

    case FieldRefMethod::DatabaseObjectBlobField:
        return m_p_dbobject && m_blob;

    case FieldRefMethod::IsolatedBlobFieldForTesting:
        return m_blob;

    case FieldRefMethod::Functions:
        return m_getterfunc && m_setterfunc;

    case FieldRefMethod::StoredVar:
    case FieldRefMethod::CachedStoredVar:
        return m_app && m_app->hasVar(m_storedvar_name);

    default:
        // Shouldn't get here
        qCritical() << Q_FUNC_INFO << "Bad method";
        return false;
    }
}


bool FieldRef::setValue(const QVariant& value, const QObject* originator)
{
    // Try for user feedback before database save.
    // HOWEVER, we have to set the value first, because the signal may lead
    // to other code reading our value.

#ifdef DEBUG_CHECK_VALID
    if (!valid()) {
        qWarning() << Q_FUNC_INFO << "Setting an invalid field";
        return false;
    }
#endif

#ifdef DEBUG_SET_VALUE
    {
        QDebug debug = qDebug().nospace();
        debug << Q_FUNC_INFO << " - value: ";
        debugfunc::debugConcisely(debug, value);
    }  // endl on destruction
#endif

    bool changed = true;

    // Store value
    switch (m_method) {

    case FieldRefMethod::Invalid:
        qWarning() << Q_FUNC_INFO << "Attempt to set invalid field reference";
        return false;

    case FieldRefMethod::Field:
        changed = m_p_field->setValue(value);
        break;

    case FieldRefMethod::DatabaseObject:
        changed = m_p_dbobject->setValue(m_fieldname, value);
        break;

    case FieldRefMethod::DatabaseObjectBlobField:
        changed = m_blob->setBlob(value, true);
        if (changed) {
            // it will ALREADY have saved (see setBlob); don't save it twice!
            m_p_dbobject->setValue(m_fieldname, m_blob->pkvalue(), true);
        }
        // ... (a) sets the BLOB, and (b) if the BLOB has changed or is being
        // set for the first time, sets the "original" field to contain the PK
        // of the BLOB entry.
        // ... and (c) we ensure that the setValue() command touches the
        // record, on the basis that a task has changed if one of its BLOBs has
        // changed, even if the BLOB PK has not changed.
        break;

    case FieldRefMethod::IsolatedBlobFieldForTesting:
        changed = m_blob->setBlob(value);
        break;

    case FieldRefMethod::Functions:
        changed = m_setterfunc(value);
        break;

    case FieldRefMethod::StoredVar:
        changed = m_app->setVar(m_storedvar_name, value);
        break;

    case FieldRefMethod::CachedStoredVar:
        changed = m_app->setCachedVar(m_storedvar_name, value);
        break;

    default:
        qCritical() << Q_FUNC_INFO << "Bad method";
        break;
    }

    return signalSetValue(changed, originator);
}


bool FieldRef::signalSetValue(bool changed, const QObject* originator)
{
    // Signal
    if (changed) {
#ifdef DEBUG_SIGNALS
        {
            QDebug debugns = qDebug().nospace();
            debugns << Q_FUNC_INFO << " - emitting valueChanged: this="
                    << this << ", value=";
            debugfunc::debugConcisely(debugns, value);
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

    return changed;
}


void FieldRef::emitValueChanged(const QObject* originator)
{
    emit valueChanged(this, originator);
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
    case FieldRefMethod::IsolatedBlobFieldForTesting:
        return m_blob->blobVariant();

    case FieldRefMethod::Functions:
        return m_getterfunc();

    case FieldRefMethod::StoredVar:
        return m_app->var(m_storedvar_name);

    case FieldRefMethod::CachedStoredVar:
        return m_app->getCachedVar(m_storedvar_name);

    default:  // to remove warning
        qCritical() << Q_FUNC_INFO << "Bad method";
        return QVariant();
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


QStringList FieldRef::valueStringList() const
{
    QVariant v = value();
    return v.toStringList();
}


QByteArray FieldRef::valueByteArray() const
{
    QVariant v = value();
    return v.toByteArray();
}


bool FieldRef::isBlob() const
{
    return (m_method == FieldRefMethod::DatabaseObjectBlobField ||
            m_method == FieldRefMethod::IsolatedBlobFieldForTesting) && m_blob;
}


QVector<int> FieldRef::valueVectorInt() const
{
    QVariant v = value();
    return convert::qVariantToIntVector(v);
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
    QVariant v = value();
    if (v.isNull()) {
        return false;
    }
    if (v.toString().isEmpty()) {
        return false;
    }
    return true;
}


bool FieldRef::missingInput() const
{
    return mandatory() && !complete();
}


void FieldRef::setHint(const QVariant& hint)
{
    m_hint = hint;
}


QVariant FieldRef::getHint() const
{
    return m_hint;
}


void FieldRef::setMandatory(bool mandatory, const QObject* originator)
{
    if (mandatory == m_mandatory) {
        return;
    }
    m_mandatory = mandatory;
#ifdef DEBUG_SIGNALS
    qDebug().nospace() << Q_FUNC_INFO << "- emitting mandatoryChanged: this="
                       << this << ", mandatory=" << mandatory;
#endif
    emit mandatoryChanged(this, originator);
}
