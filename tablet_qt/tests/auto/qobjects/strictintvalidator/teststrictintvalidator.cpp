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

#include "qobjects/strictintvalidator.h"

#define TESTSTRICTINT_INCLUDE_RANDOM  // should generally be defined

class TestStrictIntValidator : public QObject
{
    Q_OBJECT

private slots:
    void testValidateReturnsAcceptableIfEmptyAndEmptyAllowed();
    void testValidateReturnsIntermediateIfEmptyAndEmptyNotAllowed();
    void testValidateReturnsInvalidIfDecimalPoint();
    void testValidateReturnsIntermediateIfMinusAndNegativeAllowed();
    void testValidateReturnsInvalidIfMinusAndNegativeNotAllowed();
    void testValidateReturnsIntermediateIfPlusAndPositiveAllowed();
    void testValidateReturnsInvalidIfPlusAndPositiveNotAllowed();
    void testValidateReturnsInvalidIfNotAnInt();
    void testValidateReturnsAcceptableIfAnIntWithinRange();
    void testValidateReturnsIntermediateIfNegativeZero();
    void testValidateReturnsInvalidIfTopNegativeAndNoMinus();
    void testValidateReturnsIntermediateIfHasValidStart();
    void testValidateReturnsInvalidIfHasInvalidStart();
    void testValidateReturnsIntermediateIfZeroAndRangeGreaterThanZero();
#ifdef TESTSTRICTINT_INCLUDE_RANDOM
    void testRandomNumbersAndRanges();
#endif
};

void TestStrictIntValidator::
    testValidateReturnsAcceptableIfEmptyAndEmptyAllowed()
{
    const int bottom = 0;
    const int top = 10;
    const bool allow_empty = true;
    QString text("");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Acceptable);
}

void TestStrictIntValidator::
    testValidateReturnsIntermediateIfEmptyAndEmptyNotAllowed()
{
    const int bottom = 0;
    const int top = 10;
    const bool allow_empty = false;
    QString text("");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictIntValidator::testValidateReturnsInvalidIfDecimalPoint()
{
    const int bottom = 0;
    const int top = 10;
    const bool allow_empty = false;
    QString text("3.1416");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictIntValidator::
    testValidateReturnsIntermediateIfMinusAndNegativeAllowed()
{
    const int bottom = -1;
    const int top = 10;
    const bool allow_empty = false;
    QString text("-");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictIntValidator::
    testValidateReturnsInvalidIfMinusAndNegativeNotAllowed()
{
    const int bottom = 0;
    const int top = 10;
    const bool allow_empty = false;
    QString text("-");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictIntValidator::
    testValidateReturnsIntermediateIfPlusAndPositiveAllowed()
{
    const int bottom = 0;
    const int top = 10;
    const bool allow_empty = false;
    QString text("+");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictIntValidator::
    testValidateReturnsInvalidIfPlusAndPositiveNotAllowed()
{
    const int bottom = -100;
    const int top = -1;
    const bool allow_empty = false;
    QString text("+");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictIntValidator::testValidateReturnsInvalidIfNotAnInt()
{
    const int bottom = 0;
    const int top = 10;
    const bool allow_empty = false;
    QString text("not an int");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictIntValidator::testValidateReturnsAcceptableIfAnIntWithinRange()
{
    const int bottom = 0;
    const int top = 10;
    const bool allow_empty = false;
    QString text("3");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Acceptable);
}

void TestStrictIntValidator::testValidateReturnsIntermediateIfNegativeZero()
{
    const int bottom = -2;
    const int top = -1;
    const bool allow_empty = false;
    QString text("-0");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictIntValidator::testValidateReturnsInvalidIfTopNegativeAndNoMinus(
)
{
    const int bottom = -10;
    const int top = -1;
    const bool allow_empty = false;
    QString text("1");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictIntValidator::testValidateReturnsIntermediateIfHasValidStart()
{
    const int bottom = 10;
    const int top = 20;
    const bool allow_empty = false;
    QString text("1");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestStrictIntValidator::testValidateReturnsInvalidIfHasInvalidStart()
{
    const int bottom = 10;
    const int top = 19;
    const bool allow_empty = false;
    QString text("2");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestStrictIntValidator::
    testValidateReturnsIntermediateIfZeroAndRangeGreaterThanZero()
{
    const int bottom = 1;
    const int top = 5;
    const bool allow_empty = false;
    QString text("0");
    int pos = 0;

    StrictIntValidator validator(bottom, top, allow_empty, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

#ifdef TESTSTRICTINT_INCLUDE_RANDOM
void TestStrictIntValidator::testRandomNumbersAndRanges()
{
    const int seed = 1234;
    const int num_tests = 1000;
    const int limit = 1000000;

    QRandomGenerator rng(seed);

    for (int test = 0; test < num_tests; ++test) {
        const int factor = rng.bounded(-limit, limit);
        const int limit_1 = rng.generateDouble() * factor;
        const int limit_2 = rng.generateDouble() * factor;

        const int bottom = std::min(limit_1, limit_2);
        const int top = std::max(limit_1, limit_2);

        const double number = rng.bounded(top - bottom) + bottom;

        QString str_number;
        str_number.setNum(number);

        const bool allow_empty = false;
        int pos = 0;

        StrictIntValidator validator(bottom, top, allow_empty, nullptr);

        for (int c = 1; c <= str_number.length(); ++c) {
            QString typed = str_number.first(c);

            auto state = validator.validate(typed, pos);

            if (state == QValidator::Invalid) {
                qDebug() << "Validation failed for" << typed << "from"
                         << number << "range" << bottom << "to" << top;
                QVERIFY(false);
            }
        }

        QVERIFY(true);
    }
}
#endif

QTEST_MAIN(TestStrictIntValidator)

#include "teststrictintvalidator.moc"
