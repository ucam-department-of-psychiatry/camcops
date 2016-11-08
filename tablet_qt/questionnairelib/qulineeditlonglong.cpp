#include "qulineeditlonglong.h"
#include "qobjects/strictint64validator.h"


QuLineEditLongLong::QuLineEditLongLong(FieldRefPtr fieldref,
                                       bool allow_empty) :
    QuLineEdit(fieldref),
    m_minimum(std::numeric_limits<qlonglong>::min()),
    m_maximum(std::numeric_limits<qlonglong>::max()),
    m_allow_empty(allow_empty)
{
    commonConstructor();
}


QuLineEditLongLong::QuLineEditLongLong(FieldRefPtr fieldref,
                                       qlonglong minimum,
                                       qlonglong maximum,
                                       bool allow_empty) :
    QuLineEdit(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_allow_empty(allow_empty)
{
    commonConstructor();
}


void QuLineEditLongLong::commonConstructor()
{
    setHint(QString("integer, range %1 to %2").arg(m_minimum).arg(m_maximum));
}


void QuLineEditLongLong::extraLineEditCreation(QLineEdit* editor)
{
    editor->setValidator(new StrictInt64Validator(m_minimum, m_maximum,
                                                  m_allow_empty, this));
}
