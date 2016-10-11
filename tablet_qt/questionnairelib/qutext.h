#pragma once
#include "db/fieldref.h"
#include "quelement.h"
#include "common/uiconstants.h"

class LabelWordWrapWide;


class QuText : public QuElement
{
    // Provides static text, or text from a field.

    Q_OBJECT
public:
    QuText(const QString& text = "");
    QuText(FieldRefPtr fieldref);
    QuText* big(bool big = true);
    QuText* bold(bool bold = true);
    QuText* italic(bool italic = true);
    QuText* warning(bool warning = true);
    QuText* setFormat(Qt::TextFormat format);
    QuText* setOpenLinks(bool open_links = true);
    QuText* setAlignment(Qt::Alignment alignment);
protected:
    void commonConstructor();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected slots:
    void fieldValueChanged(const FieldRef* fieldref);
protected:
    QString m_text;
    FieldRefPtr m_fieldref;
    UiConst::FontSize m_fontsize;
    bool m_bold;
    bool m_italic;
    bool m_warning;
    Qt::TextFormat m_text_format;
    bool m_open_links;
    Qt::Alignment m_alignment;
    QPointer<LabelWordWrapWide> m_label;
};
