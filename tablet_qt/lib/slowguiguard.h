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
#include <QPointer>
#include <QString>

#include "common/textconst.h"

class QApplication;
class QWidget;
class WaitBox;

class SlowGuiGuard
{
    // Create an instance of this object on the stack in a block containing
    // a slow GUI operation. It will:
    //  (1) show a wait box (on construction)
    //  (2) refresh the GUI manually using processEvents() (on construction)
    //  ... then you do your slow GUI thing
    //  ... and on destruction:
    //  (3) clear the wait box.
    //
    // Only one wait box can be created at any given time (detected by a
    // static member variable).
    //
    // You can also create an instance of this object on the heap, but be
    // careful!

public:
    SlowGuiGuard(
        QApplication& app,
        QWidget* parent,
        const QString& text = QStringLiteral("Operation in progress..."),
        const QString& title = TextConst::pleaseWait(),
        int minimum_duration_ms = 100
    );
    ~SlowGuiGuard();

protected:
    QPointer<WaitBox> m_wait_box;

    // "A wait box is open."
    static bool s_waiting;
};
