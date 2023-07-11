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

#include "lib/convert.h"


class TestConvert: public QObject
{
    Q_OBJECT

private slots:
    void testToSqlLiteralNullReturnsNullString();
    void testToSqlLiteralIntReturnsIntString();
    void testToSqlLiteralLongLongReturnsLongLongString();
    void testToSqlLiteralUIntReturnsUIntString();
    void testToSqlLiteralULongLongReturnsULongLongString();
    void testToSqlLiteralBoolReturnsIntString();
    void testToSqlLiteralDoubleReturnsDoubleString();
    void testToSqlLiteralCharReturnsQuotedString();
    void testToSqlLiteralStringReturnsQuotedStringWithEscapedNewlines();
    void testToSqlLiteralStringListReturnsQuotedCommaSeparatedString();
};


using namespace convert;

void TestConvert::testToSqlLiteralNullReturnsNullString()
{
    QCOMPARE(toSqlLiteral(QVariant::fromValue(nullptr)), QStringLiteral("NULL"));
}

void TestConvert::testToSqlLiteralIntReturnsIntString()
{
    const int value = -123;
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("-123"));
}

void TestConvert::testToSqlLiteralLongLongReturnsLongLongString()
{
    const qlonglong value = Q_INT64_C(-9223372036854775807);
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("-9223372036854775807"));
}

void TestConvert::testToSqlLiteralUIntReturnsUIntString()
{
    const uint value = 123;
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("123"));
}

void TestConvert::testToSqlLiteralULongLongReturnsULongLongString()
{
    const qulonglong value = Q_UINT64_C(18446744073709551615);
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("18446744073709551615"));
}

void TestConvert::testToSqlLiteralBoolReturnsIntString()
{
    const bool value = true;
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("1"));
}

void TestConvert::testToSqlLiteralDoubleReturnsDoubleString()
{
    const double value = 3.14159265358979323846;
    // https://doc.qt.io/qt-6/qstring.html#setNum-9
    // Will default to format 'g', precision = 6
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("3.14159"));
}

void TestConvert::testToSqlLiteralCharReturnsQuotedString()
{
    const QChar value = 'A';
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("'A'"));
}

void TestConvert::testToSqlLiteralStringReturnsQuotedStringWithEscapedNewlines()
{
    const QString value = "Two's complement.\nThree's a crowd.\n\rBackslash:\\";
    QCOMPARE(toSqlLiteral(QVariant(value)),
             QString("'Two''s complement.\\nThree''s a crowd.\\n\\rBackslash:\\\\'"));
}

void TestConvert::testToSqlLiteralStringListReturnsQuotedCommaSeparatedString()
{
    const QStringList value = {"one", "two", "three"};
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("'\"one\",\"two\",\"three\"'"));
}

QTEST_MAIN(TestConvert)

#include "testconvert.moc"
