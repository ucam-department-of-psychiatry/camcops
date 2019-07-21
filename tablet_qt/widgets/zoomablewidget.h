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

#if 1

// NOT YET PROPERLY IMPLEMENTED.

#include <QWidget>

class ZoomableWidget : public QWidget
{
    Q_OBJECT
public:
    // Constructor
    ZoomableWidget(QWidget* contents,
                   qreal min_scale = 1.0,
                   qreal max_scale = 5.0,
                   qreal scale_step_factor = 1.1,
                   QWidget* parent = nullptr);
protected:
    void paintEvent(QPaintEvent* event);
    void wheelEvent(QWheelEvent* event);
    QPoint translateWorldToContents(const QPoint& p,
                                    bool screenpos_not_localpos) const;
protected:
    QWidget* m_contents;
    qreal m_min_scale;
    qreal m_max_scale;
    qreal m_scale_step_factor;
    qreal m_scale;
};

#endif  // whole header file
