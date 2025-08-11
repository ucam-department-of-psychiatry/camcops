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

#include "qobjects/uint64validator.h"

#define TESTUINT64_INCLUDE_RANDOM  // should generally be defined

class TestUInt64Validator : public QObject
{
    Q_OBJECT

private slots:
    void testValidateReturnsIntermediateIfEmpty();
    void testValidateReturnsInvalidIfDecimalPoint();
    void testValidateReturnsInvalidIfMinus();
    void testValidateReturnsIntermediateIfPlusAndPositiveAllowed();
    void testValidateReturnsInvalidIfNotAnInt();
    void testValidateReturnsAcceptableIfAnIntWithinRange();
    void testValidateReturnsInvalidIfMinusZero();
    void testValidateReturnsIntermediateIfHasValidStart();
    void testValidateReturnsIntermediateIfHasInvalidStart();
    void testValidateReturnsIntermediateIfZeroAndRangeGreaterThanZero();
#ifdef TESTUINT64_INCLUDE_RANDOM
    void testRandomNumbersAndRanges();
#endif
};

void TestUInt64Validator::testValidateReturnsIntermediateIfEmpty()
{
    const quint64 bottom = 0;
    const quint64 top = 10;
    QString text("");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestUInt64Validator::testValidateReturnsInvalidIfDecimalPoint()
{
    const quint64 bottom = 0;
    const quint64 top = 10;
    QString text("3.1416");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestUInt64Validator::testValidateReturnsInvalidIfMinus()
{
    const quint64 bottom = 0;
    const quint64 top = 10;
    QString text("-");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestUInt64Validator::
    testValidateReturnsIntermediateIfPlusAndPositiveAllowed()
{
    const quint64 bottom = 0;
    const quint64 top = 10;
    QString text("+");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestUInt64Validator::testValidateReturnsInvalidIfNotAnInt()
{
    const quint64 bottom = 0;
    const quint64 top = 10;
    QString text("not an int");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestUInt64Validator::testValidateReturnsAcceptableIfAnIntWithinRange()
{
    const quint64 bottom = 0;
    const quint64 top = 10;
    QString text("3");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Acceptable);
}

void TestUInt64Validator::testValidateReturnsInvalidIfMinusZero()
{
    const quint64 bottom = -2;
    const quint64 top = -1;
    QString text("-0");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Invalid);
}

void TestUInt64Validator::testValidateReturnsIntermediateIfHasValidStart()
{
    const quint64 bottom = 10;
    const quint64 top = 20;
    QString text("1");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestUInt64Validator::testValidateReturnsIntermediateIfHasInvalidStart()
{
    const quint64 bottom = 10;
    const quint64 top = 19;
    QString text("2");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

void TestUInt64Validator::
    testValidateReturnsIntermediateIfZeroAndRangeGreaterThanZero()
{
    const quint64 bottom = 1;
    const quint64 top = 5;
    QString text("0");
    int pos = 0;

    UInt64Validator validator(bottom, top, nullptr);

    QCOMPARE(validator.validate(text, pos), QValidator::Intermediate);
}

#ifdef TESTUINT64_INCLUDE_RANDOM
void TestUInt64Validator::testRandomNumbersAndRanges()
{
    const int seed = 1234;
    const int num_tests = 1000;

    QRandomGenerator rng(seed);

    for (int test = 0; test < num_tests; ++test) {
        const int limit_1 = rng.generate64();
        const int limit_2 = rng.generate64();

        const quint64 bottom = std::min(limit_1, limit_2);
        const quint64 top = std::max(limit_1, limit_2);

        const quint64 number = rng.bounded(top - bottom) + bottom;

        QString str_number;
        str_number.setNum(number);

        int pos = 0;

        UInt64Validator validator(bottom, top, nullptr);

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

QTEST_MAIN(TestUInt64Validator)

#include "testuint64validator.moc"
