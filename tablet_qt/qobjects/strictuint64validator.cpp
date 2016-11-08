#include "strictuint64validator.h"
#include <algorithm>
#include "lib/numericfunc.h"


StrictUInt64Validator::StrictUInt64Validator(bool allow_empty,
                                             QObject* parent) :
    QValidator(parent),
    m_allow_empty(allow_empty)
{
    b = 0;
    t = std::numeric_limits<quint64>::max();
}


StrictUInt64Validator::StrictUInt64Validator(quint64 bottom, quint64 top,
                                             bool allow_empty,
                                             QObject* parent) :
    QValidator(parent),
    m_allow_empty(allow_empty)
{
    if (top < bottom) {  // user has supplied them backwards
        std::swap(bottom, top);
    }
    b = bottom;
    t = top;
}


StrictUInt64Validator::~StrictUInt64Validator()
{
}


QValidator::State StrictUInt64Validator::validate(QString& s, int& pos) const
{
    Q_UNUSED(pos);
    return Numeric::validateInteger(s, locale(), bottom(), top(),
                                    m_allow_empty);
}


void StrictUInt64Validator::setBottom(quint64 bottom)
{
    setRange(bottom, top());
}


void StrictUInt64Validator::setTop(quint64 top)
{
    setRange(bottom(), top);
}


void StrictUInt64Validator::setRange(quint64 bottom, quint64 top)
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
