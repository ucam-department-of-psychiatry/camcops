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

#include <QValidator>
#include <QtTest/QtTest>

#include "qobjects/strictdoublevalidator.h"

class TestStrictDoubleValidator: public QObject
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
};

void TestStrictDoubleValidator::testValidateReturnsAcceptableIfEmptyAndEmptyAllowed()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = true;
    QString text("");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Acceptable);
}


void TestStrictDoubleValidator::testValidateReturnsIntermediateIfEmptyAndEmptyNotAllowed()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Intermediate);
}


void TestStrictDoubleValidator::testValidateReturnsInvalidIfTooManyDecimalPlaces()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("3.1416");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::testValidateReturnsIntermediateIfMinusAndNegativeAllowed()
{
    const double bottom = -1.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("-");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::testValidateReturnsInvalidIfMinusAndNegativeNotAllowed()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("-");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::testValidateReturnsIntermediateIfPlusAndPositiveAllowed()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("+");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::testValidateReturnsInvalidIfPlusAndPositiveNotAllowed()
{
    const double bottom = -10.0;
    const double top = -1.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("+");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::testValidateReturnsInvalidIfNotADouble()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("not a double");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::testValidateReturnsAcceptableIfADoubleWithinRange()
{
    const double bottom = 0.0;
    const double top = 10.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("3.141");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Acceptable);
}

void TestStrictDoubleValidator::testValidateReturnsIntermediateIfNegativeZero()
{
    const double bottom = -0.2;
    const double top = -0.1;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("-0");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::testValidateReturnsInvalidIfTopNegativeAndNoMinus()
{
    const double bottom = -10;
    const double top = -1.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("1");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Invalid);
}

void TestStrictDoubleValidator::testValidateReturnsIntermediateIfHasValidStart()
{
    const double bottom = 10.0;
    const double top = 20.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("1");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Intermediate);
}

void TestStrictDoubleValidator::testValidateReturnsInvalidIfHasInvalidStart()
{
    const double bottom = 10.0;
    const double top = 19.0;
    const int decimals = 3;
    const bool allow_empty = false;
    QString text("2");
    int pos = 0;

    auto validator = new StrictDoubleValidator(bottom, top, decimals, allow_empty, nullptr);

    QCOMPARE(validator->validate(text, pos), QValidator::Invalid);
}

QTEST_MAIN(TestStrictDoubleValidator)

#include "teststrictdoublevalidator.moc"
