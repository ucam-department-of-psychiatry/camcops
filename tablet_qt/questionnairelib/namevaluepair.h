#pragma once
#include <QString>


template<typename T> class NameValuePair
{
public:
    NameValuePair(const QString& name, const T& value) :
        m_name(name),
        m_value(value)
    {}
    QString name() const { return m_name; }
    T value() const { return m_value; }
protected:
    QString m_name;
    T m_value;
};
