#pragma once
#include <QPointer>
#include <QString>
#include "lib/fieldref.h"
#include "quelement.h"


class QuText : public QuElement
{
public:
    QuText(const QString& text);
    QuText(FieldRefPtr fieldref);
    QuText* big(bool big = true);
    QuText* bold(bool bold = true);
    QuText* italic(bool italic = true);
    QuText* setFormat(Qt::TextFormat format);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected:
    QString m_text;
    FieldRefPtr m_fieldref;
    bool m_big;
    bool m_bold;
    bool m_italic;
    Qt::TextFormat m_text_format;
};
