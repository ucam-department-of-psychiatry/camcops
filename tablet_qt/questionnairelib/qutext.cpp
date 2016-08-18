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
    m_text_format(Qt::AutoText)
{
}


QuText::QuText(FieldRefPtr fieldref) :
    m_text(""),
    m_fieldref(fieldref),
    m_big(false),
    m_bold(false),
    m_italic(false),
    m_text_format(Qt::AutoText)
{
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


QuText* QuText::setFormat(Qt::TextFormat format)
{
    m_text_format = format;
    return this;
}


QPointer<QWidget> QuText::makeWidget(Questionnaire* questionnaire)
{
    QString text = m_fieldref ? m_fieldref->getString() : m_text;
    LabelWordWrapWide* label = new LabelWordWrapWide(text);
    int fontsize = questionnaire->fontSizePt(m_big ? FontSize::Big
                                                   : FontSize::Normal);
    QString css = textCSS(fontsize, m_bold, m_italic);
    label->setStyleSheet(css);
    label->setTextFormat(m_text_format);
    return QPointer<QWidget>(label);
}
