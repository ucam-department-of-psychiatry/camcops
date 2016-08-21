#pragma once
#include "lib/fieldref.h"
#include "quelement.h"


class QuText : public Cloneable<QuElement, QuText>
{
public:
    QuText(const QString& text = "");
    QuText(FieldRefPtr fieldref);
    QuText& big(bool big = true);
    QuText& bold(bool bold = true);
    QuText& italic(bool italic = true);
    QuText& warning(bool warning = true);
    QuText& setFormat(Qt::TextFormat format);
    QuText& setOpenLinks(bool open_links = true);
    QuText& setAlignment(Qt::Alignment alignment);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected:
    QString m_text;
    FieldRefPtr m_fieldref;
    bool m_big;
    bool m_bold;
    bool m_italic;
    bool m_warning;
    Qt::TextFormat m_text_format;
    bool m_open_links;
    Qt::Alignment m_alignment;
};
