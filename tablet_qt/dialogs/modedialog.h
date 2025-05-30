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
#include <QPointer>

#include "common/varconst.h"

class QButtonGroup;

class ModeDialog : public QDialog
{
    // Dialogue to select mode of operation.
    // MODAL and BLOCKING: call exec() and read mode() if it succeeds.

    Q_OBJECT

public:
    ModeDialog(
        int previous_choice = varconst::MODE_NOT_SET, QWidget* parent = nullptr
    );
    int mode() const;

protected:
    QPointer<QButtonGroup> m_mode_selector;
};
