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

#include "progressbox.h"

#include "qobjects/widgetpositioner.h"

ProgressBox::ProgressBox(
    const QString& label,
    const QString& cancel_button_text,
    int minimum,
    const int maximum,
    QWidget* parent,
    Qt::WindowFlags f
) :
    QProgressDialog(label, cancel_button_text, minimum, maximum, parent, f)
{
    new WidgetPositioner(this);
}
