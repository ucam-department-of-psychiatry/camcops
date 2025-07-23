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

#pragma once
#include <Qt>

class QColor;
class QLayout;
class QObject;
class QPlainTextEdit;
class QSize;
class QString;
class QVariant;
class QWidget;

namespace widgetfunc {

// ============================================================================
// Widget manipulations, and other Qt internals
// ============================================================================

// Set a widget's background colour by setting its CSS stylesheet.
void setBackgroundColour(QWidget* widget, const QColor& colour);

// Set a widget's background colour and "pressed" background colour
// by setting its CSS stylesheet.
void setBackgroundAndPressedColour(
    QWidget* widget, const QColor& background, const QColor& pressed
);

// Delete all children of a widget.
void removeAllChildWidgets(QObject* object);

// Combines a horizontal and a vertical alignment into an alignment object
// that carries the same information jointly.
Qt::Alignment combineAlignment(Qt::Alignment halign, Qt::Alignment valign);

// Repolishes the widget.  Calls the widget style's unpolish() then polish()
// functions, then the widget's update().
void repolish(QWidget* widget);

// Calls the widget's setProperty() with a property name/value pair, converting
// to the requisite Qt types on the way. Optionally, repolishes the widget.
void setProperty(
    QWidget* widget,
    const QString& property,
    const QVariant& value,
    bool repolish = true
);

// Converts a bool to "true" or "false" (for use in CSS).
QString cssBoolean(bool value);

// And some specific ones:

// Sets the widget's "italic" property.
void setPropertyItalic(QWidget* widget, bool italic, bool repolish = true);

// Sets the widget's "missing" property.
void setPropertyMissing(QWidget* widget, bool missing, bool repolish = true);

// Clear all widgets from a layout
void clearLayout(QLayout* layout, bool delete_widgets = true);

// Handy functions:

// Scrolls an editor to the end (bottom left).
void scrollToEnd(QPlainTextEdit* editor);

// Scrolls an editor to the top (top left).
void scrollToStart(QPlainTextEdit* editor);

// Calculates the minimum size a widget title will need depending on the
// platform
QSize minimumSizeForTitle(
    const QWidget* widget, bool include_app_name = false
);


}  // namespace widgetfunc
