#include "qulineeditdouble.h"
#include <QDoubleValidator>
#include <QLineEdit>
#include "widgets/strictdoublevalidator.h"
#include "qulineeditinteger.h"


QuLineEditDouble::QuLineEditDouble(FieldRefPtr fieldref) :
    QuLineEdit(fieldref),
    m_minimum(std::numeric_limits<int>::min()),
    m_maximum(std::numeric_limits<int>::max()),
    m_decimals(2),
    m_strict_validator(true)
{
}


QuLineEditDouble::QuLineEditDouble(FieldRefPtr fieldref, double minimum,
                                   double maximum, int decimals) :
    QuLineEdit(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_decimals(decimals),
    m_strict_validator(true)
{
}


QuLineEditDouble* QuLineEditDouble::setStrictValidator(bool strict)
{
    m_strict_validator = strict;
    return this;
}


void QuLineEditDouble::extraLineEditCreation(QLineEdit* editor)
{
    if (m_strict_validator) {
        editor->setValidator(new StrictDoubleValidator(m_minimum, m_maximum,
                                                       m_decimals, this));
    } else {
        editor->setValidator(new QDoubleValidator(m_minimum, m_maximum,
                                                  m_decimals, this));
    }
}
