/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

// #define DEBUG_LAYOUT

#include "verticalscrollareaviewport.h"
#include <QDebug>
#include <QResizeEvent>
#include "lib/sizehelpers.h"


VerticalScrollAreaViewport::VerticalScrollAreaViewport(QWidget* parent) :
    QWidget(parent)
{
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
#endif
}


void VerticalScrollAreaViewport::resizeEvent(QResizeEvent* event)
{
    QSize s = event->size();

#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO << s;
#endif
    // QWidget::resizeEvent(event);  // doesn't actually do anything

    resizeSingleChild(s);
}


/*
void VerticalScrollAreaViewport::setGeometry(const QRect& rect)
{
    QWidget::setGeometry(rect);
    resizeSingleChild(rect.size());
}


void VerticalScrollAreaViewport::setGeometry(int x, int y, int w, int h)
{
    QWidget::setGeometry(x, y, w, h);
    resizeSingleChild(QSize(w, h));
}
*/


void VerticalScrollAreaViewport::resizeSingleChild(const QSize& our_size)
{
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO << our_size;
#endif

    if (layout()) {
        qWarning() << Q_FUNC_INFO << "- shouldn't have a layout!";
        return;
    }

    const QObjectList& children_list = children();
    if (children_list.length() == 0) {
        qWarning() << Q_FUNC_INFO << "- no children!";
        return;
    }
    if (children_list.length() > 1) {
        qWarning() << Q_FUNC_INFO << "- multiple children!";
        return;
    }
    QObject* child_object = children_list.at(0);
    QWidget* child = dynamic_cast<QWidget*>(child_object);
    if (!child) {
        qWarning() << Q_FUNC_INFO << "- child is not a QWidget!";
        return;
    }

    QSize new_child_size;
    if (child->hasHeightForWidth()) {
        new_child_size = our_size;
        new_child_size.rheight() = child->heightForWidth(our_size.width());
    } else {
        new_child_size = child->sizeHint();
    }
    child->resize(new_child_size);
}
