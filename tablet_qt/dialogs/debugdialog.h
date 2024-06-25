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
#include <QDialog>

#include "lib/layoutdumper.h"

class DebugDialog : public QDialog
{
    // Dialogue to display a widget for debugging purposes
    Q_OBJECT

public:
    DebugDialog(
        QWidget* parent,
        QWidget* widget,
        const bool set_background_by_name = false,
        const bool set_background_by_stylesheet = true,
        const layoutdumper::DumperConfig& config
        = layoutdumper::DumperConfig(),
        const bool use_hfw_layout = true,
        const QString* dialog_stylesheet = nullptr
    );
};
