#include "clickablelabel.h"

ClickableLabel::ClickableLabel(const QString& text, QWidget* parent) :
    QLabel(text, parent),
    m_clickable(false)
{
}


void ClickableLabel::setClickable(bool clickable)
{
    m_clickable = clickable;
}


void ClickableLabel::mousePressEvent(QMouseEvent *event)
{
    if (m_clickable) {
        // Handle event
        emit clicked();
    } else {
        // Pass on event to others
        QLabel::mousePressEvent(event);
    }
}
