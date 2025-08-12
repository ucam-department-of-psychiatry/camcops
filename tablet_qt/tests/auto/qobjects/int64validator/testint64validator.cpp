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

#include "qobjects/int64validator.h"

#define TESTINT64_INCLUDE_RANDOM  // should generally be defined

class TestInt64Validator : public QObject
{
    Q_OBJECT

#ifdef TESTINT64_INCLUDE_RANDOM

private:
    void validateRandomNumbers(const qint64 lowest, const qint64 highest);
#endif

private slots:
    void testValidateReturnsIntermediateIfEmpty();
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
    void testValidateReturnsIntermediateIfHasInvalidStart();
    void testValidateReturnsIntermediateIfZeroAndRangeGreaterThanZero();
#ifdef TESTINT64_INCLUDE_RANDOM
    void testRandomNumbersAndRangesLargeRange();
    void testRandomNumbersAndRangesSmallRange();
#endif
};

void TestInt64Validator::testValidateReturnsIntermediateIfEmpty()
{
    const qint64 bottom = 0;
    const qint64 top = 10;
    QString text("");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestInt64Validator::testValidateReturnsInvalidIfDecimalPoint()
{
    const qint64 bottom = 0;
    const qint64 top = 10;
    QString text("3.1416");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestInt64Validator::
    testValidateReturnsIntermediateIfMinusAndNegativeAllowed()
{
    const qint64 bottom = -1;
    const qint64 top = 10;
    QString text("-");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestInt64Validator::
    testValidateReturnsInvalidIfMinusAndNegativeNotAllowed()
{
    const qint64 bottom = 0;
    const qint64 top = 10;
    QString text("-");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestInt64Validator::
    testValidateReturnsIntermediateIfPlusAndPositiveAllowed()
{
    const qint64 bottom = 0;
    const qint64 top = 10;
    QString text("+");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestInt64Validator::testValidateReturnsInvalidIfPlusAndPositiveNotAllowed(
)
{
    const qint64 bottom = -100;
    const qint64 top = -1;
    QString text("+");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestInt64Validator::testValidateReturnsInvalidIfNotAnInt()
{
    const qint64 bottom = 0;
    const qint64 top = 10;
    QString text("not an int");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestInt64Validator::testValidateReturnsAcceptableIfAnIntWithinRange()
{
    const qint64 bottom = 0;
    const qint64 top = 10;
    QString text("3");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Acceptable);
}

void TestInt64Validator::testValidateReturnsIntermediateIfNegativeZero()
{
    const qint64 bottom = -2;
    const qint64 top = -1;
    QString text("-0");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestInt64Validator::testValidateReturnsInvalidIfTopNegativeAndNoMinus()
{
    const qint64 bottom = -10;
    const qint64 top = -1;
    QString text("1");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestInt64Validator::testValidateReturnsIntermediateIfHasValidStart()
{
    const qint64 bottom = 10;
    const qint64 top = 20;
    QString text("1");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestInt64Validator::testValidateReturnsIntermediateIfHasInvalidStart()
{
    const qint64 bottom = 10;
    const qint64 top = 19;
    QString text("2");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestInt64Validator::
    testValidateReturnsIntermediateIfZeroAndRangeGreaterThanZero()
{
    const qint64 bottom = 1;
    const qint64 top = 5;
    QString text("0");
    int pos = 0;

    Int64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

#ifdef TESTINT64_INCLUDE_RANDOM
void TestInt64Validator::testRandomNumbersAndRangesLargeRange()
{
    // QRandomGenerator does not work across the full range but this is
    // good enough for our purposes
    validateRandomNumbers(-1e10, 1e10);
}

void TestInt64Validator::testRandomNumbersAndRangesSmallRange()
{
    validateRandomNumbers(-1000, 1000);
}

void TestInt64Validator::validateRandomNumbers(
    const qint64 lowest, const qint64 highest
)
{
    const int seed = 1234;
    const int num_tests = 1000;

    QRandomGenerator rng(seed);

    for (int test = 0; test < num_tests; ++test) {
        const qint64 limit_1 = rng.bounded(lowest, highest);
        const qint64 limit_2 = rng.bounded(lowest, highest);

        const qint64 bottom = std::min(limit_1, limit_2);
        const qint64 top = std::max(limit_1, limit_2);

        QString str_number;

        if (bottom == top) {
            str_number.setNum(bottom);
        } else {
            const qint64 number = rng.bounded(top - bottom) + bottom;
            str_number.setNum(number);
        }

        int pos = 0;

        Int64Validator validator(bottom, top, nullptr);

        for (int c = 1; c <= str_number.length(); ++c) {
            QString typed = str_number.first(c);

            auto state = validator.validate(typed, pos);

            if (state == QValidator::Invalid) {
                qDebug() << "Validation failed for" << typed << "from"
                         << str_number << "range" << bottom << "to" << top;
                QVERIFY(false);
            }
        }

        QVERIFY(true);
    }
}
#endif

QTEST_MAIN(TestInt64Validator)

#include "testint64validator.moc"
