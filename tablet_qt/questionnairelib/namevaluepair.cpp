#include "namevaluepair.h"

NameValuePair::NameValuePair(const QString& name, const QVariant& value) :
    m_name(name),
    m_value(value)
{
}


QString NameValuePair::name() const
{
    return m_name;
}


QVariant NameValuePair::value() const
{
    return m_value;
}
