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
#include <QProgressDialog>

// Prototypical use: modal, as per
// https://doc.qt.io/qt-6.5/qprogressdialog.html#details

class ProgressBox : public QProgressDialog
{
    // Progress dialogue.
    // MODAL.
    // NOT CURRENTLY USED.

    Q_OBJECT

public:
    ProgressBox(
        const QString& label_text,
        const QString& cancel_button_text,
        int minimum,
        int maximum,
        QWidget* parent = nullptr,
        Qt::WindowFlags f = Qt::WindowFlags()
    );
};
