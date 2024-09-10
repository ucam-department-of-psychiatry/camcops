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
#include <QValidator>

#include "qobjects/strictdoublevalidator.h"

#define TESTSTRICTDOUBLE_INCLUDE_RANDOM  // should generally be defined

class TestStrictDoubleValidator : public QObject
{
    Q_OBJECT

private slots:
    void testValidateReturnsAcceptableIfEmptyAndEmptyAllowed();
    void testValidateReturnsIntermediateIfEmptyAndEmptyNotAllowed();
    void testValidateReturnsInvalidIfTooManyDecimalPlaces();
    void testValidateReturnsIntermediateIfMinusAndNegativeAllowed();
    void testValidateReturnsInvalidIfMinusAndNegativeNotAllowed();
    void testValidateReturnsIntermediateIfPlusAndPositiveAllowed();
    void testValidateReturnsInvalidIfPlusAndPositiveNotAllowed();
    void testValidateReturnsInvalidIfNotADouble();
    void testValidateReturnsAcceptableIfADoubleWithinRange();
    void testValidateReturnsIntermediateIfNegativeZero();
    void testValidateReturnsInvalidIfTopNegativeAndNoMinus();
    void testValidateReturnsIntermediateIfHasValidStart();
    void testValidateReturnsInvalidIfHasInvalidStart();
    void testValidateReturnsIntermediateIfZeroAndRangeGreaterThanZero();
#ifdef TESTSTRICTDOUBLE_INCLUDE_RANDOM
    void testRandomNumbersAndRanges();
#endif
    void testSpecificFailure1();
    void testSpecificFailure2();
};

void TestStrictDoubleValidator::
    testValidateReturnsAcceptableIfEmptyAndEmptyAllowed()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = true;
    QString text("");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Acceptable);
}

void TestStrictDoubleValidator::
    testValidateReturnsIntermediateIfEmptyAndEmptyNotAllowed()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::
    testValidateReturnsInvalidIfTooManyDecimalPlaces()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("3.1416");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::
    testValidateReturnsIntermediateIfMinusAndNegativeAllowed()
{
    const double bottom = -1.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("-");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::
    testValidateReturnsInvalidIfMinusAndNegativeNotAllowed()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("-");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::
    testValidateReturnsIntermediateIfPlusAndPositiveAllowed()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("+");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::
    testValidateReturnsInvalidIfPlusAndPositiveNotAllowed()
{
    const double bottom = -10.0;
    const double top = -1.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("+");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::testValidateReturnsInvalidIfNotADouble()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("not a double");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::
    testValidateReturnsAcceptableIfADoubleWithinRange()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("3.141");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Acceptable);
}

void TestStrictDoubleValidator::testValidateReturnsIntermediateIfNegativeZero()
{
    const double bottom = -0.2;
    const double top = -0.1;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("-0");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::
    testValidateReturnsInvalidIfTopNegativeAndNoMinus()
{
    const double bottom = -10;
    const double top = -1.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("1");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::testValidateReturnsIntermediateIfHasValidStart(
)
{
    const double bottom = 10.0;
    const double top = 20.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("1");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::testValidateReturnsInvalidIfHasInvalidStart()
{
    const double bottom = 10.0;
    const double top = 19.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("2");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    // This is exceptionally tricky.
    // Recursion (trying every potential keystroke) is slow.
    // In this example, "2" can be extended so it is smaller than top, e.g.
    // as "2.5". It can also be extended so that it's larger than bottom, e.g.
    // as "20". It can't be extended to satisfy both criteria.
    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::
    testValidateReturnsIntermediateIfZeroAndRangeGreaterThanZero()
{
    const double bottom = 0.01;
    const double top = 5;
    const int decimals = 2;
    const bool allow_empty = false;
    QString text("0");
    int pos = 0;

    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

#ifdef TESTSTRICTDOUBLE_INCLUDE_RANDOM
void TestStrictDoubleValidator::testRandomNumbersAndRanges()
{
    const int seed = 1234;
    const int num_tests = 1000;
    const int limit = 1000000;
    const int max_decimals = 10;  // a large number is likely to break things

    QRandomGenerator rng(seed);

    for (int test = 0; test < num_tests; ++test) {
        const int decimals = rng.bounded(0, max_decimals);

        const int factor = rng.bounded(-limit, limit);
        const double limit_1 = rng.generateDouble() * factor;
        const double limit_2 = rng.generateDouble() * factor;

        // Ensure that we don't specify ranges to more decimal places than
        // we will allow:
        const double bottom
            = QString::number(std::min(limit_1, limit_2), 'f', decimals)
                  .toDouble();
        const double top
            = QString::number(std::max(limit_1, limit_2), 'f', decimals)
                  .toDouble();

        const double number
            = QString::number(
                  rng.bounded(top - bottom) + bottom, 'f', decimals
            )
                  .toDouble();

        QString str_number;
        str_number.setNum(number);

        const bool allow_empty = false;
        int pos = 0;

        StrictDoubleValidator validator(
            bottom, top, decimals, allow_empty, nullptr
        );

        for (int c = 1; c <= str_number.length(); ++c) {
            QString typed = str_number.first(c);

            auto state = validator.validate(typed, pos);

            if (state == QValidator::Invalid) {
                qDebug().nospace()
                    << "Validation failed for " << typed << " from " << number
                    << ", range " << bottom << " to " << top << ", with "
                    << decimals << " dp";
                QVERIFY(false);
            }
        }

        QVERIFY(true);
    }
}
#endif

void TestStrictDoubleValidator::testSpecificFailure1()
{
    // An example thrown up by testRandomNumbersAndRanges()
    QString text("-1");  // intention: -124401
    const double bottom = -154620;
    const double top = -113217;
    const int decimals = 0;
    const bool allow_empty = false;
    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );
    int pos = 0;
    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::testSpecificFailure2()
{
    // An example thrown up by testRandomNumbersAndRanges()
    QString text("-69839.7");
    const double bottom = -70369.8;
    const double top = -57920.8;
    const int decimals = 1;
    const bool allow_empty = false;
    StrictDoubleValidator validator(
        bottom, top, decimals, allow_empty, nullptr
    );
    int pos = 0;
    QCOMPARE(validator.validate(text, pos), QValidator::Acceptable);
}

QTEST_MAIN(TestStrictDoubleValidator)

#include "teststrictdoublevalidator.moc"
