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

#include <QtTest/QtTest>

#include "lib/margins.h"

class TestMargins : public QObject
{
    Q_OBJECT

private slots:
    void testGetContentsMarginsReturnsWidgetMargins();
};

void TestMargins::testGetContentsMarginsReturnsWidgetMargins()
{
    QWidget widget;

    const int left = 0;
    const int top = 10;
    const int right = 20;
    const int bottom = 50;

    widget.setContentsMargins(left, top, right, bottom);
    auto margins = Margins::getContentsMargins(&widget);

    QCOMPARE(margins.left(), left);
    QCOMPARE(margins.top(), top);
    QCOMPARE(margins.right(), right);
    QCOMPARE(margins.bottom(), bottom);
}

QTEST_MAIN(TestMargins)

#include "testmargins.moc"
