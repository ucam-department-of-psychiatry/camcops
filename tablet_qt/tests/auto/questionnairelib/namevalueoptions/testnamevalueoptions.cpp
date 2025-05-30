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

#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/namevaluepair.h"

class TestNameValueOptions : public QObject
{
    Q_OBJECT

private slots:
    void testInitializedWithList();
};

void TestNameValueOptions::testInitializedWithList()
{
    NameValueOptions options{
        {"A", 1},
        {"B", 2},
        {"C", 3},
    };

    QCOMPARE(options.nameFromPosition(0), "A");
    QCOMPARE(options.valueFromPosition(0), 1);
    QCOMPARE(options.nameFromPosition(1), "B");
    QCOMPARE(options.valueFromPosition(1), 2);
    QCOMPARE(options.nameFromPosition(2), "C");
    QCOMPARE(options.valueFromPosition(2), 3);
}

QTEST_MAIN(TestNameValueOptions)

#include "testnamevalueoptions.moc"
