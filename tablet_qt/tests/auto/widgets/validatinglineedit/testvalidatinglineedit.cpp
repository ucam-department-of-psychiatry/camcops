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
    void testSignalsForDelayedValidInputFastTyping();
    void testSignalsForDelayedValidInputSlowTyping();
    void testSignalsForReadOnly();
    void testAddInputMethodHintsUpdatesExisting();
    void testSetText();
    void testText();
    void testSetTextBlockingSignals();
    void testSetPlaceholderText();
    void testSetEchoMode();
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

void TestValidatingLineEdit::testSignalsForValidInput()
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

    // Input is only valid once the whole string has been
    // typed in.
    QCOMPARE(valid_spy.count(), 1);
    QCOMPARE(invalid_spy.count(), input.length() - 1);
    QCOMPARE(validated_spy.count(), input.length());
}

void TestValidatingLineEdit::testSignalsForIntermediateInput()
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

    // Input is never valid because it never equals the string "valid".
    QCOMPARE(valid_spy.count(), 0);
    QCOMPARE(invalid_spy.count(), input.length());
    QCOMPARE(validated_spy.count(), input.length());
}

void TestValidatingLineEdit::testSignalsForDelayedValidInputFastTyping()
{
    const bool allow_empty = false;
    const bool read_only = false;
    const bool delayed = true;

    auto vle = new ValidatingLineEdit(
        new TestValidator(), allow_empty, read_only, delayed
    );
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    QSignalSpy valid_spy(vle, SIGNAL(valid()));
    QVERIFY(valid_spy.isValid());

    QSignalSpy invalid_spy(vle, SIGNAL(invalid()));
    QVERIFY(invalid_spy.isValid());

    QSignalSpy validated_spy(vle, SIGNAL(validated()));
    QVERIFY(validated_spy.isValid());

    QString input("valid");
    QTest::keyClicks(line_edit, input);

    // With delayed validation there is a 400ms delay between the text being
    // entered and our validation being run. Each simulated keypress will
    // restart the timer. This test assumes that the pretend typing will
    // complete within that time. So we should expect the signals to be
    // broadcast once.
    validated_spy.wait(1000);

    QCOMPARE(validated_spy.count(), 1);
    QCOMPARE(valid_spy.count(), 1);

    // Never invalid because the whole string is validated once and never the
    // intermediate parts.
    QCOMPARE(invalid_spy.count(), 0);
}

void TestValidatingLineEdit::testSignalsForDelayedValidInputSlowTyping()
{
    const bool allow_empty = false;
    const bool read_only = false;
    const bool delayed = true;

    auto vle = new ValidatingLineEdit(
        new TestValidator(), allow_empty, read_only, delayed
    );
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    QSignalSpy valid_spy(vle, SIGNAL(valid()));
    QVERIFY(valid_spy.isValid());

    QSignalSpy invalid_spy(vle, SIGNAL(invalid()));
    QVERIFY(invalid_spy.isValid());

    QSignalSpy validated_spy(vle, SIGNAL(validated()));
    QVERIFY(validated_spy.isValid());

    QString input("valid");
    QTest::keyClicks(line_edit, input, Qt::NoModifier, 500);

    // The simulated typist types slower than the validation timeout
    // so we should expect signals for every character.
    for (int i = 0; i < input.length(); ++i) {
        validated_spy.wait(1000);
    }

    QCOMPARE(validated_spy.count(), input.length());
    QCOMPARE(valid_spy.count(), 1);
    QCOMPARE(invalid_spy.count(), input.length() - 1);
}

void TestValidatingLineEdit::testSignalsForReadOnly()
{
    const bool allow_empty = false;
    const bool read_only = true;

    auto vle
        = new ValidatingLineEdit(new TestValidator(), allow_empty, read_only);
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    QSignalSpy valid_spy(vle, SIGNAL(valid()));
    QVERIFY(valid_spy.isValid());

    QSignalSpy invalid_spy(vle, SIGNAL(invalid()));
    QVERIFY(invalid_spy.isValid());

    QSignalSpy validated_spy(vle, SIGNAL(validated()));
    QVERIFY(validated_spy.isValid());

    QString input("valid");
    QTest::keyClicks(line_edit, input);

    // Nothing should happen
    QCOMPARE(validated_spy.count(), 0);
    QCOMPARE(valid_spy.count(), 0);
    QCOMPARE(invalid_spy.count(), 0);
}

void TestValidatingLineEdit::testAddInputMethodHintsUpdatesExisting()
{
    auto vle = new ValidatingLineEdit();
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    vle->addInputMethodHints(Qt::ImhPreferNumbers);
    vle->addInputMethodHints(Qt::ImhSensitiveData);

    QCOMPARE(
        line_edit->inputMethodHints(),
        Qt::ImhPreferNumbers | Qt::ImhSensitiveData
    );
}

void TestValidatingLineEdit::testSetText()
{
    auto vle = new ValidatingLineEdit();
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    vle->setText("Test");

    QCOMPARE(line_edit->text(), "Test");
}

void TestValidatingLineEdit::testText()
{
    auto vle = new ValidatingLineEdit();
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    QString input("Test");
    QTest::keyClicks(line_edit, input);

    QCOMPARE(line_edit->text(), "Test");
}

void TestValidatingLineEdit::testSetTextBlockingSignals()
{
    auto vle = new ValidatingLineEdit();
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    QSignalSpy valid_spy(vle, SIGNAL(valid()));
    QVERIFY(valid_spy.isValid());

    QSignalSpy invalid_spy(vle, SIGNAL(invalid()));
    QVERIFY(invalid_spy.isValid());

    QSignalSpy validated_spy(vle, SIGNAL(validated()));
    QVERIFY(validated_spy.isValid());

    vle->setTextBlockingSignals("Test");

    // None of our callbacks should be called
    QCOMPARE(validated_spy.count(), 0);
    QCOMPARE(valid_spy.count(), 0);
    QCOMPARE(invalid_spy.count(), 0);

    // But the text should be set
    QCOMPARE(line_edit->text(), "Test");
}

void TestValidatingLineEdit::testSetPlaceholderText()
{
    auto vle = new ValidatingLineEdit();
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    vle->setPlaceholderText("Test");

    QCOMPARE(line_edit->placeholderText(), "Test");
}

void TestValidatingLineEdit::testSetEchoMode()
{
    auto vle = new ValidatingLineEdit();
    QLineEdit* line_edit = vle->findChild<QLineEdit*>();

    vle->setEchoMode(QLineEdit::Password);

    QCOMPARE(line_edit->echoMode(), QLineEdit::Password);
}

QTEST_MAIN(TestValidatingLineEdit)

#include "testvalidatinglineedit.moc"
