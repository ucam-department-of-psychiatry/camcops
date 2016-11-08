#include "qulineeditinteger.h"
#include <limits>
#include <QIntValidator>
#include <QLineEdit>
#include "qobjects/strictintvalidator.h"


QuLineEditInteger::QuLineEditInteger(FieldRefPtr fieldref, bool allow_empty) :
    QuLineEdit(fieldref),
    m_minimum(std::numeric_limits<int>::min()),
    m_maximum(std::numeric_limits<int>::max()),
    m_allow_empty(allow_empty),
    m_strict_validator(true)
{
    setDefaultHint();
}


QuLineEditInteger::QuLineEditInteger(FieldRefPtr fieldref, int minimum,
                                     int maximum, bool allow_empty) :
    QuLineEdit(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_allow_empty(allow_empty),
    m_strict_validator(true)
{
    setDefaultHint();
}


void QuLineEditInteger::setDefaultHint()
{
    setHint(QString("integer, range %1 to %2").arg(m_minimum).arg(m_maximum));
}


QuLineEditInteger* QuLineEditInteger::setStrictValidator(bool strict)
{
    m_strict_validator = strict;
    return this;
}


void QuLineEditInteger::extraLineEditCreation(QLineEdit* editor)
{
    if (m_strict_validator) {
        editor->setValidator(new StrictIntValidator(m_minimum, m_maximum,
                                                    m_allow_empty, this));
    } else {
        editor->setValidator(new QIntValidator(m_minimum, m_maximum, this));
    }
}
