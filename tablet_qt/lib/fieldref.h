#pragma once
#include <functional>
#include <QDate>
#include <QDateTime>
#include <QObject>
#include <QSharedPointer>
#include "field.h"
#include "databaseobject.h"


class FieldRef : public QObject
{
    // If a FieldRef didn't do signals, one would think:
    //
    // - Copy these things by value. They're small.
    // - Don't use references; the owning function is likely to have finished
    //   and made the reference become invalid.
    // - Don't bother with pointers; they have pointers within them anyway.
    // - The only prerequisite is that the things they point to outlast the
    //   lifetime of this object.
    //
    // However, it'd be helpful if they could do signals.
    // - In which case, they should be a QObject.
    // - In which case, you can't copy them.
    // - In which case, they should be managed by pointer.
    // - In which case, they should be managed by a QSharedPointer.
    Q_OBJECT
public:
    enum class FieldRefMethod {
        Invalid,
        Field,
        DatabaseObject,
        Functions,
    };
    typedef std::function<const QVariant&()> GetterFunction;
    typedef std::function<void(const QVariant&)> SetterFunction;
public:
    FieldRef();
    FieldRef(Field* p_field);
    FieldRef(DatabaseObject* p_dbobject, const QString& fieldname,
             bool autosave = true);
    FieldRef(const GetterFunction& getterfunc,
             const SetterFunction& setterfunc);
    bool valid() const;
    void setValue(const QVariant& value);
    QVariant value() const;
    bool valueBool() const;
    int valueInt() const;
    qlonglong valueLongLong() const;
    double valueDouble() const;
    QDateTime valueDateTime() const;
    QDate valueDate() const;
    QString valueString() const;
    QByteArray valueByteArray() const;

signals:
    void valueChanged(const QVariant& value) const;

protected:
    FieldRefMethod m_method;
    Field* m_p_field;

    DatabaseObject* m_p_dbobject;
    QString m_fieldname;
    bool m_autosave;

    GetterFunction m_getterfunc;
    SetterFunction m_setterfunc;
};


typedef QSharedPointer<FieldRef> FieldRefPtr;
