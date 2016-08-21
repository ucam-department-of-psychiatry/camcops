#include "qutext.h"
#include <QDebug>
#include "lib/uifunc.h"
#include "questionnaire.h"
#include "widgets/labelwordwrapwide.h"


QuText::QuText(const QString& text) :
    m_text(text),
    m_fieldref(nullptr),
    m_big(false),
    m_bold(false),
    m_italic(false),
    m_warning(false),
    m_text_format(Qt::AutoText),
    m_open_links(false),
    m_alignment(Qt::AlignLeft | Qt::AlignVCenter)
{
}


QuText::QuText(FieldRefPtr fieldref) :
    m_text(""),
    m_fieldref(fieldref),
    m_big(false),
    m_bold(false),
    m_italic(false),
    m_text_format(Qt::AutoText),
    m_open_links(false),
    m_alignment(Qt::AlignLeft | Qt::AlignVCenter)
{
}


QuText& QuText::big(bool big)
{
    m_big = big;
    return *this;
}


QuText& QuText::bold(bool bold)
{
    m_bold = bold;
    return *this;
}


QuText& QuText::italic(bool italic)
{
    m_italic = italic;
    return *this;
}


QuText& QuText::warning(bool warning)
{
    m_warning = warning;
    return *this;
}


QuText& QuText::setFormat(Qt::TextFormat format)
{
    m_text_format = format;
    return *this;
}


QuText& QuText::setOpenLinks(bool open_links)
{
    m_open_links = open_links;
    return *this;
}


QuText& QuText::setAlignment(Qt::Alignment alignment)
{
    m_alignment = alignment;
    return *this;
}


QPointer<QWidget> QuText::makeWidget(Questionnaire* questionnaire)
{
    QString text = m_fieldref ? m_fieldref->valueString() : m_text;
    LabelWordWrapWide* label = new LabelWordWrapWide(text);
    int fontsize = questionnaire->fontSizePt(m_big ? FontSize::Big
                                                   : FontSize::Normal);
    QString colour = m_warning ? WARNING_COLOUR : "";
    QString css = textCSS(fontsize, m_bold, m_italic, colour);
    label->setStyleSheet(css);
    label->setTextFormat(m_text_format);
    label->setOpenExternalLinks(m_open_links);
    label->setAlignment(m_alignment);
    return QPointer<QWidget>(label);
}
