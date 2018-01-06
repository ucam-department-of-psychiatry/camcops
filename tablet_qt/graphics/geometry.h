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
#include <QtGlobal>
#include <QWidget>  // for QWIDGETSIZE_MAX
#include "graphics/linesegment.h"


namespace geometry
{

/*

Standard Cartesian/polar coordinate systems
===============================================================================

- Positive x is to the right.
- Positive y is UP.
- Positive theta is ANTICLOCKWISE, and theta = 0 is at the 3 o'clock position.
  ... so for a point (x=1, y=0), positive rotation moves it in the direction of
  INCREASING y.
  When you rotate by theta, you rotate anticlockwise.
  https://en.wikipedia.org/wiki/Rotation_of_axes

The Qt coordinate system
===============================================================================

- Positive x is to the right.
- Positive y is DOWN. (This matches commonplace screen coordinates; the origin
  is at the top left.)
  http://doc.qt.io/qt-5.8/coordsys.html

- When you rotate a coordinate system, rotation angles are CLOCKWISE.
  http://doc.qt.io/qt-5.8/qpainter.html#rotate
  ... so for a point (x=1, y=0), positive rotation moves it in the direction of
  INCREASING y.

- But when you draw a pie, rotation angles are ANTICLOCKWISE, and zero degrees
  is in the 3 o'clock position.
  http://doc.qt.io/qt-5.8/qpainter.html#drawPie

- Other ANTICLOCKWISE bits:
  - QTranform::rotate
    http://doc.qt.io/qt-5.8/qtransform.html#rotate

- Qt also uses a "positive ANTICLOCKWISE" system for its graphs, though that's
  more obvious as it's mimicking standard graph geometry here.
  https://doc.qt.io/qt-5/qtcharts-polarchart-example.html

Which representation to use internally for polar coordinates?
===============================================================================

- Any sophisticated representations are going to assume a standard Cartesian
  system and the most important part of that isn't "up"/"down" but the fact
  that positive angles are anticlockwise WITH RESPECT TO "x right, y up", i.e.
  that positive rotation moves the point (x=1, y=0) in the direction of
  INCREASING y.

  That's helpful so we can use standard representations like
        x = r * cos(theta)      y = r * sin(theta)
  not
        x = r * cos(theta)      y = -r * sin(theta)

- That means angles are clockwise in the standard Qt coordinates.

- So we'll use that when we refer to "polar", and convert explicitly for those
  places (like pie drawing) where anticlockwise angles are required.

Compass headings
===============================================================================

- These are based on the idea of "North up" (though also support a
  transformation via an "alternative North"), and positive rotation is
  CLOCKWISE.

Other notes on Qt coordinates
===============================================================================

- QPainter::drawText()

  "The y-position is used as the baseline of the font."

   0123456789
  0   |
  1   SSOOMMEE  TTEEXXTT
  2   SSOOMMEE  TTEEXXTT
  3 - SSOOMMEE  TTEEXXTT -      [descenders go below line?]
  4   |

  So if you draw at y = 3, it'll be bottom-aligned there.
  To top-align it, add its height to the y coordinate.
  To vcentre-align it, add half its height to the y coordinate.

  To left-align it, plot at the unmodified x coordinate.
  To centre-align it, subtract half its width from the x coordinate.
  To right-align it, subtract its width from the x coordinate.

*/

extern const qreal DEG_0;
extern const qreal DEG_90;
extern const qreal DEG_270;
extern const qreal DEG_180;
extern const qreal DEG_360;

int sixteenthsOfADegree(qreal degrees);

inline qreal clockwiseToAnticlockwise(qreal degrees) { return -degrees; }
inline qreal anticlockwiseToClockwise(qreal degrees) { return -degrees; }

qreal normalizeHeading(qreal heading_deg);
bool headingNearlyEq(qreal heading_deg, qreal value_deg);
bool headingInRange(qreal first_bound_deg,
                    qreal heading_deg,
                    qreal second_bound_deg,
                    bool inclusive = false);
qreal convertHeadingFromTrueNorth(qreal true_north_heading_deg,
                                  qreal pseudo_north_deg,
                                  bool normalize = true);
qreal convertHeadingToTrueNorth(qreal pseudo_north_heading_deg,
                                qreal pseudo_north_deg,
                                bool normalize = true);

QPointF polarToCartesian(qreal r, qreal theta_degrees);
qreal distanceBetween(const QPointF& from, const QPointF& to);
qreal polarTheta(const QPointF& from, const QPointF& to);
qreal polarTheta(const QPointF& to);
qreal polarThetaToHeading(qreal theta_deg, qreal north_deg = 0.0);
qreal headingToPolarTheta(qreal heading_deg, qreal north_deg = 0.0,
                          bool normalize = true);
qreal headingDegrees(const QPointF& from, const QPointF& to,
                     qreal north_deg = 0.0);
LineSegment lineFromPointInHeadingWithRadius(const QPointF& point,
                                             qreal heading_deg,
                                             qreal north_deg = 0.0,
                                             qreal radius = QWIDGETSIZE_MAX);
bool lineCrossesHeadingWithinRadius(const QPointF& from, const QPointF& to,
                                    const QPointF& point, qreal heading_deg,
                                    qreal north_deg = 0.0,
                                    qreal radius = QWIDGETSIZE_MAX);
bool linePassesBelowPoint(const QPointF& from, const QPointF& to,
                          const QPointF& point);

}  // namespace geometry
