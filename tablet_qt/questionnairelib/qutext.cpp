#include "qutext.h"
#include <QDebug>
#include "lib/uifunc.h"
#include "questionnaire.h"
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
            this, &QuText::valueChanged);
}


void QuText::commonConstructor()
{
    m_big = false;
    m_bold = false;
    m_italic = false;
    m_warning = false;
    m_text_format = Qt::AutoText;
    m_open_links = false;
    m_alignment = Qt::AlignLeft | Qt::AlignVCenter;
    m_label = nullptr;
}


QuText* QuText::big(bool big)
{
    m_big = big;
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
    int fontsize = questionnaire->fontSizePt(m_big ? UiConst::FontSize::Big
                                                   : UiConst::FontSize::Normal);
    QString colour = m_warning ? UiConst::WARNING_COLOUR : "";
    QString css = UiFunc::textCSS(fontsize, m_bold, m_italic, colour);
    m_label->setStyleSheet(css);
    m_label->setTextFormat(m_text_format);
    m_label->setOpenExternalLinks(m_open_links);
    m_label->setAlignment(m_alignment);
    return QPointer<QWidget>(m_label);
}


void QuText::valueChanged(const FieldRef* fieldref)
{
    qDebug().nospace() << "QuText: receiving valueChanged: this=" << this
                       << ", value=" << fieldref->value();
    if (!m_label) {
        qDebug() << "... NO LABEL";
        return;
    }
    m_label->setText(fieldref->valueString());
    m_label->update();  // *** necessary?
}
