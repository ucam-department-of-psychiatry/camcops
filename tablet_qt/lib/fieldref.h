#pragma once
#include <functional>
#include <QDate>
#include <QDateTime>
#include <QSharedPointer>
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
    FieldRef(DatabaseObject* p_dbobject, const QString& fieldname,
             bool autosave = true);
    FieldRef(const GetterFunction& getterfunc,
             const SetterFunction& setterfunc);
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
