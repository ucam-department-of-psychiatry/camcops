#include "quthermometeritem.h"


QuThermometerItem::QuThermometerItem()
{
}


QuThermometerItem::QuThermometerItem(const QString& active_filename,
                                     const QString& inactive_filename,
                                     const QString& text,
                                     const QVariant& value) :
    m_active_filename(active_filename),
    m_inactive_filename(inactive_filename),
    m_text(text),
    m_value(value)
{
    Q_ASSERT(!m_value.isNull());
}


QString QuThermometerItem::activeFilename() const
{
    return m_active_filename;
}


QString QuThermometerItem::inactiveFilename() const
{
    return m_inactive_filename;
}


QString QuThermometerItem::text() const
{
    return m_text;
}


QVariant QuThermometerItem::value() const
{
    return m_value;
}
