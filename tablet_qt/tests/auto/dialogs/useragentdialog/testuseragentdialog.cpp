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

#include <QDialogButtonBox>
#include <QLineEdit>
#include <QPushButton>
#include <QString>
#include <QtTest/QtTest>

#include "dialogs/useragentdialog.h"
#include "qobjects/widgetpositioner.h"


class TestUserAgentDialog : public QObject
{
    Q_OBJECT

private slots:
    void testDisplaysCurrent();
    void testSavesNewValue();
    void testRestoresDefault();
};

void TestUserAgentDialog::testDisplaysCurrent()
{
    auto default_user_agent = QString("Mozilla/5.0 (Linux x86_64) CamCOPS/v2.4.22");
    auto current_user_agent = QString("Mozilla/5.0");

    auto dialog = new UserAgentDialog(default_user_agent, current_user_agent);

    QLineEdit *user_agent_edit = dialog->findChild<QLineEdit *>();
    QVERIFY(user_agent_edit);

    QCOMPARE(user_agent_edit->text(), current_user_agent);
}

void TestUserAgentDialog::testSavesNewValue()
{
    auto default_user_agent = QString("Mozilla/5.0 (Linux x86_64) CamCOPS/v2.4.22");
    auto current_user_agent = default_user_agent;

    auto dialog = new UserAgentDialog(default_user_agent, current_user_agent);

    QLineEdit *user_agent_edit = dialog->findChild<QLineEdit *>();
    QVERIFY(user_agent_edit);

    auto new_user_agent = QString("Mozilla/5.0");
    user_agent_edit->setText(new_user_agent);

    QCOMPARE(dialog->userAgent(), new_user_agent);
}

void TestUserAgentDialog::testRestoresDefault()
{
    auto default_user_agent = QString("Mozilla/5.0 (Linux x86_64) CamCOPS/v2.4.22");
    auto current_user_agent = QString("Mozilla/5.0");

    auto dialog = new UserAgentDialog(default_user_agent, current_user_agent);

    dialog->open();

    auto buttonbox = dialog->findChild<QDialogButtonBox *>();
    QPushButton* defaults_button = buttonbox->button(
        QDialogButtonBox::RestoreDefaults
    );

    QTest::mouseClick(defaults_button, Qt::LeftButton);

    dialog->accept();

    QCOMPARE(dialog->userAgent(), default_user_agent);
}

QTEST_MAIN(TestUserAgentDialog)

#include "testuseragentdialog.moc"
