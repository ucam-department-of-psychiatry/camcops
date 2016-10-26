#include "spacer.h"
#include "common/uiconstants.h"

Spacer::Spacer(QWidget* parent) :
    QWidget(parent),
    m_size(UiConst::SPACE, UiConst::SPACE)
{
    setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
}


Spacer::Spacer(const QSize& size, QWidget* parent) :
    QWidget(parent),
    m_size(size)
{
    setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
}


QSize Spacer::sizeHint() const
{
    return m_size;
}
