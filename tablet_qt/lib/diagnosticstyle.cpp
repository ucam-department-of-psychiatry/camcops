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
*/

// https://stackoverflow.com/questions/5909907/drawing-an-overlay-on-top-of-an-applications-window

#include "diagnosticstyle.h"

#include <QBrush>
#include <QPainter>
#include <QWidget>

void DiagnosticStyle::drawControl(
    ControlElement element,
    const QStyleOption* option,
    QPainter* painter,
    const QWidget* widget
) const
{
    QCommonStyle::drawControl(element, option, painter, widget);
    if (widget && painter) {
        // draw a border around the widget
        painter->setPen(QColor("red"));
        painter->drawRect(widget->rect());

        // show the classname of the widget
        QBrush translucentBrush(QColor(255, 246, 240, 100));
        painter->fillRect(widget->rect(), translucentBrush);
        painter->setPen(QColor("darkblue"));
        painter->drawText(
            widget->rect(),
            Qt::AlignLeft | Qt::AlignVCenter,
            widget->metaObject()->className()
        );
    }
};
