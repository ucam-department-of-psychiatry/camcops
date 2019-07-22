/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#define DEBUG_PAINTING

#include "zoomablewidget.h"
#include <QDebug>
#include <QGraphicsProxyWidget>
#include <QGraphicsScene>
#include <QVBoxLayout>
#include "qobjects/sizewatcher.h"
#include "widgets/zoomablegraphicsview.h"

/*

See:

- https://stackoverflow.com/questions/6650219/zooming-function-on-a-qwidget
- https://stackoverflow.com/questions/26811446/qt-scaling-zooming-contents-of-a-qframe-widgets-etc

NOT YET IMPLEMENTED, OR BUGGY

- In ZoomableGraphicsView, fitInView() is scaling things a bit too small.
- Getting the right background colour, and style -- in general, the CSS is
  not being applied properly.
- First-time sizing not always right (better on second page paint!).
  Likely related to current failure to correct for scroll bar size.
- Testing of two-finger zoom.

Once fixed, undefine DISABLE_ZOOMABLE_WIDGET in questionnaire.cpp.

SLIGHTLY UNDESIRABLE BUT OK:

- It's a pixel-wise zoom -- better than that (e.g. having text be painted at a
  different font size) would be a bit optimistic!

*/


ZoomableWidget::ZoomableWidget(QWidget* contents,
                               const bool can_scale_smaller_than_viewport,
                               const qreal min_scale,
                               const qreal max_scale,
                               const qreal scale_step_factor,
                               QWidget* parent) :
    QWidget(parent),
    m_contents(contents)
{
    Q_ASSERT(m_contents);

    // We create a graphics scene containing our target widget.
    contents->ensurePolished();
    // At this point, contents->contentsRect() is unhelpfully 640x480. So:
    const QRectF scene_rect(QPointF(0, 0), contents->sizeHint());
    m_scene = new QGraphicsScene(scene_rect);
    m_scene->addWidget(contents);  // adds it at (0,0); returns QGraphicsProxyWidget*
    m_size_watcher = new SizeWatcher(contents);
    connect(m_size_watcher, &SizeWatcher::resized,
            this, &ZoomableWidget::widgetSizeChanged);

    // We create a graphics view to show the scene.
    // The view is where we implement sooming.
    m_view = new ZoomableGraphicsView(
                m_scene, can_scale_smaller_than_viewport,
                min_scale, max_scale, scale_step_factor);
    m_view->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);

    // *** view->setBackgroundColour(background_colour);

    // Our widget has a layout containing the graphics view.
    auto layout = new QVBoxLayout(this);
    layout->addWidget(m_view);

    QSizePolicy sp(QSizePolicy::Expanding, QSizePolicy::Expanding);
    // sp.setHeightForWidth(contents->hasHeightForWidth());
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << "ZoomableWidget size policy:" << sp;
#endif
    setSizePolicy(sp);
}


QSize ZoomableWidget::sizeHint() const
{
    const QSize size = m_contents->sizeHint();
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << size;
#endif
    return size;
}


QSize ZoomableWidget::minimumSizeHint() const
{
    const QSize size = m_contents->minimumSizeHint();
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << size;
#endif
    return size;
}


bool ZoomableWidget::hasHeightForWidth() const
{
    const bool hfw = m_contents->hasHeightForWidth();
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << hfw;
#endif
    return hfw;
}


int ZoomableWidget::heightForWidth(int width) const
{
    const int h = m_contents->heightForWidth(width);
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << h;
#endif
    return h;
}


void ZoomableWidget::widgetSizeChanged(const QSize& size)
{
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << size;
#endif
    const QRectF rect(QPointF(0, 0), size);
    m_scene->setSceneRect(rect);
}
