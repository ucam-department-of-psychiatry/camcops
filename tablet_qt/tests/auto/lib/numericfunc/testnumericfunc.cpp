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

#include "lib/numericfunc.h"

using namespace numeric;

class TestNumericFunc : public QObject
{
    Q_OBJECT

private slots:
    // Invalid because extendedDoubleMustBeLessThanBottom() returns true
    void testIsValidStartToDoubleFalseWhenNegativeAndBottomPositive();
    void testIsValidStartToDoubleFalseWhenBelowPositiveRangeEvenWhenExtended();
    void testIsValidStartToDoubleFalseWhenBelowPositiveRange();
    void testIsValidStartToDoubleFalseWhenBelowNegativeRangeEvenWhenExtended();
    void testIsValidStartToDoubleFalseWhenBelowNegativeRange();

    // Invalid because extendedDoubleMustBeLessThanBottom() returns false and
    // extendedDoubleMustExceedTop() returns true
    void testIsValidStartToDoubleFalseWhenPositiveAndTopNegative();
    void testIsValidStartToDoubleFalseWhenAbovePositiveRangeEvenWhenExtended();
    void testIsValidStartToDoubleFalseWhenAbovePositiveRange();
    void testIsValidStartToDoubleFalseWhenAboveNegativeRangeEvenWhenExtended();
};

void TestNumericFunc::
    testIsValidStartToDoubleFalseWhenNegativeAndBottomPositive()
{
    // Invalid because number is negative and bottom is positive. No need to
    // check any further because of the minus sign.
    const double number = -1;
    const double bottom = 1;
    const double top = 10;  // irrelevant
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

void TestNumericFunc::
    testIsValidStartToDoubleFalseWhenBelowPositiveRangeEvenWhenExtended()
{
    // Invalid because appending nines to number up to the length of top will
    // not make it greater than or equal to bottom.
    const double number = 1.01;
    const double bottom = 2;
    const double top = 3.0001;
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

void TestNumericFunc::testIsValidStartToDoubleFalseWhenBelowPositiveRange()
{
    // Invalid because number < bottom and you couldn't append more digits to
    // change that because of the length of top.
    const double number = 1;
    const double bottom = 2;
    const double top = 3;
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

void TestNumericFunc::
    testIsValidStartToDoubleFalseWhenBelowNegativeRangeEvenWhenExtended()
{
    // Invalid because appending zeros to number up to the length of bottom
    // will not make it greater than or equal to bottom
    const double number = -0.02;
    const double bottom = -0.012345;
    const double top = 10;  // irrelevant
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

void TestNumericFunc::testIsValidStartToDoubleFalseWhenBelowNegativeRange()
{
    // Invalid because number < bottom and you couldn't append more digits to
    // change that because of the length of bottom.
    const double number = -0.02;
    const double bottom = -0.01;
    const double top = 10;  // irrelevant
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

void TestNumericFunc::testIsValidStartToDoubleFalseWhenPositiveAndTopNegative()
{
    // Invalid because number is positive and top is negative. No need to
    // check any further because of the lack of minus sign.
    const double number = 1;
    const double bottom = -2;  // must be negative and less than number
    const double top = -1;
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

void TestNumericFunc::
    testIsValidStartToDoubleFalseWhenAbovePositiveRangeEvenWhenExtended()
{
    // Invalid because appending zeros to number up to the length of top will
    // not make it less than or equal to top
    const double number = 6;
    const double bottom = -5;
    const double top = 5.1234;
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

void TestNumericFunc::testIsValidStartToDoubleFalseWhenAbovePositiveRange()
{
    // Invalid because number > top and you couldn't append more digits to
    // change that because of the length of bottom.
    const double number = 6;
    const double bottom = -5;
    const double top = 5;
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

void TestNumericFunc::
    testIsValidStartToDoubleFalseWhenAboveNegativeRangeEvenWhenExtended()
{
    // Invalid because appending nines to number up to the length of bottom
    // will not make it less than or equal to top.
    const double number = -1.1;
    const double bottom = -5.1234;
    const double top = -2;
    const int max_dp = 5;

    QVERIFY(!isValidStartToDouble(number, bottom, top, max_dp));
}

QTEST_MAIN(TestNumericFunc)

#include "testnumericfunc.moc"
