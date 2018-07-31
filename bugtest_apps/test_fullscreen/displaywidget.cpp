#include "displaywidget.h"
#include <QDebug>
#include <QHBoxLayout>
#include <QKeyEvent>
#include <QLabel>
#include <QMouseEvent>


DisplayWidget::DisplayWidget(const QString& text, bool fullscreen,
                             QWidget* parent)
    : QWidget(parent),
      m_text(text),
      m_fullscreen(fullscreen)
{
    setFocusPolicy(Qt::ClickFocus);  // for keyboard input

    QLabel* label = new QLabel(m_text);
    QHBoxLayout* layout = new QHBoxLayout();
    layout->addWidget(label);
    setLayout(layout);

    label->installEventFilter(this);

}


void DisplayWidget::mousePressEvent(QMouseEvent* event)
{
    qDebug().nospace() << "Widget " << m_text
            << ": QMouseEvent: pos " << event->pos()
            << ", buttons " << event->buttons();
}


void DisplayWidget::keyPressEvent(QKeyEvent* event)
{
    const int key = event->key();
    qDebug().nospace() << "DisplayWidget " << m_text
            << ": QKeyEvent: key " << key;
    if (key == Qt::Key_C) {
        qDebug() << "User pressed C to close";
        emit pleaseClose();
    }
}
