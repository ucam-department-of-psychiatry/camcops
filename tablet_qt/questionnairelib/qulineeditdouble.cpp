#include "qulineeditdouble.h"
#include <limits>
#include <QDoubleValidator>
#include <QLineEdit>
#include "qobjects/strictdoublevalidator.h"
#include "questionnairelib/qulineeditinteger.h"


QuLineEditDouble::QuLineEditDouble(FieldRefPtr fieldref, bool allow_empty) :
    QuLineEdit(fieldref),
    m_minimum(std::numeric_limits<double>::min()),
    m_maximum(std::numeric_limits<double>::max()),
    m_decimals(2),
    m_allow_empty(allow_empty),
    m_strict_validator(true)
{
    setHint(QString("real number, %1 dp").arg(m_decimals));
}


QuLineEditDouble::QuLineEditDouble(FieldRefPtr fieldref, double minimum,
                                   double maximum, int decimals,
                                   bool allow_empty) :
    QuLineEdit(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_decimals(decimals),
    m_allow_empty(allow_empty),
    m_strict_validator(true)
{
    setHint(QString("real number, %1 to %2, %3 dp")
            .arg(m_minimum)
            .arg(m_maximum)
            .arg(m_decimals));
}


QuLineEditDouble* QuLineEditDouble::setStrictValidator(bool strict)
{
    m_strict_validator = strict;
    return this;
}


void QuLineEditDouble::extraLineEditCreation(QLineEdit* editor)
{
    if (m_strict_validator) {
        editor->setValidator(new StrictDoubleValidator(
            m_minimum, m_maximum, m_decimals, m_allow_empty, this));
    } else {
        editor->setValidator(new QDoubleValidator(
            m_minimum, m_maximum, m_decimals, this));
    }
}
