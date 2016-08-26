#include "version.h"


namespace Version {
    // Amend these
    const unsigned int CAMCOPS_VERSION_MAJOR = 2;
    const unsigned int CAMCOPS_VERSION_MINOR = 0;
    const unsigned int CAMCOPS_VERSION_PATCH = 0;

    // Don't fiddle:
    static_assert(CAMCOPS_VERSION_MINOR < 100, "Minor version must be 0-99");
    static_assert(CAMCOPS_VERSION_PATCH < 100, "Patch version must be 0-99");
    const double CAMCOPS_VERSION_FLOAT = (
        CAMCOPS_VERSION_MAJOR +
        (double)CAMCOPS_VERSION_MINOR / 100 +
        (double)CAMCOPS_VERSION_PATCH / 10000
    );
    const QString CAMCOPS_VERSION_STRING = QString("%1.%2.%3")
            .arg(CAMCOPS_VERSION_MAJOR)
            .arg(CAMCOPS_VERSION_MINOR, 2, QChar('0'))
            .arg(CAMCOPS_VERSION_PATCH, 2, QChar('0'));
}
