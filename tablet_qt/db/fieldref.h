/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#pragma once
#include <functional>
#include <QDate>
#include <QDateTime>
#include <QImage>
#include <QObject>
#include <QPixmap>
#include <QSharedPointer>
#include "field.h"
#include "databaseobject.h"

class Blob;
class CamcopsApp;


class FieldRef : public QObject
{
    /*

If a FieldRef didn't do signals, one would think:
- Copy these things by value. They're small.
- Don't use references; the owning function is likely to have finished
  and made the reference become invalid.
- Don't bother with pointers; they have pointers within them anyway.
- The only prerequisite is that the things they point to outlast the
  lifetime of this object.

However, it'd be very helpful if they could do signals.
- In which case, they should be a QObject.
- In which case, you can't copy them.
- In which case, they should be managed by pointer.
- In which case, they should be managed by a QSharedPointer.

The FieldRef manages various kinds of indirection; see FieldRefMethod below.

    */

    Q_OBJECT
public:
    enum class FieldRefMethod {
        Invalid,
            // Dummy value indicating "not configured".
        Field,
            // Direct connection to a Field object.
        DatabaseObject,
            // Connection to a Field object belonging to a DatabaseObject.
        DatabaseObjectBlobField,
            // Connection to (a) a field in the DatabaseObject that stores the
            // PK of a BLOB record, and (b) a record in the BLOB table that
            // stores the actual blob, and references back to the
            // table/PK/field of the DatabaseObject in question.
        IsolatedBlobFieldForTesting,
            // As the name suggests.
        Functions,
            // Getter/setter functions, to allow the use e.g. of Questionnaires
            // (which use FieldRefs) together with arbitrary C++ objects, e.g.
            // for setting StoredVar objects.
        StoredVar,
            // Connection to a named StoredVar of the master app object.
        CachedStoredVar,
            // Connection to a named CachedStoredVar of the master app object.
    };
    using GetterFunction = std::function<QVariant()>;
    using SetterFunction = std::function<bool(const QVariant&)>;  // returns: changed?
public:
    // ========================================================================
    // Constructors
    // ========================================================================
    FieldRef();
    FieldRef(Field* p_field, bool mandatory);
    FieldRef(DatabaseObject* p_dbobject, const QString& fieldname,
             bool mandatory, bool autosave = true, bool blob = false,
             CamcopsApp* p_app = nullptr);
    FieldRef(QSharedPointer<Blob> blob, bool mandatory,
             bool disable_creation_warning = false);  // for widget testing only; specimen BLOB
    FieldRef(const GetterFunction& getterfunc,
             const SetterFunction& setterfunc,
             bool mandatory);
    FieldRef(CamcopsApp* app, const QString& storedvar_name,
             bool mandatory, bool cached);  // StoredVar

    // ========================================================================
    // Validity check
    // ========================================================================
    bool valid() const;

    // ========================================================================
    // Setting the value
    // ========================================================================
    bool setValue(const QVariant& value, const QObject* originator = nullptr);
    // ... originator is optional and used as a performance hint (see QSlider)
    void emitValueChanged(const QObject* originator = nullptr);  // for rare manual use

    // ========================================================================
    // Retrieving the value
    // ========================================================================
    QVariant value() const;
    bool isNull() const;
    bool valueBool() const;
    int valueInt() const;
    qlonglong valueLongLong() const;
    double valueDouble() const;
    QDateTime valueDateTime() const;
    QDate valueDate() const;
    QString valueString() const;
    QStringList valueStringList() const;
    QByteArray valueByteArray() const;
    QVector<int> valueVectorInt() const;

    // ========================================================================
    // BLOB-related functions, overridden by BlobFieldRef for higher performance
    // ========================================================================
    bool isBlob() const;
    virtual QImage image(bool* p_loaded = nullptr) const;
    virtual QPixmap pixmap(bool* p_loaded = nullptr) const;
    virtual void rotateImage(int angle_degrees_clockwise,
                             const QObject* originator = nullptr);
    virtual bool setImage(const QImage& image,
                          const QObject* originator = nullptr);
    virtual bool setRawImage(const QByteArray& data,
                             const QString& extension_without_dot,
                             const QString& mimetype,
                             const QObject* originator = nullptr);

    // ========================================================================
    // Completeness of input
    // ========================================================================
    bool mandatory() const;
    void setMandatory(bool mandatory, const QObject* originator = nullptr);
    // ... originator is optional and used as a performance hint (see QSlider)
    bool complete() const;  // not null?
    bool missingInput() const;  // block progress because (mandatory() && !complete())?

    // ========================================================================
    // Hints
    // ========================================================================
    void setHint(const QVariant& hint);
    QVariant getHint() const;

protected:
    void commonConstructor();
    bool signalSetValue(bool changed, const QObject* originator);
    void setFkToBlob();

signals:
    void valueChanged(const FieldRef* fieldref,
                      const QObject* originator) const;
    void mandatoryChanged(const FieldRef* fieldref,
                          const QObject* originator) const;
    // You should NOT cause a valueChanged() signal to be emitted whilst in a
    // mandatoryChanged() signal, but it's fine to emit mandatoryChanged()
    // signals (typically on other fields) whilst processing valueChanged()
    // signals.

protected:
    FieldRefMethod m_method;
    bool m_mandatory;

    Field* m_p_field;

    DatabaseObject* m_p_dbobject;
    QString m_fieldname;
    bool m_autosave;

    QSharedPointer<Blob> m_blob;

    GetterFunction m_getterfunc;
    SetterFunction m_setterfunc;

    CamcopsApp* m_app;
    QString m_storedvar_name;
    QVariant m_hint;
};
