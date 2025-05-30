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

#include "horizontalline.h"

#include <QPainter>
#include <QStyleOption>

/*

===============================================================================
Horizontal/vertical lines
===============================================================================
- Option 1: QFrame
- Option 2: QWidget
    http://stackoverflow.com/questions/10053839/how-does-designer-create-a-line-widget

- Complex interaction between C++ properties and stylesheets.
  https://doc.qt.io/qt-6.5/stylesheet-examples.html#customizing-qframe

- If you inherit from a QWidget, you need to implement the stylesheet painter:
  http://stackoverflow.com/questions/7276330/qt-stylesheet-for-custom-widget
  https://doc.qt.io/qt-6.5/stylesheet-reference.html

*/

HorizontalLine::HorizontalLine(const int width, QWidget* parent) :
    QWidget(parent)
{
    setFixedHeight(width);
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    // setStyleSheet(QString("background-color: %1;").arg(colour));
}

void HorizontalLine::paintEvent(QPaintEvent*)
{
    // Must do this for stylesheets to work.
    QStyleOption opt;
    opt.initFrom(this);
    QPainter p(this);
    style()->drawPrimitive(QStyle::PE_Widget, &opt, &p, this);
}
