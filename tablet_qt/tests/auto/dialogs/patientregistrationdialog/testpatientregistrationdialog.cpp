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
#include <QPushButton>
#include <QString>
#include <QtTest/QtTest>
#include <QUrl>

#include "dialogs/patientregistrationdialog.h"
#include "widgets/validatinglineedit.h"

class TestPatientRegistrationDialog : public QObject
{
    Q_OBJECT

private slots:
    void testPatientProquint();
    void testServerUrlAsString();
    void testServerUrl();
    void testPatientProquintTrimmed();
    void testServerUrlTrimmed();
    void testNoValdationFeedbackWhenFieldsAreEmpty();
    void testOKButtonDisabledWhenProquintInvalid();
    void testOKButtonDisabledWhenUrlInvalid();
    void testOKButtonEnabledWhenAllValid();
};

void TestPatientRegistrationDialog::testPatientProquint()
{
    QString current_proquint(
        "kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov-t"
    );
    auto dialog
        = new PatientRegistrationDialog(nullptr, QUrl(), current_proquint);

    QCOMPARE(dialog->patientProquint(), current_proquint);
}

void TestPatientRegistrationDialog::testServerUrlAsString()
{
    QString server_url("https://example.com/");
    auto dialog = new PatientRegistrationDialog(nullptr, QUrl(server_url), "");

    QCOMPARE(dialog->serverUrlAsString(), server_url);
}

void TestPatientRegistrationDialog::testServerUrl()
{

    QUrl server_url("https://example.com/");
    auto dialog = new PatientRegistrationDialog(nullptr, server_url);

    QCOMPARE(dialog->serverUrl(), server_url);
}

void TestPatientRegistrationDialog::testPatientProquintTrimmed()
{
    QString current_proquint(
        "    kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov-t    "
    );
    auto dialog
        = new PatientRegistrationDialog(nullptr, QUrl(), current_proquint);

    QCOMPARE(dialog->patientProquint(), current_proquint.trimmed());
}

void TestPatientRegistrationDialog::testServerUrlTrimmed()
{
    QString server_url("https://example.com/   ");
    auto dialog = new PatientRegistrationDialog(nullptr, QUrl(server_url), "");

    QCOMPARE(dialog->serverUrlAsString(), server_url.trimmed());
}

void TestPatientRegistrationDialog::testNoValdationFeedbackWhenFieldsAreEmpty()
{
    auto dialog = new PatientRegistrationDialog();

    auto vles = dialog->findChildren<ValidatingLineEdit*>();
    QCOMPARE(vles.size(), 2);

    for (auto& vle : vles) {
        auto label = vle->findChild<QLabel*>();
        QCOMPARE(label->text(), "");
    }
}

void TestPatientRegistrationDialog::testOKButtonDisabledWhenProquintInvalid()
{
    QUrl server_url("https://example.com/");
    auto dialog = new PatientRegistrationDialog(nullptr, server_url, "");

    auto buttonbox = dialog->findChild<QDialogButtonBox*>();
    QPushButton* ok_button = buttonbox->button(QDialogButtonBox::Ok);

    QVERIFY(!ok_button->isEnabled());
}

void TestPatientRegistrationDialog::testOKButtonDisabledWhenUrlInvalid()
{
    QUrl server_url("");
    QString proquint("kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov-t");
    auto dialog = new PatientRegistrationDialog(nullptr, server_url, proquint);

    auto buttonbox = dialog->findChild<QDialogButtonBox*>();
    QPushButton* ok_button = buttonbox->button(QDialogButtonBox::Ok);

    QVERIFY(!ok_button->isEnabled());
}

void TestPatientRegistrationDialog::testOKButtonEnabledWhenAllValid()
{
    QUrl server_url("https://example.com/");
    QString proquint("kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov-t");
    auto dialog = new PatientRegistrationDialog(nullptr, server_url, proquint);

    auto buttonbox = dialog->findChild<QDialogButtonBox*>();
    QPushButton* ok_button = buttonbox->button(QDialogButtonBox::Ok);

    QVERIFY(ok_button->isEnabled());
}

QTEST_MAIN(TestPatientRegistrationDialog)

#include "testpatientregistrationdialog.moc"
