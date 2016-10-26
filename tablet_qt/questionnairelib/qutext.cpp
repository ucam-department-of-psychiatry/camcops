#include "qutext.h"
#include <QDebug>
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/labelwordwrapwide.h"


QuText::QuText(const QString& text) :
    m_text(text),
    m_fieldref(nullptr)
{
    commonConstructor();
}


QuText::QuText(FieldRefPtr fieldref) :
    m_text(""),
    m_fieldref(fieldref)
{
    Q_ASSERT(m_fieldref);
    commonConstructor();
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuText::fieldValueChanged);
}


void QuText::commonConstructor()
{
    m_fontsize = UiConst::FontSize::Normal;
    m_bold = false;
    m_italic = false;
    m_warning = false;
    m_text_format = Qt::AutoText;
    m_open_links = false;
    m_alignment = Qt::AlignLeft | Qt::AlignVCenter;
    m_label = nullptr;
    m_forced_fontsize_pt = -1;
}


QuText* QuText::big(bool big)
{
    m_fontsize = big ? UiConst::FontSize::Big : UiConst::FontSize::Normal;
    return this;
}


QuText* QuText::bold(bool bold)
{
    m_bold = bold;
    return this;
}


QuText* QuText::italic(bool italic)
{
    m_italic = italic;
    return this;
}


QuText* QuText::warning(bool warning)
{
    m_warning = warning;
    return this;
}


QuText* QuText::setFormat(Qt::TextFormat format)
{
    m_text_format = format;
    return this;
}


QuText* QuText::setOpenLinks(bool open_links)
{
    m_open_links = open_links;
    return this;
}


QuText* QuText::setAlignment(Qt::Alignment alignment)
{
    m_alignment = alignment;
    return this;
}


QPointer<QWidget> QuText::makeWidget(Questionnaire* questionnaire)
{
    QString text;
    if (m_fieldref && m_fieldref->valid()) {
        text = m_fieldref->valueString();
    } else {
        text = m_text;
    }
    m_label = new LabelWordWrapWide(text);
    int fontsize = questionnaire->fontSizePt(m_fontsize);
    setWidgetFontSize(m_forced_fontsize_pt > 0 ? m_forced_fontsize_pt
                                               : fontsize);
    m_label->setTextFormat(m_text_format);
    m_label->setOpenExternalLinks(m_open_links);
    m_label->setAlignment(m_alignment);
    return QPointer<QWidget>(m_label);
}


void QuText::fieldValueChanged(const FieldRef* fieldref)
{
    if (!m_label) {
        qDebug() << Q_FUNC_INFO << "... NO LABEL";
        return;
    }
    m_label->setText(fieldref->valueString());
}


void QuText::forceFontSize(int fontsize_pt, bool repolish)
{
    m_forced_fontsize_pt = fontsize_pt;
    setWidgetFontSize(m_forced_fontsize_pt, repolish);
}


void QuText::forceText(const QString &text, bool repolish)
{
    if (!m_label) {
        return;
    }
    m_label->setText(text);
    if (repolish) {
        repolishWidget();
    }
}


void QuText::setWidgetFontSize(int fontsize_pt, bool repolish)
{
    if (!m_label) {
        return;
    }
    QString colour = m_warning ? UiConst::WARNING_COLOUR : "";
    QString css = UiFunc::textCSS(fontsize_pt, m_bold, m_italic, colour);
    m_label->setStyleSheet(css);
    if (repolish) {
        repolishWidget();
    }
}


void QuText::repolishWidget()
{
    if (m_label) {
        UiFunc::repolish(m_label);
        m_label->updateGeometry();
    }
}
