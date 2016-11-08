#include "qulineeditulonglong.h"
#include <QDebug>
#include "qobjects/strictuint64validator.h"


QuLineEditULongLong::QuLineEditULongLong(FieldRefPtr fieldref,
                                         bool allow_empty) :
    QuLineEdit(fieldref),
    m_minimum(std::numeric_limits<qulonglong>::min()),
    m_maximum(std::numeric_limits<qulonglong>::max()),
    m_allow_empty(allow_empty)
{
    commonConstructor();
}


QuLineEditULongLong::QuLineEditULongLong(FieldRefPtr fieldref,
                                         qulonglong minimum,
                                         qulonglong maximum,
                                         bool allow_empty) :
    QuLineEdit(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_allow_empty(allow_empty)
{
    commonConstructor();
}


void QuLineEditULongLong::commonConstructor()
{
    qWarning() << "SQLite v3 does not properly support unsigned 64-bit "
                  "integers (https://www.sqlite.org/datatype3.html); "
                  "use signed if possible";
    // see also http://jakegoulding.com/blog/2011/02/06/sqlite-64-bit-integers/
    setHint(QString("integer, range %1 to %2").arg(m_minimum).arg(m_maximum));
}


void QuLineEditULongLong::extraLineEditCreation(QLineEdit* editor)
{
    editor->setValidator(new StrictUInt64Validator(m_minimum, m_maximum,
                                                   m_allow_empty, this));
}
