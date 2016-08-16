#include "text.h"
#include <QDebug>
#include <QLabel>
#include "lib/uifunc.h"
#include "questionnaire.h"


Text::Text(const QString& text) :
    m_text(text),
    m_fieldref(nullptr),
    m_big(false),
    m_bold(false),
    m_italic(false),
    m_text_format(Qt::AutoText)
{
}


Text::Text(FieldRefPtr fieldref) :
    m_text(""),
    m_fieldref(fieldref),
    m_big(false),
    m_bold(false),
    m_italic(false),
    m_text_format(Qt::AutoText)
{
}


Text* Text::big(bool big)
{
    m_big = big;
    return this;
}


Text* Text::bold(bool bold)
{
    m_bold = bold;
    return this;
}


Text* Text::italic(bool italic)
{
    m_italic = italic;
    return this;
}


Text* Text::setFormat(Qt::TextFormat format)
{
    m_text_format = format;
    return this;
}


QPointer<QWidget> Text::makeWidget(Questionnaire* questionnaire)
{
    QString text = m_fieldref ? m_fieldref->getString() : m_text;
    QLabel* label = new QLabel(text);
    int fontsize = questionnaire->fontSizePt(m_big ? FontSize::Big
                                                   : FontSize::Normal);
    QString css = textCSS(fontsize, m_bold, m_italic);
    label->setStyleSheet(css);
    label->setTextFormat(m_text_format);
    label->setWordWrap(true);
    // QSizePolicy sp(QSizePolicy::Expanding, QSizePolicy::Minimum);
    // label->setSizePolicy(sp);
    return QPointer<QWidget>(label);
}
