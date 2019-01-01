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
#include <QColor>
#include <QDebug>
#include <QDateTime>
#include <QRect>
#include <QString>
#include <QStringList>
#include "whisker/whiskerconstants.h"

namespace whiskerapi {

// ============================================================================
// Helper functions
// ============================================================================

QString onVal(bool on);

// ============================================================================
// Helper structs
// ============================================================================

struct Pen {
    Pen(int width = 1,
        const QColor& colour = whiskerconstants::WHITE,
        whiskerconstants::PenStyle style = whiskerconstants::PenStyle::Solid);
    QString whiskerOptionString() const;

    int width;
    QColor colour;
    whiskerconstants::PenStyle style;
};


struct Brush {
    Brush(const QColor& colour = whiskerconstants::WHITE,
          const QColor& bg_colour = whiskerconstants::BLACK,
          bool opaque = true,
          whiskerconstants::BrushStyle style = whiskerconstants::BrushStyle::Solid,
          whiskerconstants::BrushHatchStyle hatch_style = whiskerconstants::BrushHatchStyle::Cross);
    QString whiskerOptionString() const;

    QColor colour;
    QColor bg_colour;
    bool opaque;
    whiskerconstants::BrushStyle style;
    whiskerconstants::BrushHatchStyle hatch_style;
};


struct LogOptions {
    bool events = true;
    bool key_events = true;
    bool client_client = true;
    bool comms = false;
    bool signature = true;
};


struct DisplayCreationOptions {
    bool resize = true;
    bool directdraw = true;
    bool debug_touches = false;
    QRect rectangle;
};


// ============================================================================
// Display object definition classes
// ============================================================================

class DisplayObject {
public:
    virtual QStringList options() const = 0;
    QString optionString() const;
};


class Arc : public DisplayObject {
public:
    Arc(const QRect& rect, const QPoint& start, const QPoint& end,
        const Pen& pen = Pen());
    virtual QStringList options() const override;

    QRect rect;  // The arc fits into the rect.
    QPoint start;
    QPoint end;
    Pen pen;
};


class Bezier : public DisplayObject {
public:
    Bezier(const QPoint& start, const QPoint& control1, const QPoint& control2,
           const QPoint& end, const Pen& pen = Pen());
    virtual QStringList options() const override;

    QPoint start;
    QPoint control1;  // The control points "pull" the curve.
    QPoint control2;
    QPoint end;
    Pen pen;
};


class Bitmap : public DisplayObject {
public:
    Bitmap(const QPoint& pos, const QString& filename,
           bool stretch = false, int height = -1, int width = -1,
           whiskerconstants::VerticalAlign valign = whiskerconstants::VerticalAlign::Top,
           whiskerconstants::HorizontalAlign halign = whiskerconstants::HorizontalAlign::Left);
    virtual QStringList options() const override;

    QPoint pos;
    QString filename;
    bool stretch = false;
    int height = -1;
    int width = -1;
    whiskerconstants::VerticalAlign valign = whiskerconstants::VerticalAlign::Top;
    whiskerconstants::HorizontalAlign halign = whiskerconstants::HorizontalAlign::Left;
};


class CamcogQuadPattern : public DisplayObject {
public:
    CamcogQuadPattern(const QPoint& pos, const QSize& pixel_size,
                      const QVector<uint8_t>& top_left_patterns,
                      const QVector<uint8_t>& top_right_patterns,
                      const QVector<uint8_t>& bottom_left_patterns,
                      const QVector<uint8_t>& bottom_right_patterns,
                      const QColor& top_left_colour,
                      const QColor& top_right_colour,
                      const QColor& bottom_left_colour,
                      const QColor& bottom_right_colour,
                      const QColor& bg_colour);
    virtual QStringList options() const override;

    // See Whisker docs.
    QPoint pos;
    QSize pixel_size;
    QVector<uint8_t> top_left_patterns;
    QVector<uint8_t> top_right_patterns;
    QVector<uint8_t> bottom_left_patterns;
    QVector<uint8_t> bottom_right_patterns;
    QColor top_left_colour;
    QColor top_right_colour;
    QColor bottom_left_colour;
    QColor bottom_right_colour;
    QColor bg_colour;
};


class Chord : public DisplayObject {
public:
    Chord(const QRect& rect, const QPoint& line_start, const QPoint& line_end,
          const Pen& pen = Pen(), const Brush& brush = Brush());
    virtual QStringList options() const override;

    // The chord is the intersection of an ellipse (defined by the rect)
    // and a line that intersects it.
    QRect rect;
    QPoint line_start;
    QPoint line_end;
    Pen pen;
    Brush brush;
};


class Ellipse : public DisplayObject {
public:
    Ellipse(const QRect& rect,
            const Pen& pen = Pen(), const Brush& brush = Brush());
    virtual QStringList options() const override;

    // The ellipse fits into the rectangle (and its centre is at the centre
    // of the rectangle).
    QRect rect;
    Pen pen;
    Brush brush;
};


class Line : public DisplayObject {
public:
    Line(const QPoint& start, const QPoint& end, const Pen& pen = Pen());
    virtual QStringList options() const override;

    QPoint start;
    QPoint end;
    Pen pen;
};


class Pie : public DisplayObject {
public:
    Pie(const QRect& rect, const QPoint& arc_start, const QPoint& arc_end,
        const Pen& pen = Pen(), const Brush& brush = Brush());
    virtual QStringList options() const override;

    // See Whisker docs.
    QRect rect;
    QPoint arc_start;
    QPoint arc_end;
    Pen pen;
    Brush brush;
};


class Polygon : public DisplayObject {
public:
    Polygon(const QVector<QPoint>& points,
            const Pen& pen = Pen(), const Brush& brush = Brush(),
            bool alternate = false);
    virtual QStringList options() const override;

    // See Whisker docs.
    QVector<QPoint> points;
    Pen pen;
    Brush brush;
    bool alternate = false;
};


class Rectangle : public DisplayObject {
public:
    Rectangle(const QRect& rect,
              const Pen& pen = Pen(), const Brush& brush = Brush());
    virtual QStringList options() const override;

    // See Whisker docs.
    QRect rect;
    Pen pen;
    Brush brush;
};


class RoundRect : public DisplayObject {
public:
    RoundRect(const QRect& rect, const QSize& ellipse_size,
              const Pen& pen = Pen(), const Brush& brush = Brush());
    virtual QStringList options() const override;

    // See Whisker docs.
    QRect rect;
    QSize ellipse_size;
    Pen pen;
    Brush brush;
};


class Text : public DisplayObject {
public:
    Text(const QPoint& pos, const QString& text, int height = 0,
         const QString& font = "");
    virtual QStringList options() const override;

    QPoint pos;
    QString text;
    int height = 0;  // 0 means some vaguely sensible default
    QString font;  // empty gives a system font
    bool italic = false;
    bool underline = false;
    int weight = 0;  // 0 for default weight
    QColor colour = whiskerconstants::WHITE;
    bool opaque = false;
    QColor bg_colour = whiskerconstants::BLACK;
    whiskerconstants::TextVerticalAlign valign = whiskerconstants::TextVerticalAlign::Top;
    whiskerconstants::TextHorizontalAlign halign = whiskerconstants::TextHorizontalAlign::Left;
};


class Video : public DisplayObject {
public:
    Video(const QPoint& pos, const QString& filename, bool loop = false,
          whiskerconstants::VideoPlayMode playmode = whiskerconstants::VideoPlayMode::Wait,
          int width = -1, int height = -1);
    virtual QStringList options() const override;

    // See Whisker docs.
    QPoint pos;
    QString filename;
    bool loop = false;
    whiskerconstants::VideoPlayMode playmode = whiskerconstants::VideoPlayMode::Wait;
    int width = -1;
    int height = -1;
    bool play_audio = true;
    whiskerconstants::VerticalAlign valign = whiskerconstants::VerticalAlign::Top;
    whiskerconstants::HorizontalAlign halign = whiskerconstants::HorizontalAlign::Left;
    QColor bg_colour = whiskerconstants::BLACK;
};


// ============================================================================
// Helper functions
// ============================================================================

bool onOffToBoolean(const QString& msg);
QString quote(const QString& s);
QString msgFromArgs(const QStringList& args);
QString rgbFromColour(const QColor& colour);
QString pointCoordinates(const QPoint& point);
QString rectCoordinates(const QRect& rect);
QString sizeCoordinates(const QSize& size);


}  // namespace whiskerapi
