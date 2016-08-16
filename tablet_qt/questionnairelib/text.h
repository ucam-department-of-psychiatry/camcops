#pragma once
#include <QPointer>
#include <QString>
#include "lib/fieldref.h"
#include "element.h"


class Text : public Element
{
public:
    Text(const QString& text);
    Text(FieldRefPtr fieldref);
    Text* big(bool big = true);
    Text* bold(bool bold = true);
    Text* italic(bool italic = true);
    Text* setFormat(Qt::TextFormat format);
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
