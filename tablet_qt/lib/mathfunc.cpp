#include "mathfunc.h"


QVariant MathFunc::mean(QList<QVariant> values, bool ignore_null)
{
    double total = 0;
    int n = 0;
    for (auto value : values) {
        if (value.isNull()) {
            if (ignore_null) {
                continue;
            } else {
                return QVariant();  // mean of something including null is null
            }
        }
        n += 1;
        total += value.toDouble();
    }
    if (n == 0) {
        return QVariant();
    }
    return total / n;
}
