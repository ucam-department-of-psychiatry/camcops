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

#pragma once
#include <QDialog>
#include <QPointer>
#include <QUrl>
class QDialogButtonBox;
class QLabel;
class ValidatingLineEdit;

class PatientRegistrationDialog : public QDialog
{
    // Dialogue to select mode of operation.
    // MODAL and BLOCKING: call exec() and read serverUrl() and
    // patientProquint() if it succeeds.

    Q_OBJECT

public:
    PatientRegistrationDialog(
        QWidget* parent = nullptr,
        const QUrl& server_url = QUrl(),
        const QString& patient_proquint = ""
    );
    QString patientProquint() const;
    QString serverUrlAsString() const;
    QUrl serverUrl() const;

protected:
    QPointer<QDialogButtonBox> m_buttonbox;
    QPointer<ValidatingLineEdit> m_editor_patient_proquint;
    QPointer<ValidatingLineEdit> m_editor_server_url;

protected slots:
    void updateOkButtonEnabledState();
};
