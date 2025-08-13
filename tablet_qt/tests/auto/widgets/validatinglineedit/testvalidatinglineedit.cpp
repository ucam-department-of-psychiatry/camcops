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

#include <QHBoxLayout>
#include <QtTest/QtTest>
#include <QVBoxLayout>

#include "widgets/validatinglineedit.h"

class TestValidator : public QValidator
{
    Q_OBJECT

public:
    TestValidator(QObject* parent = nullptr);
    virtual QValidator::State
        validate(QString& input, int& pos) const override;
};

TestValidator::TestValidator(QObject* parent) :
    QValidator(parent)
{
}

QValidator::State TestValidator::validate(QString& input, int&) const
{
    qDebug() << Q_FUNC_INFO << input;

    if (input == "valid") {
        return Acceptable;
    }

    return Intermediate;
}

class TestValidatingLineEdit : public QObject
{
    Q_OBJECT

private slots:
    void testHasHorizontalLayout();
    void testHasVerticalLayout();
    void testSignalsForValidInput();
    void testSignalsForIntermediateInput();
};

void TestValidatingLineEdit::testHasVerticalLayout()
{
    QValidator* validator = nullptr;
    const bool allow_empty = false;
    const bool read_only = false;
    const bool delayed = false;
    const bool vertical = true;

    auto vle = new ValidatingLineEdit(
        validator, allow_empty, read_only, delayed, vertical
    );

    QVERIFY(qobject_cast<QVBoxLayout*>(vle->layout()) != nullptr);
}

void TestValidatingLineEdit::testHasHorizontalLayout()
{
    QValidator* validator = nullptr;
    const bool allow_empty = false;
    const bool read_only = false;
    const bool delayed = false;
    const bool vertical = false;

    auto vle = new ValidatingLineEdit(
        validator, allow_empty, read_only, delayed, vertical
    );

    QVERIFY(qobject_cast<QHBoxLayout*>(vle->layout()) != nullptr);
}

void::TestValidatingLineEdit::testSignalsForValidInput()
{
    auto vle = new ValidatingLineEdit(new TestValidator());
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    QSignalSpy valid_spy(vle, SIGNAL(valid()));
    QVERIFY(valid_spy.isValid());

    QSignalSpy invalid_spy(vle, SIGNAL(invalid()));
    QVERIFY(invalid_spy.isValid());

    QSignalSpy validated_spy(vle, SIGNAL(validated()));
    QVERIFY(validated_spy.isValid());

    QString input("valid");
    QTest::keyClicks(line_edit, input);

    QCOMPARE(valid_spy.count(), 1);
    QCOMPARE(invalid_spy.count(), input.length()-1);
    QCOMPARE(validated_spy.count(), input.length());
}

void::TestValidatingLineEdit::testSignalsForIntermediateInput()
{
    auto vle = new ValidatingLineEdit(new TestValidator());
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    QSignalSpy valid_spy(vle, SIGNAL(valid()));
    QVERIFY(valid_spy.isValid());

    QSignalSpy invalid_spy(vle, SIGNAL(invalid()));
    QVERIFY(invalid_spy.isValid());

    QSignalSpy validated_spy(vle, SIGNAL(validated()));
    QVERIFY(validated_spy.isValid());

    QString input("intermediate");
    QTest::keyClicks(line_edit, input);

    QCOMPARE(valid_spy.count(), 0);
    QCOMPARE(invalid_spy.count(), input.length());
    QCOMPARE(validated_spy.count(), input.length());
}

QTEST_MAIN(TestValidatingLineEdit)

#include "testvalidatinglineedit.moc"
