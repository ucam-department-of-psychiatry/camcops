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

#if 1

#define DEBUG_PAINTING

#include "zoomablewidget.h"
#include <QDebug>
#include <QPainter>
#include <QVBoxLayout>
#include <QWheelEvent>

/*

See:

- https://stackoverflow.com/questions/6650219/zooming-function-on-a-qwidget
- https://stackoverflow.com/questions/26811446/qt-scaling-zooming-contents-of-a-qframe-widgets-etc

NOT YET IMPLEMENTED, OR BUGGY

- The current show()/hide() method in paintEvent works, broadly, but triggers
  an endless series of further paint events.
- Getting the right background colour for the "paint to pixmap", grab().
- Translating mouse (and touch) event coordinates.
- Making the contents widget responsive despite being hidden.

SLIGHTLY UNDESIRABLE:

- It's a pixel-wise zoom -- better than that (e.g. having text be painted at a
  different font size) would be a bit optimistic!

*/


ZoomableWidget::ZoomableWidget(QWidget* contents,
                               qreal min_scale,
                               qreal max_scale,
                               qreal scale_step_factor,
                               QWidget* parent) :
    QWidget(parent),
    m_contents(contents),
    m_min_scale(min_scale),
    m_max_scale(max_scale),
    m_scale_step_factor(scale_step_factor),
    m_scale(1.0)
{
    Q_ASSERT(m_contents);
    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->addWidget(contents);
    QSizePolicy sp(QSizePolicy::Expanding, QSizePolicy::Expanding);
    sp.setHeightForWidth(contents->hasHeightForWidth());
    setSizePolicy(sp);
}


void ZoomableWidget::paintEvent(QPaintEvent* event)
{
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO;
#endif
    if (qFuzzyCompare(m_scale, 1.0)) {
        // Unscaled
        m_contents->show();
        QWidget::paintEvent(event);
    } else {
        // Scaled
        m_contents->show();
        const QPixmap pm = m_contents->grab();
        m_contents->hide();
        QPainter painter(this);
        painter.scale(m_scale, m_scale);
        painter.drawPixmap(0, 0, pm);
    }

}


void ZoomableWidget::wheelEvent(QWheelEvent* event)
{
    // https://github.com/glumpy/glumpy/issues/99
    const int steps = event->angleDelta().y() / 120;
    if (steps == 0) {
        return;  // nothing to do
    }
    if (steps > 0) {
        // zoom in (magnify); steps is positive
        m_scale *= m_scale_step_factor * steps;
    } else {
        // zoom out (shrink); steps is negative
        m_scale /= m_scale_step_factor * (-steps);
    }
    m_scale = qBound(m_min_scale, m_scale, m_max_scale);
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << "steps" << steps << "m_scale" << m_scale;
#endif
    update();
}


QPoint ZoomableWidget::translatedPoint(const QPoint& p) const
{
    if (qFuzzyCompare(m_scale, 1.0)) {
        return p;
    }
    // *** implement
}


#endif  // whole source file
