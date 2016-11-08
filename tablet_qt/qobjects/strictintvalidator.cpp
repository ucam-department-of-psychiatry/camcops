#include "strictintvalidator.h"
#include "lib/numericfunc.h"


StrictIntValidator::StrictIntValidator(int bottom, int top, bool allow_empty,
                                       QObject* parent) :
    QIntValidator(bottom, top, parent),
    m_allow_empty(allow_empty)
{
    if (top < bottom) {  // user has supplied them backwards
        setRange(top, bottom);  // reverse the range
    }
}



QValidator::State StrictIntValidator::validate(QString& s, int& pos) const
{
    Q_UNUSED(pos);
    return Numeric::validateInteger(s, locale(), bottom(), top(),
                                    m_allow_empty);
}
