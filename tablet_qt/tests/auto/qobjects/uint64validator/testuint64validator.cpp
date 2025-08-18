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

#ifdef TESTUINT64_INCLUDE_RANDOM

private:
    void validateRandomNumbers(const quint64 lowest, const quint64 highest);
#endif

private slots:
    void testSetRangeSetsTopAndBottom();
    void testSetRangeSignalsWhenTopChanges();
    void testSetRangeSignalsWhenBottomChanges();
    void testSetRangeSignalsWhenNothingChanges();
    void testSetBottomSetsBottom();
    void testSetTopSetsTop();
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
    void testRandomNumbersAndRangesLargeRange();
    void testRandomNumbersAndRangesSmallRange();
#endif
};

void TestUInt64Validator::testSetRangeSetsTopAndBottom()
{
    const quint64 bottom = 0;
    const quint64 top = 10;

    UInt64Validator* validator = new UInt64Validator();

    validator->setRange(bottom, top);

    QCOMPARE(validator->top(), top);
    QCOMPARE(validator->bottom(), bottom);
}

void TestUInt64Validator::testSetRangeSignalsWhenTopChanges()
{
    const quint64 bottom = 0;
    const quint64 old_top = 10;

    UInt64Validator* validator = new UInt64Validator(bottom, old_top);

    QSignalSpy changed_spy(validator, SIGNAL(changed()));
    QVERIFY(changed_spy.isValid());

    QSignalSpy top_spy(validator, SIGNAL(topChanged(quint64)));
    QVERIFY(top_spy.isValid());

    QSignalSpy bottom_spy(validator, SIGNAL(bottomChanged(quint64)));
    QVERIFY(bottom_spy.isValid());

    const quint64 new_top = 20;
    validator->setRange(bottom, new_top);

    QCOMPARE(changed_spy.count(), 1);
    QCOMPARE(top_spy.count(), 1);
    QList<QVariant> arguments = top_spy.takeFirst();
    QVERIFY(arguments.at(0).toInt() == new_top);

    QCOMPARE(bottom_spy.count(), 0);
}

void TestUInt64Validator::testSetRangeSignalsWhenBottomChanges()
{
    const quint64 old_bottom = 0;
    const quint64 top = 10;

    UInt64Validator* validator = new UInt64Validator(old_bottom, top);

    QSignalSpy changed_spy(validator, SIGNAL(changed()));
    QVERIFY(changed_spy.isValid());

    QSignalSpy top_spy(validator, SIGNAL(topChanged(quint64)));
    QVERIFY(top_spy.isValid());

    QSignalSpy bottom_spy(validator, SIGNAL(bottomChanged(quint64)));
    QVERIFY(bottom_spy.isValid());

    const quint64 new_bottom = 5;
    validator->setRange(new_bottom, top);

    QCOMPARE(changed_spy.count(), 1);
    QCOMPARE(top_spy.count(), 0);

    QCOMPARE(bottom_spy.count(), 1);
    QList<QVariant> arguments = bottom_spy.takeFirst();
    QVERIFY(arguments.at(0).toInt() == new_bottom);
}

void TestUInt64Validator::testSetRangeSignalsWhenNothingChanges()
{
    const quint64 bottom = 0;
    const quint64 top = 10;

    UInt64Validator* validator = new UInt64Validator(bottom, top);

    QSignalSpy changed_spy(validator, SIGNAL(changed()));
    QVERIFY(changed_spy.isValid());

    QSignalSpy top_spy(validator, SIGNAL(topChanged(quint64)));
    QVERIFY(top_spy.isValid());

    QSignalSpy bottom_spy(validator, SIGNAL(bottomChanged(quint64)));
    QVERIFY(bottom_spy.isValid());

    validator->setRange(bottom, top);

    QCOMPARE(changed_spy.count(), 0);
    QCOMPARE(top_spy.count(), 0);
    QCOMPARE(bottom_spy.count(), 0);
}

void TestUInt64Validator::testSetBottomSetsBottom()
{
    const quint64 bottom = 10;

    UInt64Validator* validator = new UInt64Validator();
    validator->setBottom(bottom);

    QCOMPARE(validator->bottom(), bottom);
}

void TestUInt64Validator::testSetTopSetsTop()
{
    const quint64 top = 10;

    UInt64Validator* validator = new UInt64Validator();
    validator->setTop(top);

    QCOMPARE(validator->top(), top);
}

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
void TestUInt64Validator::testRandomNumbersAndRangesLargeRange()
{
    // QRandomGenerator does not work across the full range but this is
    // good enough for our purposes
    validateRandomNumbers(0, 1e10);
}

void TestUInt64Validator::testRandomNumbersAndRangesSmallRange()
{
    validateRandomNumbers(0, 1000);
}

void TestUInt64Validator::validateRandomNumbers(
    const quint64 lowest, const quint64 highest
)
{
    const int seed = 1234;
    const int num_tests = 1000;

    QRandomGenerator rng(seed);

    for (int test = 0; test < num_tests; ++test) {
        const quint64 limit_1 = rng.bounded(lowest, highest);
        const quint64 limit_2 = rng.bounded(lowest, highest);

        const quint64 bottom = std::min(limit_1, limit_2);
        const quint64 top = std::max(limit_1, limit_2);

        QString str_number;

        if (bottom == top) {
            str_number.setNum(bottom);
        } else {
            const quint64 number = rng.bounded(top - bottom) + bottom;
            str_number.setNum(number);
        }

        int pos = 0;

        UInt64Validator validator(bottom, top, nullptr);

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

QTEST_MAIN(TestUInt64Validator)

#include "testuint64validator.moc"
