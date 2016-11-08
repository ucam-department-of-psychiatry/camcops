#pragma once
#include <QList>
#include <QVariant>


namespace MathFunc
{
    QVariant mean(QList<QVariant> values, bool ignore_null = false);
}
