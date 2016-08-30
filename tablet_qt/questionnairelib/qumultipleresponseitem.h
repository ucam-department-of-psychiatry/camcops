#pragma once
#include <QString>
#include "lib/fieldref.h"


class QuMultipleResponseItem
{
public:
    QuMultipleResponseItem(FieldRefPtr fieldref, const QString& text);
    FieldRefPtr fieldref() const;
    QString text() const;
protected:
    FieldRefPtr m_fieldref;
    QString m_text;
};
