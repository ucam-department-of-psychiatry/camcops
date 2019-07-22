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

#pragma once

#include <QGraphicsView>

class ZoomableGraphicsView : public QGraphicsView
{
    Q_OBJECT
public:
    ZoomableGraphicsView(QGraphicsScene* scene,
                         bool can_scale_smaller_than_viewport,
                         qreal min_scale = 0.2,
                         qreal max_scale = 5.0,
                         qreal scale_step_factor = 1.1);

    // To zoom:
    virtual void wheelEvent(QWheelEvent* event) override;
    virtual bool viewportEvent(QEvent* event) override;

    // Other events:
    virtual void resizeEvent(QResizeEvent* event) override;
    virtual void showEvent(QShowEvent* event) override;

    // Scaling
    void rescale();
    void fitView();

protected:
    bool m_can_scale_smaller_than_viewport;
    qreal m_min_scale;
    qreal m_max_scale;
    qreal m_scale_step_factor;
    qreal m_scale;
    qreal m_smallest_fit_scale;
};
