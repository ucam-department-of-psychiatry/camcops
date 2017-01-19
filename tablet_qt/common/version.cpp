/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "version.h"
#include <QStringList>


Version::Version(unsigned int major, unsigned int minor, unsigned int patch) :
    m_valid(true),
    m_major(major),
    m_minor(minor),
    m_patch(patch)
{
    if (minor >= 100 || patch >= 100 ||
            (major == 0 && minor == 0 && patch == 0)) {
        qWarning() << Q_FUNC_INFO << "Refusing to create invalid version with:"
                   << "major" << major
                   << "minor" << minor
                   << "patch" << patch;
        m_valid = false;
        m_major = 0;
        m_minor = 0;
        m_patch = 0;
    }
}


bool Version::isValid() const
{
    return m_valid;
}


QString Version::toString() const
{
    return QString("%1.%2.%3")
            .arg(m_major)
            .arg(m_minor)
            .arg(m_patch);
    // NOT: arg(m_minor, 2, QChar('0'))
    // ... no leading zeros for semantic versioning; http://semver.org/
}



double Version::toFloat() const
{
    // Will be zero (the lowest possible value) for an invalid version.
    return m_major + (double)m_minor / 100 + (double)m_patch / 10000;
}


QString Version::toFloatString() const
{
    return QString::number(toFloat(), 'f', 4);
}


bool operator<(const Version& v1, const Version& v2)
{
    return v1.toFloat() < v2.toFloat();
}


bool operator<=(const Version& v1, const Version& v2)
{
    return v1.toFloat() <= v2.toFloat();
}


bool operator==(const Version& v1, const Version& v2)
{
    return v1.m_major == v2.m_major &&
           v1.m_minor == v2.m_minor &&
           v1.m_patch == v2.m_patch;
}


bool operator>=(const Version& v1, const Version& v2)
{
    return v1.toFloat() >= v2.toFloat();
}


bool operator>(const Version& v1, const Version& v2)
{
    return v1.toFloat() > v2.toFloat();
}


Version Version::makeInvalidVersion()
{
    return Version(0, 0, 0);
}


bool operator!=(const Version& v1, const Version& v2)
{
    return v1.m_major != v2.m_major ||
           v1.m_minor != v2.m_minor ||
           v1.m_patch != v2.m_patch;
}


Version Version::fromString(const QString& version_string)
{
    QStringList parts = version_string.split(".");
    if (parts.size() != 3) {
        return makeInvalidVersion();
    }
    int major, minor, patch;
    bool ok;
    major = parts.at(0).toInt(&ok);
    if (ok) {
        minor = parts.at(1).toInt(&ok);
    }
    if (ok) {
        patch = parts.at(2).toInt(&ok);
    }
    if (!ok) {
        return makeInvalidVersion();
    }
    Version v = Version(major, minor, patch);
    if (!v.isValid()) {
        qWarning() << "... invalid version string was:" << version_string;
    }
    return v;
}


QDebug operator<<(QDebug debug, const Version& v)
{
    debug.noquote() << v.toString();
    return debug;
}
