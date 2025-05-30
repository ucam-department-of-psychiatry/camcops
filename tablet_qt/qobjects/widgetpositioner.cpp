
/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

    Based on the DialogPositioner class in https://github.com/f4exb/sdrangel/
    v7.21.1, which has the following licence:

    Copyright (C) 2022-2023 Jon Beniston, M7RCE <jon@beniston.com>
    Copyright (C) 2023 Mohamed <mohamedadlyi@github.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation as version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License V3 for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

#include <QEvent>
#include <QObject>
#include <QScreen>
#include <QtDebug>
#include <QTimer>
#include <QWidget>

// #define DEBUG_WIDGET_POSITIONER
// #define DEBUG_WIDGET_POSITIONER_LAYOUT

#ifdef DEBUG_WIDGET_POSITIONER_LAYOUT
    #include "lib/layoutdumper.h"
#endif

#include "widgetpositioner.h"

WidgetPositioner::WidgetPositioner(QWidget* widget) :
    QObject(widget),  // make widget our parent; it will own us
    m_widget(widget)
{
    Q_ASSERT(widget);

    centre();
    m_widget->installEventFilter(this);

    connect(
        m_widget->screen(),
        &QScreen::orientationChanged,
        this,
        &WidgetPositioner::orientationChanged
    );
}

void WidgetPositioner::orientationChanged(Qt::ScreenOrientation orientation)
{
#ifdef DEBUG_WIDGET_POSITIONER
    qDebug().nospace() << Q_FUNC_INFO;
#endif

    Q_UNUSED(orientation)

    // Not reliable to retrieve the screen or dialog geometry at this point.
    // https://bugreports.qt.io/browse/QTBUG-91363
    // https://bugreports.qt.io/browse/QTBUG-109127

    // hide() followed by show() will resize and reposition the dialog
    // correctly on iOS but this crashes on Android. So we do this ourselves
    // after a short delay.
    QTimer::singleShot(200, this, &WidgetPositioner::centre);
}

void WidgetPositioner::centre()
{
    Q_ASSERT(m_widget);

#ifdef DEBUG_WIDGET_POSITIONER
    qDebug().nospace() << Q_FUNC_INFO;
#endif

    sizeToScreen();

    const QRect available_geometry = m_widget->screen()->availableGeometry();
    const int x = (available_geometry.width() - m_widget->width()) / 2;
    const int y = (available_geometry.height() - m_widget->height()) / 2;

    const QPoint new_pos = QPoint(x, y);

    if (new_pos != m_widget->pos()) {
#ifdef DEBUG_WIDGET_POSITIONER
        qDebug("Moving widget to %d, %d", x, y);
#endif
        m_widget->move(x, y);
    } else {
#ifdef DEBUG_WIDGET_POSITIONER
        qDebug("No need to move widget");
#endif
    }

#ifdef DEBUG_WIDGET_POSITIONER_LAYOUT
    layoutdumper::dumpWidgetHierarchy(m_widget);
#endif
}

void WidgetPositioner::sizeToScreen()
{
#ifdef DEBUG_WIDGET_POSITIONER
    qDebug().nospace() << Q_FUNC_INFO;
#endif

    Q_ASSERT(m_widget);

    const QRect available_geometry = m_widget->screen()->availableGeometry();
    const int screen_width = available_geometry.width();
    const int screen_height = available_geometry.height();

    bool changed = false;

    int new_width = m_widget->width();
    int new_height = m_widget->height();

    if (new_width > screen_width) {
        new_width = screen_width;
        changed = true;
    }
    if (new_height > screen_height) {
        new_height = screen_height;
        changed = true;
    }
    if (changed) {
#ifdef DEBUG_WIDGET_POSITIONER
        qDebug("Resizing widget to %d, %d", new_width, new_height);
#endif
        m_widget->resize(new_width, new_height);
    } else {
#ifdef DEBUG_WIDGET_POSITIONER
        qDebug().nospace() << "No need to resize widget";
#endif
    }
}

bool WidgetPositioner::eventFilter(QObject* obj, QEvent* event)
{
    if (event->type() == QEvent::Show) {
#ifdef DEBUG_WIDGET_POSITIONER
        qDebug() << "Event filter calling centre()";
#endif
        centre();
    }

    return QObject::eventFilter(obj, event);
}
