#include "clickablelabel.h"
#include <QApplication>
#include <QDebug>
#include <QMouseEvent>


ClickableLabel::ClickableLabel(const QString& text, QWidget* parent) :
    QLabel(text, parent),
    m_clickable(true),  // if that's not the default, the name's confusing!
    m_down(false)
{
}


void ClickableLabel::setClickable(bool clickable)
{
    m_clickable = clickable;
}


void ClickableLabel::mousePressEvent(QMouseEvent* event)
{
    if (!m_clickable) {
        // Pass on event to others
        QLabel::mousePressEvent(event);
        return;
    }

    // Handle event
    // See QAbstractButton::mousePressEvent; here simplified.
    if (event->button() != Qt::LeftButton) {
        event->ignore();
        return;
    }

    m_down = true;
    qDebug() << Q_FUNC_INFO << "calling update()";
    update();
    QApplication::flush();
    emit pressed();
    event->accept();
}


void ClickableLabel::mouseReleaseEvent(QMouseEvent* event)
{
    // See QAbstractButton::mouseReleaseEvent, here simplified.
    if (!m_down || event->button() != Qt::LeftButton) {
        event->ignore();
        return;
    }
    m_down = false;
    if (hitButton(event->pos())) {
        qDebug() << Q_FUNC_INFO << "calling update()";
        update();
        QApplication::flush();
        emit clicked();
        event->accept();
    } else {
        event->ignore();
    }
}


void ClickableLabel::mouseMoveEvent(QMouseEvent* event)
{
    // See QAbstractButton::mouseMoveEvent, here simplified.
    if (!(event->buttons() & Qt::LeftButton) || !m_down) {
        event->ignore();
        return;
    }
    if (hitButton(event->pos()) != m_down) {
        m_down = !m_down;
        qDebug() << Q_FUNC_INFO << "calling update()";
        update();
        QApplication::flush();
        if (m_down) {
            emit pressed();
        } else {
            emit released();
        }
        event->accept();
    } else if (!hitButton(event->pos())) {
        event->ignore();
    }
}


bool ClickableLabel::hitButton(const QPoint& pos) const
{
    return rect().contains(pos);
}
