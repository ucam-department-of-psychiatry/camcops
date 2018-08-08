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
#include <QColor>
#include <QDebug>
#include <QDateTime>
#include <QString>
#include <QStringList>
#include "whisker/whiskerconstants.h"

namespace whiskerapi {

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


// ============================================================================
// Helper functions
// ============================================================================

bool onOffToBoolean(const QString& msg);
QString quote(const QString& s);
QString msgFromArgs(const QStringList& args);


// ============================================================================
// Whisker API handler
// ============================================================================

class WhiskerApi
{
    using ImmSendGetReplyFn = std::function<QString(const QStringList&)>;
    // ... function taking a "const QStringList&" parameter (a list of
    //     arguments to be joined with spaces and send to the Whisker server
    //     via the immediate socket) and returning a QString (the server's
    //     reply).

public:
    WhiskerApi(const ImmSendGetReplyFn& whisker_immsend_get_reply_fn,
               const QString& sysevent_prefix = "sys_");

protected:
    ImmSendGetReplyFn m_immsend_get_reply_fn;
    QString m_sysevent_prefix;
    unsigned int m_sysevent_counter;
};


}  // namespace whiskerapi
