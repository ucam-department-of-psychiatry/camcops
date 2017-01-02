/*
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


NameValueOptions NameValueOptions::makeNumbers(int first, int last, int step)
{
    NameValueOptions nvo;
    if (first < last && step > 0) {
        for (int i = first; i <= last; i += step) {
            nvo.addItem(NameValuePair{QString::number(i), i});
        }
    } else if (last < first && step < 0) {
        for (int i = first; i >= last; i += step) {
            nvo.addItem(NameValuePair{QString::number(i), i});
        }
    } else {
        UiFunc::stopApp("Bad arguments to NameValueOptions");
    }
    return nvo;
}
