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
#include <Qt>
#include <QtTest/QtTest>

#include "qobjects/widgetpositioner.h"

class TestWidgetPositioner: public QObject
{
    Q_OBJECT

private slots:
    void testOrientationChangeClipsToScreenIfTooBig();

};


void TestWidgetPositioner::testOrientationChangeClipsToScreenIfTooBig()
{
    auto dialog = new QDialog();

    // Something silly
    dialog->resize(12345678, 12345678);
    auto positioner = new WidgetPositioner(dialog);

    // The orientation actually gets ignored but we have to put in something
    const bool ok = QMetaObject::invokeMethod(positioner, "orientationChanged",
                                              Qt::PortraitOrientation);
    QVERIFY(ok);

    QRect screen_geometry = dialog->screen()->availableGeometry();
    qDebug() << "Screen size:";
    qDebug() << screen_geometry;

    QCOMPARE(dialog->width(), screen_geometry.width());
    QCOMPARE(dialog->height(), screen_geometry.height());

}

QTEST_MAIN(TestWidgetPositioner)

#include "testwidgetpositioner.moc"
