#include "debugfunc.h"
#include <QVariant>

// #define DEBUG_EVEN_GIANT_VARIANTS


void DebugFunc::debugConcisely(QDebug debug, const QVariant& value)
{
#ifdef DEBUG_EVEN_GIANT_VARIANTS
    debug << value;
#else
    switch (value.type()) {

    // Big things; don't show their actual value to the console
    case QVariant::ByteArray:
        debug << "<ByteArray>";
        break;

    // Normal things
    default:
        debug << value;
        break;
    }
#endif
}


void DebugFunc::debugConcisely(QDebug debug, const QList<QVariant>& values)
{
    debug << "(";
    int n = values.length();
    for (int i = 0; i < n; ++i) {
        if (i > 0) {
            debug << ", ";
        }
        debugConcisely(debug, values.at(i));
    }
    debug << ")";
}
