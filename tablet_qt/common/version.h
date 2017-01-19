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

#pragma once
#include <QDebug>
#include <QString>


class Version {
    // For semantic versioning: http://semver.org/
    // ... with the additional constraint of minor/patch versions being
    // limited to integers in the range 0-99.
public:
    Version(unsigned int major, unsigned int minor, unsigned int patch);
    unsigned int major() const;
    unsigned int minor() const;
    unsigned int patch() const;
    QString toString() const;
    double toFloat() const;
    QString toFloatString() const;
    bool isValid() const;
    friend bool operator<(const Version& v1, const Version& v2);
    friend bool operator<=(const Version& v1, const Version& v2);
    friend bool operator==(const Version& v1, const Version& v2);
    friend bool operator>=(const Version& v1, const Version& v2);
    friend bool operator>(const Version& v1, const Version& v2);
    friend bool operator!=(const Version& v1, const Version& v2);
    friend QDebug operator<<(QDebug debug, const Version& v);
    static Version fromString(const QString& version_string);
    static Version makeInvalidVersion();
protected:
    bool m_valid;
    unsigned int m_major;
    unsigned int m_minor;
    unsigned int m_patch;
};
