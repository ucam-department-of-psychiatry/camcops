#pragma once
#include <QString>
#include <QVariant>


class QuThermometerItem {
public:
    QuThermometerItem();
    QuThermometerItem(const QString& active_filename,
                      const QString& inactive_filename,
                      const QString& text,
                      const QVariant& value);
    QString activeFilename() const;
    QString inactiveFilename() const;
    QString text() const;
    QVariant value() const;
protected:
    QString m_active_filename;
    QString m_inactive_filename;
    QString m_text;
    QVariant m_value;
};
