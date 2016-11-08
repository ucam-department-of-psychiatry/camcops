#include "strictint64validator.h"
#include <algorithm>
#include "lib/numericfunc.h"


StrictInt64Validator::StrictInt64Validator(bool allow_empty, QObject* parent) :
    QValidator(parent),
    m_allow_empty(allow_empty)
{
    b = 0;
    t = std::numeric_limits<qint64>::max();
}


StrictInt64Validator::StrictInt64Validator(qint64 bottom, qint64 top,
                                           bool allow_empty, QObject* parent) :
    QValidator(parent),
    m_allow_empty(allow_empty)
{
    if (top < bottom) {  // user has supplied them backwards
        std::swap(bottom, top);
    }
    b = bottom;
    t = top;
}


StrictInt64Validator::~StrictInt64Validator()
{
}


QValidator::State StrictInt64Validator::validate(QString& s, int& pos) const
{
    Q_UNUSED(pos);
    return Numeric::validateInteger(s, locale(), bottom(), top(),
                                    m_allow_empty);
}


void StrictInt64Validator::setBottom(qint64 bottom)
{
    setRange(bottom, top());
}


void StrictInt64Validator::setTop(qint64 top)
{
    setRange(bottom(), top);
}


void StrictInt64Validator::setRange(qint64 bottom, qint64 top)
{
    bool rangeChanged = false;
    if (b != bottom) {
        b = bottom;
        rangeChanged = true;
        emit bottomChanged(b);
    }

    if (t != top) {
        t = top;
        rangeChanged = true;
        emit topChanged(t);
    }

    if (rangeChanged) {
        emit changed();
    }
}
