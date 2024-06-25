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

#include "db/field.h"
#include "lib/customtypes.h"
#include "lib/version.h"

class TestField : public QObject
{
    Q_OBJECT

private slots:
    void testDatabaseValueQCharReturnsString();
    void testDatabaseValueQDateReturnsString();
    void testDatabaseValueQDateTimeReturnsString();
    void testDatabaseValueQStringListReturnsString();
    void testDatabaseValueQUuidReturnsString();
    void testDatabaseValueQVectorIntReturnsString();
    void testDatabaseValueVersionReturnsString();

    void testSetFromDatabaseValueQCharFromText();
    void testSetFromDatabaseValueQDateFromText();
    void testSetFromDatabaseValueQDateTimeFromText();
    void testSetFromDatabaseValueQStringListFromText();
    void testSetFromDatabaseValueQVectorIntFromText();
    void testSetFromDatabaseValueVersionFromText();
    void testSetFromDatabaseValueIntFromInt();

    void testSetValueStringTypeQCharConverted();

    void testSqlColumnTypeBoolIsInteger();
    void testSqlColumnTypeIntIsInteger();
    void testSqlColumnTypeLongLongIsInteger();
    void testSqlColumnTypeUIntIsInteger();
    void testSqlColumnTypeULongLongIsInteger();
    void testSqlColumnTypeDoubleIsReal();
    void testSqlColumnTypeQCharIsText();
    void testSqlColumnTypeQDateIsText();
    void testSqlColumnTypeQDateTimeIsText();
    void testSqlColumnTypeQStringIsText();
    void testSqlColumnTypeQStringListIsText();
    void testSqlColumnTypeQTimeIsText();
    void testSqlColumnTypeQUuidIsText();
    void testSqlColumnTypeQByteArrayIsBlob();
    void testSqlColumnTypeQVectorIntIsText();
    void testSqlColumnTypeVersionIsText();
};

void TestField::testDatabaseValueQCharReturnsString()
{
    auto field = Field("test", QMetaType::fromType<QChar>());
    const QVariant value_in = QChar('R');
    field.setValue(value_in);
    QCOMPARE(field.databaseValue(), QVariant("R"));
}

void TestField::testDatabaseValueQDateReturnsString()
{
    auto field = Field("test", QMetaType::fromType<QDate>());
    const QVariant value_in = QDate(2023, 7, 28);
    field.setValue(value_in);
    QCOMPARE(field.databaseValue(), QVariant("2023-07-28"));
}

void TestField::testDatabaseValueQDateTimeReturnsString()
{
    auto field = Field("test", QMetaType::fromType<QDateTime>());
    const QDate date = QDate(2023, 7, 13);
    const QTime time = QTime(16, 8, 49, 512);
    const QDateTime datetime = QDateTime(date, time, QTimeZone::utc());
    const QVariant value_in = QVariant(datetime);
    field.setValue(value_in);
    QCOMPARE(field.databaseValue(), QVariant("2023-07-13T16:08:49.512+00:00"));
}

void TestField::testDatabaseValueQStringListReturnsString()
{
    auto field = Field("test", QMetaType::fromType<QStringList>());
    const QStringList list = {"one", "two", "three"};
    QVariant value_in;
    value_in.setValue(list);
    field.setValue(value_in);
    QCOMPARE(field.databaseValue(), QVariant("\"one\",\"two\",\"three\""));
}

void TestField::testDatabaseValueQUuidReturnsString()
{
    auto field = Field("test", QMetaType::fromType<QUuid>());
    auto uuid = QUuid();
    const QVariant value_in = uuid;
    field.setValue(value_in);
    QCOMPARE(field.databaseValue(), QVariant(uuid.toString()));
}

void TestField::testDatabaseValueQVectorIntReturnsString()
{
    customtypes::registerTypesForQVariant();
    auto field = Field("test", QMetaType::fromType<QVector<int>>());
    const QVector<int> vector_int = {1, 2, 3};
    QVariant value_in;
    value_in.setValue(vector_int);
    field.setValue(value_in);
    QCOMPARE(field.databaseValue(), QVariant("1,2,3"));
}

void TestField::testDatabaseValueVersionReturnsString()
{
    customtypes::registerTypesForQVariant();
    auto field = Field("test", QMetaType::fromType<Version>());
    const Version version = Version(1, 2, 3);
    QVariant value_in;
    value_in.setValue(version);
    field.setValue(value_in);
    QCOMPARE(field.databaseValue(), QVariant("1.2.3"));
}

void TestField::testSetFromDatabaseValueQCharFromText()
{
    auto field = Field("test", QMetaType::fromType<QChar>());
    const QVariant value_in = "A";
    field.setFromDatabaseValue(value_in);

    QVariant value_out = field.value();
    QCOMPARE(value_out, QVariant(QChar('A')));
}

void TestField::testSetFromDatabaseValueQDateFromText()
{
    auto field = Field("test", QMetaType::fromType<QDate>());
    const QVariant value_in = "2023-07-18";
    field.setFromDatabaseValue(value_in);

    QVariant value_out = field.value();
    QCOMPARE(value_out, QVariant(QDate(2023, 07, 18)));
}

void TestField::testSetFromDatabaseValueQDateTimeFromText()
{
    auto field = Field("test", QMetaType::fromType<QDateTime>());
    const QVariant value_in = "2023-07-13T16:08:49.512+00:00";
    field.setFromDatabaseValue(value_in);

    QVariant value_out = field.value();
    const QDate date = QDate(2023, 7, 13);
    const QTime time = QTime(16, 8, 49, 512);
    const QDateTime datetime = QDateTime(date, time, QTimeZone::utc());
    QCOMPARE(value_out, QVariant(datetime));
}

void TestField::testSetFromDatabaseValueQStringListFromText()
{
    auto field = Field("test", QMetaType::fromType<QStringList>());
    const QVariant value_in = "one,two,three";
    field.setFromDatabaseValue(value_in);

    QVariant value_out = field.value();
    const QStringList expected = {"one", "two", "three"};
    QVariant variant;
    variant.setValue(expected);
    QCOMPARE(value_out, variant);
}

void TestField::testSetFromDatabaseValueQVectorIntFromText()
{
    customtypes::registerTypesForQVariant();
    auto field = Field("test", QMetaType::fromType<QVector<int>>());
    const QVariant value_in = "1,2,3";
    field.setFromDatabaseValue(value_in);

    QVariant value_out = field.value();
    const QVector<int> expected = {1, 2, 3};
    QVariant variant;
    variant.setValue(expected);
    QCOMPARE(value_out, variant);
}

void TestField::testSetFromDatabaseValueVersionFromText()
{
    customtypes::registerTypesForQVariant();
    auto field = Field("test", QMetaType::fromType<Version>());
    const QVariant value_in = "1.2.3";
    field.setFromDatabaseValue(value_in);

    QVariant value_out = field.value();
    const Version expected = Version(1, 2, 3);
    QVariant variant;
    variant.setValue(expected);
    QCOMPARE(value_out, variant);
}

void TestField::testSetFromDatabaseValueIntFromInt()
{
    auto field = Field("test", QMetaType::fromType<int>());
    const QVariant value_in = 123;
    field.setFromDatabaseValue(value_in);

    QVariant value_out = field.value();
    QCOMPARE(value_out, QVariant(123));
}

void TestField::testSetValueStringTypeQCharConverted()
{
    auto field = Field("test", QMetaType::fromType<QChar>());
    const QVariant value_in = QChar('R');
    field.setValue(value_in);
    const QVariant value_out = field.value();
    QCOMPARE(value_out.typeId(), QMetaType::QChar);
    QCOMPARE(value_in, value_out);
}

void TestField::testSqlColumnTypeBoolIsInteger()
{
    auto field = Field("test", QMetaType::fromType<bool>());
    QCOMPARE(field.sqlColumnType(), "INTEGER");
}

void TestField::testSqlColumnTypeIntIsInteger()
{
    auto field = Field("test", QMetaType::fromType<int>());
    QCOMPARE(field.sqlColumnType(), "INTEGER");
}

void TestField::testSqlColumnTypeLongLongIsInteger()
{
    auto field = Field("test", QMetaType::fromType<qlonglong>());
    QCOMPARE(field.sqlColumnType(), "INTEGER");
}

void TestField::testSqlColumnTypeUIntIsInteger()
{
    auto field = Field("test", QMetaType::fromType<uint>());
    QCOMPARE(field.sqlColumnType(), "INTEGER");
}

void TestField::testSqlColumnTypeULongLongIsInteger()
{
    auto field = Field("test", QMetaType::fromType<qulonglong>());
    QCOMPARE(field.sqlColumnType(), "INTEGER");
}

void TestField::testSqlColumnTypeDoubleIsReal()
{
    auto field = Field("test", QMetaType::fromType<double>());
    QCOMPARE(field.sqlColumnType(), "REAL");
}

void TestField::testSqlColumnTypeQCharIsText()
{
    auto field = Field("test", QMetaType::fromType<QChar>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}

void TestField::testSqlColumnTypeQDateIsText()
{
    auto field = Field("test", QMetaType::fromType<QDate>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}

void TestField::testSqlColumnTypeQDateTimeIsText()
{
    auto field = Field("test", QMetaType::fromType<QDateTime>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}

void TestField::testSqlColumnTypeQStringIsText()
{
    auto field = Field("test", QMetaType::fromType<QString>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}

void TestField::testSqlColumnTypeQStringListIsText()
{
    auto field = Field("test", QMetaType::fromType<QStringList>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}

void TestField::testSqlColumnTypeQTimeIsText()
{
    auto field = Field("test", QMetaType::fromType<QTime>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}

void TestField::testSqlColumnTypeQUuidIsText()
{
    auto field = Field("test", QMetaType::fromType<QUuid>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}

void TestField::testSqlColumnTypeQByteArrayIsBlob()
{
    auto field = Field("test", QMetaType::fromType<QByteArray>());
    QCOMPARE(field.sqlColumnType(), "BLOB");
}

void TestField::testSqlColumnTypeQVectorIntIsText()
{
    customtypes::registerTypesForQVariant();
    auto field = Field("test", QMetaType::fromType<QVector<int>>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}

void TestField::testSqlColumnTypeVersionIsText()
{
    customtypes::registerTypesForQVariant();
    auto field = Field("test", QMetaType::fromType<Version>());
    QCOMPARE(field.sqlColumnType(), "TEXT");
}


QTEST_MAIN(TestField)

#include "testfield.moc"
