#include "namevalueoptions.h"
#include <QDebug>
#include "common/random.h"
#include "lib/uifunc.h"


NameValueOptions::NameValueOptions()
{
}


NameValueOptions::NameValueOptions(std::initializer_list<NameValuePair> options) :
    m_options(options)
{
}


void NameValueOptions::addItem(const NameValuePair& nvp)
{
    m_options.append(nvp);
}


int NameValueOptions::size() const
{
    return m_options.size();
}


const NameValuePair& NameValueOptions::at(int index) const
{
    return m_options.at(index);
}


int NameValueOptions::indexFromName(const QString& name) const
{
    for (int i = 0; i < m_options.size(); ++i) {
        if (m_options.at(i).name() == name) {
            return i;
        }
    }
    return -1;
}


int NameValueOptions::indexFromValue(const QVariant& value) const
{
    if (value.isNull()) {
        return -1;
    }
    for (int i = 0; i < m_options.size(); ++i) {
        if (m_options.at(i).value() == value) {
            return i;
        }
    }
    return -1;
}


void NameValueOptions::validateOrDie()
{
    QList<QVariant> values;
    for (int i = 0; i < m_options.size(); ++i) {
        const NameValuePair& nvp = m_options.at(i);
        const QVariant& v = nvp.value();
        if (values.contains(v)) {
            qCritical() << Q_FUNC_INFO
                        << "Name/value pair contains duplicate value:" << v;
            UiFunc::stopApp("NameValueOptions::validateOrDie: Duplicate "
                            "name/value pair for name: " + nvp.name());
        }
        values.append(v);
    }
}


bool NameValueOptions::validIndex(int index) const
{
    return index >= 0 && index < m_options.size();
}


void NameValueOptions::shuffle()
{
    std::shuffle(m_options.begin(), m_options.end(), Random::rng);
}


QString NameValueOptions::name(int index) const
{
    if (!validIndex(index)) {
        return "";
    }
    return m_options.at(index).name();
}


QVariant NameValueOptions::value(int index) const
{
    if (!validIndex(index)) {
        return QVariant();
    }
    return m_options.at(index).value();
}
