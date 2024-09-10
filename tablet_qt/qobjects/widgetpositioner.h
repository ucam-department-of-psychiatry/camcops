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

    Based on the DialogPositioner class in https://github.com/f4exb/sdrangel/
    v7.21.1, which has the following licence:

    Copyright (C) 2022-2023 Jon Beniston, M7RCE <jon@beniston.com>
    Copyright (C) 2023 Mohamed <mohamedadlyi@github.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation as version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License V3 for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

*/
#pragma once
#include <QWidget>

class WidgetPositioner : public QObject
{
    // Helper class to reposition widgets sensibly on orientation change.
    //
    // Currently we cannot rely on Android and iOS to handle this:
    // https://bugreports.qt.io/browse/QTBUG-91363
    // https://bugreports.qt.io/browse/QTBUG-109127

    Q_OBJECT

public:
    WidgetPositioner(QWidget* widget);
    // ... widget will become our parent and own us

protected:
    void sizeToScreen();
    void centre();
    bool eventFilter(QObject* obj, QEvent* event) override;

private:
    QWidget* m_widget;
private slots:
    void orientationChanged(Qt::ScreenOrientation orientation);
};
