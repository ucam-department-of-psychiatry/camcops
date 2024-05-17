
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

#include <QDialog>
#include <QEvent>
#include <QObject>
#include <QScreen>
#include <QTimer>
#include <QWidget>

#include "lib/uifunc.h"

#include "centreddialog.h"

CentredDialog::CentredDialog(QWidget* parent) : QDialog(parent)
{
    centre();
    installEventFilter(this);

    QScreen *screen = uifunc::screen();
    connect(screen, &QScreen::orientationChanged,
            this, &CentredDialog::orientationChanged);
}

void CentredDialog::orientationChanged(Qt::ScreenOrientation orientation)
{
    Q_UNUSED(orientation)

    // Not reliable to retrieve the screen or dialog geometry at this point.
    // https://bugreports.qt.io/browse/QTBUG-91363
    // https://bugreports.qt.io/browse/QTBUG-109127

    // hide() followed by show() will resize and reposition the dialog on iOS
    // but this crashes on Android. So we do this ourselves after a short delay.
    QTimer::singleShot(200, this, &CentredDialog::centre);
}


void CentredDialog::centre()
{
    sizeToScreen();

    const int x = (uifunc::screenAvailableWidth() - width()) / 2;
    const int y = (uifunc::screenAvailableHeight() - height()) / 2;
    move(x, y);
}


void CentredDialog::sizeToScreen()
{
    const int screen_width = uifunc::screenAvailableWidth();
    const int screen_height = uifunc::screenAvailableHeight();

    bool changed = false;

    int new_width = width();
    int new_height = height();

    if (new_width > screen_width)
    {
        new_width = screen_width;
        changed = true;
    }
    if (new_height > screen_height)
    {
        new_height = screen_height;
        changed = true;
    }
    if (changed) {
        resize(new_width, new_height);
    }
}


bool CentredDialog::eventFilter(QObject *obj, QEvent *event)
{
    if (event->type() == QEvent::Show)
    {
        centre();
    }

    return QObject::eventFilter(obj, event);
}
