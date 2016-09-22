#include "debugfunc.h"
#include <QDebug>
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
    QDebug d = debug.nospace();
    d << "(";
    int n = values.length();
    for (int i = 0; i < n; ++i) {
        if (i > 0) {
            d << ", ";
        }
        debugConcisely(d, values.at(i));
    }
    d << ")";
}


void DebugFunc::dumpQObject(QObject* obj)
{
    qDebug("----------------------------------------------------");
    qDebug("Widget name : %s", qPrintable(obj->objectName()));
    qDebug("Widget class: %s", obj->metaObject()->className());
    qDebug("\nObject info:");
    obj->dumpObjectInfo();
    qDebug("\nObject tree:");
    obj->dumpObjectTree();
    qDebug("----------------------------------------------------");
}
