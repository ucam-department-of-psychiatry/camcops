#pragma once
#include <QList>
#include <QString>
#include <QVariant>


class NameValuePair
{
    // Encapsulates a single name/value pair.

public:
    NameValuePair(const QString& name, const QVariant& value);
    const QString& name() const;  // function access write-protects the members
    const QVariant& value() const;
protected:
    QString m_name;
    QVariant m_value;
};
