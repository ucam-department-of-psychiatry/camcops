#include "clickablelabelwordwrapwide.h"
#include <QDebug>
#include <QMargins>
#include <QStyleOptionButton>
#include <QVBoxLayout>
#include "lib/uifunc.h"
#include "labelwordwrapwide.h"


ClickableLabelWordWrapWide::ClickableLabelWordWrapWide(const QString& text,
                                                       QWidget* parent) :
    QPushButton(parent),
    m_label(new LabelWordWrapWide(text, this))
{
    commonConstructor();
}


ClickableLabelWordWrapWide::ClickableLabelWordWrapWide(QWidget* parent) :
    QPushButton(parent),
    m_label(new LabelWordWrapWide(this))
{
    commonConstructor();
}


void ClickableLabelWordWrapWide::commonConstructor()
{
    m_label->setMouseTracking(false);
    m_label->setTextInteractionFlags(Qt::NoTextInteraction);
    // ... makes sure that all clicks come to us (not e.g. trigger URL)
    // m_label->setObjectName("debug_yellow");

    m_layout = new QVBoxLayout();
    // m_layout->setContentsMargins(UiConst::NO_MARGINS);
    // no, use CSS instead // layout->setMargin(0);

    m_layout->addWidget(m_label);

    setLayout(m_layout);
    setSizePolicy(UiFunc::horizMaximumHFWPolicy());
    // http://doc.qt.io/qt-5/layout.html
}


void ClickableLabelWordWrapWide::setTextFormat(Qt::TextFormat format)
{
    Q_ASSERT(m_label);
    m_label->setTextFormat(format);
}


void ClickableLabelWordWrapWide::setWordWrap(bool on)
{
    Q_ASSERT(m_label);
    m_label->setWordWrap(on);
    updateGeometry();
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
    return translateSize(m_label->sizeHint());
}


QSize ClickableLabelWordWrapWide::minimumSizeHint() const
{
    Q_ASSERT(m_label);
    return translateSize(m_label->minimumSizeHint());
}


void ClickableLabelWordWrapWide::resizeEvent(QResizeEvent* event)
{
    QPushButton::resizeEvent(event);
    QLayout* lay = layout();
    if (!lay || !lay->hasHeightForWidth()) {
        return;
    }
    int w = width();
    int h = lay->heightForWidth(w);
    setFixedHeight(h);
    updateGeometry();
}


void ClickableLabelWordWrapWide::setText(const QString& text)
{
    Q_ASSERT(m_label);
    m_label->setText(text);
    updateGeometry();
}
