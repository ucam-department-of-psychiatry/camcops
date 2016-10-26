#include "clickablelabel.h"
#include <QApplication>
#include <QDebug>
#include <QLabel>
#include <QMouseEvent>
#include <QStyleOptionButton>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "lib/uifunc.h"


ClickableLabel::ClickableLabel(const QString& text, QWidget* parent) :
    QPushButton(parent),
    m_label(new QLabel(text, this))
{
    commonConstructor();
}


ClickableLabel::ClickableLabel(QWidget* parent) :
    QPushButton(parent),
    m_label(new QLabel(this))
{
    commonConstructor();
}


void ClickableLabel::commonConstructor()
{
    m_label->setMouseTracking(false);
    m_label->setTextInteractionFlags(Qt::NoTextInteraction);
    m_label->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    // m_label->setObjectName("debug_green");

    m_layout = new QVBoxLayout();
    m_layout->setContentsMargins(UiConst::NO_MARGINS);

    m_layout->addWidget(m_label);

    setLayout(m_layout);
    // Default size policy is (QSizePolicy::Preferred, QSizePolicy::Preferred);
    // see qwidget.cpp
    setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Fixed);
}


void ClickableLabel::setTextFormat(Qt::TextFormat format)
{
    Q_ASSERT(m_label);
    m_label->setTextFormat(format);
}


void ClickableLabel::setWordWrap(bool on)
{
    Q_ASSERT(m_label);
    m_label->setWordWrap(on);
    updateGeometry();
}


void ClickableLabel::setAlignment(Qt::Alignment alignment)
{
    Q_ASSERT(m_label);
    Q_ASSERT(m_layout);
    m_label->setAlignment(alignment);
    m_layout->setAlignment(m_label, alignment);
}


void ClickableLabel::setOpenExternalLinks(bool open)
{
    Q_ASSERT(m_label);
    m_label->setOpenExternalLinks(open);
}


void ClickableLabel::setPixmap(const QPixmap& pixmap)
{
    Q_ASSERT(m_label);
    m_label->setPixmap(pixmap);
    setFixedSize(pixmap.size());
    setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    updateGeometry();
}


QSize ClickableLabel::sizeHint() const
{
    Q_ASSERT(m_label);
    QStyleOptionButton opt;
    initStyleOption(&opt);  // protected
    return UiFunc::pushButtonSizeHintFromContents(this, &opt,
                                                  m_label->sizeHint());
}
