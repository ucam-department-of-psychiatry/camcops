#include "qumultipleresponseitem.h"

QuMultipleResponseItem::QuMultipleResponseItem(FieldRefPtr fieldref,
                                               const QString& text) :
    m_fieldref(fieldref),
    m_text(text)
{
    Q_ASSERT(m_fieldref);
}


FieldRefPtr QuMultipleResponseItem::fieldref() const
{
    return m_fieldref;
}


QString QuMultipleResponseItem::text() const
{
    return m_text;
}
