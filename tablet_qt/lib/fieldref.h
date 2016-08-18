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
    void set(const QVariant& value);
    QVariant get() const;
    bool getBool() const;
    int getInt() const;
    qlonglong getLongLong() const;
    double getDouble() const;
    QDateTime getDateTime() const;
    QDate getDate() const;
    QString getString() const;
    QByteArray getByteArray() const;

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
