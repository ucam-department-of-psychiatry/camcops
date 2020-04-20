/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once
#include <QDialog>
#include <QPointer>
class QDialogButtonBox;
class QLabel;
class QLineEdit;
class QUrl;


class PatientRegistrationDialog : public QDialog
{
    // Dialogue to select mode of operation.
    // MODAL and BLOCKING: call exec() and read serverUrl() and
    // patientProquint() if it succeeds.

    Q_OBJECT
public:
    PatientRegistrationDialog(QWidget* parent = nullptr);
    QString patientProquint() const;
    QUrl serverUrl() const;
protected:
    QPointer<QDialogButtonBox> m_buttonbox;
    QPointer<QLineEdit> m_editor_patient_proquint;
    QPointer<QLineEdit> m_editor_server_url;
    bool m_url_valid;
    bool m_proquint_valid;
    void updateOkButtonEnabledState();

protected slots:
    virtual void proquintChanged();
    virtual void urlChanged();
};
