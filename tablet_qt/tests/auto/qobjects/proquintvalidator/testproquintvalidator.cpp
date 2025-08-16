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

#include "qobjects/proquintvalidator.h"

class TestProquintValidator : public QObject
{
    Q_OBJECT

private slots:
    void testTooLongReturnsIntermediate();
    void testNoMatchReturnsIntermediate();
    void testInvalidReturnsIntermediate();
    void testValidReturnsAcceptable();
};

void TestProquintValidator::testTooLongReturnsIntermediate()
{
    auto validator = new ProquintValidator();

    QString input(50, 'a');
    int pos = 0;
    QCOMPARE(validator->validate(input, pos), QValidator::Intermediate);
}

void TestProquintValidator::testNoMatchReturnsIntermediate()
{
    auto validator = new ProquintValidator();

    QString input("aaaaa");
    int pos = 0;
    QCOMPARE(validator->validate(input, pos), QValidator::Intermediate);
}

void TestProquintValidator::testInvalidReturnsIntermediate()
{
    auto validator = new ProquintValidator();

    QString input("kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov-k");
    int pos = 0;
    QCOMPARE(validator->validate(input, pos), QValidator::Intermediate);
}

void TestProquintValidator::testValidReturnsAcceptable()
{
    auto validator = new ProquintValidator();

    QString input("kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov-t");
    int pos = 0;
    QCOMPARE(validator->validate(input, pos), QValidator::Acceptable);
}
QTEST_MAIN(TestProquintValidator)

#include "testproquintvalidator.moc"
