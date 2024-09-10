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

#include <QPushButton>
#include <QtTest/QtTest>

#include "layouts/flowlayouthfw.h"

class TestFlowLayoutHfw : public QObject
{
    Q_OBJECT

private slots:
    void testMinimumSizeAddsMargins();
};

void TestFlowLayoutHfw::testMinimumSizeAddsMargins()
{
    FlowLayoutHfw layout;
    auto button = new QPushButton();

    layout.addWidget(button);

    const int left = 1;
    const int top = 2;
    const int right = 4;
    const int bottom = 8;

    layout.setContentsMargins(left, top, right, bottom);

    QCOMPARE(layout.minimumSize(), QSize(left + right, top + bottom));
}

QTEST_MAIN(TestFlowLayoutHfw)

#include "testflowlayouthfw.moc"
