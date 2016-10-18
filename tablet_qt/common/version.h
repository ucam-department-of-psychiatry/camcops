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
    double toFloat() const;
    QString toString() const;
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
