#include "qulineeditinteger.h"
#include <QIntValidator>
#include <QLineEdit>
#include "widgets/strictintvalidator.h"


QuLineEditInteger::QuLineEditInteger(FieldRefPtr fieldref) :
    QuLineEdit(fieldref),
    m_minimum(std::numeric_limits<int>::min()),
    m_maximum(std::numeric_limits<int>::max()),
    m_strict_validator(true)
{
    setHint("integer");
}


QuLineEditInteger::QuLineEditInteger(FieldRefPtr fieldref, int minimum,
                                     int maximum) :
    QuLineEdit(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_strict_validator(true)
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
        editor->setValidator(new StrictIntValidator(m_minimum, m_maximum, this));
    } else {
        editor->setValidator(new QIntValidator(m_minimum, m_maximum, this));
    }
}
