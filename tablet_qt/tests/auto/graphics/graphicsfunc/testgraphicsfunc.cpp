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

#include <QGraphicsScene>
#include <QPushButton>
#include <QtTest/QtTest>
#include <QVBoxLayout>

#include "graphics/graphicsfunc.h"

class TestGraphicsfunc : public QObject
{
    Q_OBJECT

private slots:
    void testMakeTextButtonSetsMarginToZero();
};

using namespace graphicsfunc;

void TestGraphicsfunc::testMakeTextButtonSetsMarginToZero()
{
    QGraphicsScene scene = QGraphicsScene();
    const QRectF rect(0, 0, 100, 100);
    // These values are not important for the test
    const ButtonConfig config(
        5,
        20,
        QColor(255, 255, 255),
        Qt::AlignCenter,
        QColor(0, 0, 255),
        QColor(0, 255, 0),
        QPen(QBrush(QColor(255, 0, 0)), 5),
        5
    );

    const QString text = "Test";
    auto button_and_proxy = makeTextButton(&scene, rect, config, text);
    auto layout = button_and_proxy.button->layout();

    int left, top, right, bottom;

    layout->getContentsMargins(&left, &top, &right, &bottom);

    QCOMPARE(left, 0);
    QCOMPARE(top, 0);
    QCOMPARE(right, 0);
    QCOMPARE(bottom, 0);
}

QTEST_MAIN(TestGraphicsfunc)

#include "testgraphicsfunc.moc"
