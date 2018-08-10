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

#include "whiskerapi.h"
#include <QDebug>
#include "lib/convert.h"
#include "whisker/whiskerconstants.h"

using namespace whiskerconstants;

namespace whiskerapi {

// ============================================================================
// Helper functions
// ============================================================================

QString onVal(bool on)
{
    return on ? VAL_ON : VAL_OFF;
}


// ============================================================================
// Helper structs
// ============================================================================

// ----------------------------------------------------------------------------
// Pen
// ----------------------------------------------------------------------------

Pen::Pen(int width, const QColor& colour, PenStyle style) :
    width(width),
    colour(colour),
    style(style)
{
}


QString Pen::whiskerOptionString() const
{
    const QStringList args{
        FLAG_PEN_COLOUR, rgbFromColour(colour),
        FLAG_PEN_WIDTH, QString::number(width),
        FLAG_PEN_STYLE, PEN_STYLE_FLAGS[style],
    };
    return msgFromArgs(args);
}


// ----------------------------------------------------------------------------
// Brush
// ----------------------------------------------------------------------------

Brush::Brush(const QColor& colour, const QColor& bg_colour, bool opaque,
             BrushStyle style, BrushHatchStyle hatch_style) :
    colour(colour),
    bg_colour(bg_colour),
    opaque(opaque),
    style(style),
    hatch_style(hatch_style)
{
}


QString Brush::whiskerOptionString() const
{
    QStringList args{BRUSH_STYLE_FLAGS[style]};
    if (style == BrushStyle::Solid) {
        args.append(rgbFromColour(colour));
    } else if (style == BrushStyle::Hatched) {
        args.append(BRUSH_HATCH_VALUES[hatch_style]);
        args.append(rgbFromColour(colour));
        if (opaque) {
            args.append(FLAG_BRUSH_OPAQUE);
            args.append(FLAG_BRUSH_BACKGROUND);
            args.append(rgbFromColour(bg_colour));
        } else {
            args.append(FLAG_BRUSH_TRANSPARENT);
        }
    }
    return msgFromArgs(args);
}


// ============================================================================
// Display object definition classes
// ============================================================================

QString DisplayObject::optionString() const
{
    return msgFromArgs(options());
}


QStringList Text::options() const
{
    QStringList args{
        VAL_OBJTYPE_TEXT,
        pointCoordinates(pos),
        FLAG_HEIGHT, QString::number(height),
        FLAG_TEXT_WEIGHT, QString::number(weight),
        italic ? FLAG_TEXT_ITALIC : "",
        underline ? FLAG_TEXT_UNDERLINE : "",
        opaque ? FLAG_TEXT_OPAQUE : "",
        FLAG_TEXT_COLOUR, rgbFromColour(colour),
        FLAG_BACKCOLOUR, rgbFromColour(bg_colour),
        TEXT_HALIGN_FLAGS[halign],
        TEXT_VALIGN_FLAGS[valign],
    };
    if (!font.isEmpty()) {
        args.append({FLAG_FONT, quote(font)});
    }
    return args;
}


QStringList Bitmap::options() const
{
    return QStringList{
        VAL_OBJTYPE_BITMAP,
        pointCoordinates(pos),
        quote(filename),
        stretch ? FLAG_BITMAP_STRETCH : FLAG_BITMAP_CLIP,
        FLAG_HEIGHT, QString::number(height),
        FLAG_WIDTH, QString::number(width),
        HALIGN_FLAGS[halign],
        VALIGN_FLAGS[valign],
    };
}


QStringList Line::options() const
{
    return QStringList{
        VAL_OBJTYPE_LINE,
        pointCoordinates(start),
        pointCoordinates(end),
        pen.whiskerOptionString(),
    };
}


QStringList Arc::options() const
{
    return QStringList{
        VAL_OBJTYPE_ARC,
        rectCoordinates(rect),
        pointCoordinates(start),
        pointCoordinates(end),
        pen.whiskerOptionString(),
    };
}


QStringList Bezier::options() const
{
    return QStringList{
        VAL_OBJTYPE_BEZIER,
        pointCoordinates(start),
        pointCoordinates(control1),
        pointCoordinates(control2),
        pointCoordinates(end),
        pen.whiskerOptionString(),
    };
}


QStringList Chord::options() const
{
    return QStringList{
        VAL_OBJTYPE_CHORD,
        rectCoordinates(rect),
        pointCoordinates(line_start),
        pointCoordinates(line_end),
        pen.whiskerOptionString(),
        brush.whiskerOptionString(),
    };
}


QStringList Ellipse::options() const
{
    return QStringList{
        VAL_OBJTYPE_ELLIPSE,
        rectCoordinates(rect),
        pen.whiskerOptionString(),
        brush.whiskerOptionString(),
    };
}


QStringList Pie::options() const
{
    return QStringList{
        VAL_OBJTYPE_PIE,
        rectCoordinates(rect),
        pointCoordinates(arc_start),
        pointCoordinates(arc_end),
        pen.whiskerOptionString(),
        brush.whiskerOptionString(),
    };
}


QStringList Polygon::options() const
{
    if (points.size() < 3) {
        qWarning("Whisker polygon used with fewer than 3 points; will fail");
        return QStringList();
    }
    QStringList args{
        VAL_OBJTYPE_POLYGON,
        QString::number(points.size()),
    };
    for (const QPoint& point : points) {
        args.append(pointCoordinates(point));
    }
    args.append({
        alternate ? FLAG_POLYGON_ALTERNATE : FLAG_POLYGON_WINDING,
        pen.whiskerOptionString(),
        brush.whiskerOptionString(),
    });
    return args;
}


QStringList Rectangle::options() const
{
    return QStringList{
        VAL_OBJTYPE_RECTANGLE,
        rectCoordinates(rect),
        pen.whiskerOptionString(),
        brush.whiskerOptionString(),
    };
}


QStringList RoundRect::options() const
{
    return QStringList{
        VAL_OBJTYPE_ROUNDRECT,
        rectCoordinates(rect),
        sizeCoordinates(ellipse_size),
        pen.whiskerOptionString(),
        brush.whiskerOptionString(),
    };
}


QStringList CamcogQuadPattern::options() const
{
    const int required_size = 8;
    if (top_left_patterns.size() != required_size ||
            top_right_patterns.size() != required_size ||
            bottom_left_patterns.size() != required_size ||
            bottom_right_patterns.size() != required_size) {
        qWarning("Whisker CamcogQuadPattern used with wrong vector size; will fail");
        return QStringList();
    }

    auto vectorPattern = [](const QVector<int>& v) -> QString {
        QStringList numbers;
        for (const int n : v) {
            numbers.append(QString::number(n));
        }
        return numbers.join(SPACE);
    };

    return QStringList{
        VAL_OBJTYPE_CAMCOGQUADPATTERN,
        pointCoordinates(pos),
        sizeCoordinates(pixel_size),
        vectorPattern(top_left_patterns),
        vectorPattern(top_right_patterns),
        vectorPattern(bottom_left_patterns),
        vectorPattern(bottom_right_patterns),
        rgbFromColour(top_left_colour),
        rgbFromColour(top_right_colour),
        rgbFromColour(bottom_left_colour),
        rgbFromColour(bottom_right_colour),
        rgbFromColour(bg_colour),
    };
}


QStringList Video::options() const
{
    return QStringList{
        VAL_OBJTYPE_VIDEO,
        pointCoordinates(pos),
        quote(filename),
        loop ? FLAG_LOOP : FLAG_VIDEO_NOLOOP,
        VIDEO_PLAYMODE_FLAGS[playmode],
        FLAG_WIDTH, QString::number(width),
        FLAG_HEIGHT, QString::number(height),
        play_audio ? FLAG_VIDEO_AUDIO : FLAG_VIDEO_NOAUDIO,
        HALIGN_FLAGS[halign],
        VALIGN_FLAGS[valign],
        FLAG_BACKCOLOUR, rgbFromColour(bg_colour),
    };
}


// ============================================================================
// Helper functions
// ============================================================================

bool onOffToBoolean(const QString& msg)
{
    return msg == VAL_ON;
}


QString quote(const QString& s)
{
    return QUOTE + s + QUOTE;  // suboptimal! Doesn't escape quotes.
    // Mind you, don't think Whisker deals with that anyway.
}


QString msgFromArgs(const QStringList& args)
{
    QStringList nonempty_args;
    for (const QString& arg : args) {
        if (!arg.isEmpty()) {
            nonempty_args.append(arg);
        }
    }
    return nonempty_args.join(SPACE);
}


QString rgbFromColour(const QColor& colour)
{
    return QString("%1 %2 %3").arg(colour.red(), colour.green(), colour.blue());
}


QString pointCoordinates(const QPoint& point)
{
    return QString("%1 %2").arg(point.x(), point.y());
}


QString rectCoordinates(const QRect& rect)
{
    return QString("%1 %2 %3 %4").arg(
        QString::number(rect.left()),
        QString::number(rect.top()),
        QString::number(rect.right()),
        QString::number(rect.bottom())
    );
}


QString sizeCoordinates(const QSize& size)
{
    return QString("%1 %2").arg(size.width(), size.height());
}



}  // namespace whiskerapi

