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

#include <QString>
#include <QtTest/QtTest>
#include <QUrl>

#include "dialogs/patientregistrationdialog.h"

class TestPatientRegistrationDialog : public QObject
{
    Q_OBJECT

private slots:
    void testPatientProquint();
    void testServerUrlAsString();
    void testServerUrl();
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


QTEST_MAIN(TestPatientRegistrationDialog)

#include "testpatientregistrationdialog.moc"
