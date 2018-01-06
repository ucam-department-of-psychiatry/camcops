/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
#include <QPointF>
#include <QRectF>
#include <QTransform>


class LineSegment {
    // a(x - xm) + b(y - ym) = c
    // http://stackoverflow.com/questions/385305/efficient-maths-algorithm-to-calculate-intersections
public:
    LineSegment(const QPointF& from, const QPointF& to);
    qreal c(qreal x, qreal y) const;  // 0 if point is on the line; otherwise, sign gives side
    qreal c(const QPointF& pt) const;
    int side(const QPointF& pt) const;
    bool isPoint() const;
    bool xRangesOverlap(const LineSegment& other) const;
    bool yRangesOverlap(const LineSegment& other) const;
    bool intersects(const LineSegment& other) const;
    bool pointOn(const QPointF& point) const;
    qreal angleRad() const;
    QRectF rect() const;
    bool pointInPerpendicularArea(const QPointF& point) const;

protected:
    QPointF from;
    QPointF to;

    qreal xlow;
    qreal xhigh;
    qreal ylow;
    qreal yhigh;

    qreal a;  // y span of line segment
    qreal xm;  // x median of line segment
    qreal b;  // x span of line segment
    qreal ym;  // y median of line segment

    QTransform m_transform_horiz_rightwards;
    QPointF m_transformed_from;
    QPointF m_transformed_to;
};
