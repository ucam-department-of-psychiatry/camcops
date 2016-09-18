#pragma once
#include <QDebug>
#include <QList>

class QVariant;


namespace DebugFunc
{
    void debugConcisely(QDebug debug, const QVariant& value);
    void debugConcisely(QDebug debug, const QList<QVariant>& values);
}
