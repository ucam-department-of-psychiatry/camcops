// #define DEBUG_CALCULATIONS

#include "clickablelabelwordwrapwide.h"
#include <QDebug>
#include <QMargins>
#include <QStyleOptionButton>
#include <QVBoxLayout>
#include "lib/uifunc.h"
#include "labelwordwrapwide.h"


ClickableLabelWordWrapWide::ClickableLabelWordWrapWide(const QString& text,
                                                       bool stretch,
                                                       QWidget* parent) :
    QPushButton(parent),
    m_label(new LabelWordWrapWide(text, this))
{
    commonConstructor(stretch);
}


ClickableLabelWordWrapWide::ClickableLabelWordWrapWide(bool stretch,
                                                       QWidget* parent) :
    QPushButton(parent),
    m_label(new LabelWordWrapWide(this))
{
    commonConstructor(stretch);
}


void ClickableLabelWordWrapWide::commonConstructor(bool stretch)
{
    m_label->setMouseTracking(false);
    m_label->setTextInteractionFlags(Qt::NoTextInteraction);
    // ... makes sure that all clicks come to us (not e.g. trigger URL)
    // m_label->setObjectName(CssConst::DEBUG_YELLOW);

    m_layout = new QVBoxLayout();
    // m_layout->setContentsMargins(UiConst::NO_MARGINS);
    // no, use CSS instead // layout->setMargin(0);

    m_layout->addWidget(m_label);
    if (stretch) {
        m_layout->addStretch();
    }

    setLayout(m_layout);
    setSizePolicy(stretch ? UiFunc::expandingFixedHFWPolicy()
                          : UiFunc::maximumFixedHFWPolicy());
    // http://doc.qt.io/qt-5/layout.html

    adjustSize();
}


void ClickableLabelWordWrapWide::setTextFormat(Qt::TextFormat format)
{
    Q_ASSERT(m_label);
    m_label->setTextFormat(format);
    adjustSize();
}


void ClickableLabelWordWrapWide::setWordWrap(bool on)
{
    Q_ASSERT(m_label);
    m_label->setWordWrap(on);
    adjustSize();
}


void ClickableLabelWordWrapWide::setAlignment(Qt::Alignment alignment)
{
    Q_ASSERT(m_label);
    m_label->setAlignment(alignment);
    m_layout->setAlignment(m_label, alignment);
}


void ClickableLabelWordWrapWide::setOpenExternalLinks(bool open)
{
    Q_ASSERT(m_label);
    m_label->setOpenExternalLinks(open);
}


// http://permalink.gmane.org/gmane.comp.lib.qt.general/40030

QSize ClickableLabelWordWrapWide::translateSize(const QSize& size) const
{
    QStyleOptionButton opt;
    initStyleOption(&opt);  // protected
    return UiFunc::pushButtonSizeHintFromContents(this, &opt, size);
}


QSize ClickableLabelWordWrapWide::sizeHint() const
{
    Q_ASSERT(m_label);
    QSize result = translateSize(m_label->sizeHint());
#ifdef DEBUG_CALCULATIONS
    qDebug() << Q_FUNC_INFO << "->" << result;
#endif
    return result;
}


QSize ClickableLabelWordWrapWide::minimumSizeHint() const
{
    Q_ASSERT(m_label);
    QSize result = translateSize(m_label->minimumSizeHint());
#ifdef DEBUG_CALCULATIONS
    qDebug() << Q_FUNC_INFO << "->" << result;
#endif
    return result;
}


void ClickableLabelWordWrapWide::resizeEvent(QResizeEvent* event)
{
#ifdef DEBUG_CALCULATIONS
    qDebug() << Q_FUNC_INFO;
#endif
    QPushButton::resizeEvent(event);
    UiFunc::resizeEventForHFWParentWidget(this);
}


void ClickableLabelWordWrapWide::setText(const QString& text)
{
    Q_ASSERT(m_label);
#ifdef DEBUG_CALCULATIONS
    qDebug() << Q_FUNC_INFO << text;
#endif
    m_label->setText(text);
    adjustSize();
}
