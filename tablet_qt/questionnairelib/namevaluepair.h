#pragma once
#include <QList>
#include <QString>
#include <QVariant>


class NameValuePair
{
public:
    NameValuePair(const QString& name, const QVariant& value);
    QString name() const;  // function access write-protects the members
    QVariant value() const;
protected:
    QString m_name;
    QVariant m_value;
};


typedef QList<NameValuePair> NameValuePairList;


