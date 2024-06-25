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
#include "lib/customtypes.h"

class TestConvert : public QObject
{
    Q_OBJECT

private slots:
    void testPrettyValueNullReturnsNullString();
    void testPrettyValueByteArrayReturnsBinary();
    void testPrettyValueQDateReturnsIsoDate();
    void testPrettyValueQDateTimeReturnsIsoDateTimeWithMs();
    void testPrettyValueDoubleWithNegativeDPReturnsNumberAsIs();
    void testPrettyValueDoubleWithDPReturnsFormattedNumber();
    void testPrettyValueQStringEscapesWithLineBreaks();
    void testPrettyValueQStringListEscapesCommaSeparatesWithLineBreaks();
    void testPrettyValueQVectorIntReturnsCommaSeparatedString();
    void testPrettyValueByDefaultReturnsString();

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
    void testToSqlLiteralQDateReturnsIsoFormattedString();
    void testToSqlLiteralQDateTimeReturnsIsoDateWithMs();
    void testToSqlLiteralQTimeReturnsQuotedHMSString();
    void testToSqlLiteralQByteArrayReturnsBase64EncodedBlob();
    void testToSqlLiteralQVectorIntReturnsQuotedCommaSeparatedString();
};

using namespace convert;

void TestConvert::testToSqlLiteralNullReturnsNullString()
{
    QCOMPARE(
        toSqlLiteral(QVariant::fromValue(nullptr)), QStringLiteral("NULL")
    );
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

void TestConvert::testToSqlLiteralStringReturnsQuotedStringWithEscapedNewlines(
)
{
    const QString value
        = "Two's complement.\nThree's a crowd.\n\rBackslash:\\";
    QCOMPARE(
        toSqlLiteral(QVariant(value)),
        QString("'Two''s complement.\\nThree''s a crowd.\\n\\rBackslash:\\\\'")
    );
}

void TestConvert::testToSqlLiteralStringListReturnsQuotedCommaSeparatedString()
{
    const QStringList value = {"one", "two", "three"};
    QCOMPARE(
        toSqlLiteral(QVariant(value)), QString("'\"one\",\"two\",\"three\"'")
    );
}

void TestConvert::testToSqlLiteralQDateReturnsIsoFormattedString()
{
    const QDate value = QDate(2023, 7, 13);
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("'2023-07-13'"));
}

void TestConvert::testToSqlLiteralQDateTimeReturnsIsoDateWithMs()
{
    const QDate date = QDate(2023, 7, 13);
    const QTime time = QTime(16, 8, 49, 512);
    const QDateTime value = QDateTime(date, time, QTimeZone::utc());
    QCOMPARE(
        toSqlLiteral(QVariant(value)),
        QString("'2023-07-13T16:08:49.512+00:00'")
    );
}

void TestConvert::testToSqlLiteralQTimeReturnsQuotedHMSString()
{
    const QTime value = QTime(16, 8, 49);
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("'16:08:49'"));
}

void TestConvert::testToSqlLiteralQByteArrayReturnsBase64EncodedBlob()
{
    // %PDF-1.7\r
    const QByteArray value
        = QByteArray("\x25\x50\x44\x46\x2d\x31\x2e\x37\x0d");
    QCOMPARE(toSqlLiteral(QVariant(value)), QString("64'JVBERi0xLjcN'"));
}

void TestConvert::testToSqlLiteralQVectorIntReturnsQuotedCommaSeparatedString()
{
    customtypes::registerTypesForQVariant();
    const QVector<int> value{1, 2, 3};

    QVariant variant;
    variant.setValue(value);
    QCOMPARE(toSqlLiteral(variant), QString("'1,2,3'"));
}

void TestConvert::testPrettyValueByteArrayReturnsBinary()
{
    // %PDF-1.7\r
    const QByteArray value
        = QByteArray("\x25\x50\x44\x46\x2d\x31\x2e\x37\x0d");
    QCOMPARE(prettyValue(QVariant(value)), QStringLiteral("<binary>"));
}

void TestConvert::testPrettyValueNullReturnsNullString()
{
    QCOMPARE(
        prettyValue(QVariant::fromValue(nullptr)), QStringLiteral("NULL")
    );
}

void TestConvert::testPrettyValueQDateReturnsIsoDate()
{
    const QDate value = QDate(2023, 7, 13);
    QCOMPARE(prettyValue(QVariant(value)), QString("2023-07-13"));
}

void TestConvert::testPrettyValueQDateTimeReturnsIsoDateTimeWithMs()
{
    const QDate date = QDate(2023, 7, 13);
    const QTime time = QTime(16, 8, 49, 512);
    const QDateTime value = QDateTime(date, time, QTimeZone::utc());
    QCOMPARE(
        prettyValue(QVariant(value)), QString("2023-07-13T16:08:49.512+00:00")
    );
}

void TestConvert::testPrettyValueDoubleWithNegativeDPReturnsNumberAsIs()
{
    // It seems that too many decimal places will get truncated here.
    // I can't find the limit documented for double variant.toString().
    // It may well be platform dependent. If the caller cares about decimal
    // places they will set the dp argument to something.
    const double value = 3.14159;
    QCOMPARE(prettyValue(QVariant(value)), QString("3.14159"));
}

void TestConvert::testPrettyValueDoubleWithDPReturnsFormattedNumber()
{
    const double value = 3.14159265358979323846;
    QCOMPARE(prettyValue(QVariant(value), 8), QString("3.14159265"));
}

void TestConvert::testPrettyValueQStringEscapesWithLineBreaks()
{
    const QString value = "one\ntwo & three";
    QCOMPARE(prettyValue(QVariant(value)), QString("one<br>two &amp; three"));
}

void TestConvert::
    testPrettyValueQStringListEscapesCommaSeparatesWithLineBreaks()
{
    const QStringList value = {"one", "two & three", "four\nfive"};
    QCOMPARE(
        prettyValue(QVariant(value)),
        QString("one,two &amp; three,four<br>five")
    );
}

void TestConvert::testPrettyValueQVectorIntReturnsCommaSeparatedString()
{
    customtypes::registerTypesForQVariant();
    const QVector<int> value{1, 2, 3};

    QVariant variant;
    variant.setValue(value);
    QCOMPARE(prettyValue(variant), QString("1,2,3"));
}

void TestConvert::testPrettyValueByDefaultReturnsString()
{
    const int value = 123;
    QCOMPARE(prettyValue(QVariant(value)), QString("123"));
}

QTEST_MAIN(TestConvert)

#include "testconvert.moc"
