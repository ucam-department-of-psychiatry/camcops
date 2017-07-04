/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

// #define DEBUG_VERBOSE

#include "choosepatientmenu.h"
#include <QDebug>
#include <QMessageBox>
#include <QPushButton>
#include "dbobjects/patient.h"
#include "lib/uifunc.h"
#include "menulib/menuheader.h"


ChoosePatientMenu::ChoosePatientMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Choose patient"),
               uifunc::iconFilename(uiconst::ICON_CHOOSE_PATIENT))
{
    connect(&m_app, &CamcopsApp::selectedPatientDetailsChanged,
            this, &ChoosePatientMenu::selectedPatientDetailsChanged,
            Qt::UniqueConnection);

    // Set other header buttons
    m_p_header->offerAdd(true);

    connect(m_p_header, &MenuHeader::addClicked,
            this, &ChoosePatientMenu::addPatient,
            Qt::UniqueConnection);
}


void ChoosePatientMenu::build()
{
    // Patient
    PatientPtrList patients = m_app.getAllPatients();
    m_items.clear();
    qDebug() << Q_FUNC_INFO << "-" << patients.size() << "patient(s)";
    for (auto patient : patients) {
        m_items.append(MenuItem(patient));
    }

    // Call parent buildMenu()
    MenuWindow::build();
    // ... which has special facilities for detecting a currently selected
    // patient and setting offerView, offerEditDelete
}


void ChoosePatientMenu::viewItem()
{
    editPatient(true);
}


void ChoosePatientMenu::editItem()
{
    editPatient(false);
}


void ChoosePatientMenu::deleteItem()
{
    deletePatient();
}


void ChoosePatientMenu::addPatient()
{
#ifdef DEBUG_VERBOSE
    qDebug() << Q_FUNC_INFO;
#endif
    // The patient we create here needs to stay in scope for the duration of
    // editing! The simplest way is to use a member object to hold the pointer.

    PatientPtr patient = PatientPtr(new Patient(m_app, m_app.db()));
    patient->save();
    OpenableWidget* widget = patient->editor(false);
    m_app.open(widget, TaskPtr(nullptr), false, patient);
}


void ChoosePatientMenu::editPatient(bool read_only)
{
#ifdef DEBUG_VERBOSE
    qDebug() << Q_FUNC_INFO;
#endif
    PatientPtr patient = currentPatient();
    if (!patient) {
        uifunc::alert("Bug: null patient pointer in ChoosePatientMenu::editPatient");
        return;
    }
    OpenableWidget* widget = patient->editor(read_only);
    m_app.open(widget, TaskPtr(nullptr), false, patient);
}


void ChoosePatientMenu::deletePatient()
{
    qDebug() << Q_FUNC_INFO;
    PatientPtr patient = currentPatient();
    if (!patient) {
        uifunc::alert("Bug: null patient pointer in ChoosePatientMenu::editPatient");
        return;
    }
    QString patient_details = QString("%1, %2 (%3, %4, DOB %5)\n%6")
            .arg(patient->surname().toUpper(),
                 patient->forename(),
                 QString("%1 y").arg(patient->ageYears()),
                 patient->sex(),
                 patient->dobText(),
                 patient->shortIdnumSummary());

    // First check
    {
        QMessageBox msgbox(this);
        msgbox.setIcon(QMessageBox::Warning);
        msgbox.setWindowTitle(tr("Delete patient"));
        msgbox.setText(tr("Delete this patient?") + "\n\n" +  patient_details);
        QAbstractButton* delete_button = msgbox.addButton(
                    tr("Yes, delete"), QMessageBox::YesRole);
        msgbox.addButton(tr("No, cancel"), QMessageBox::NoRole);
        msgbox.exec();
        if (msgbox.clickedButton() != delete_button) {
            return;
        }
    }

    // Second check
    int n_tasks = patient->numTasks();
    if (n_tasks > 0) {
        QMessageBox msgbox(this);
        msgbox.setIcon(QMessageBox::Warning);
        msgbox.setWindowTitle(tr("Delete patient WITH TASKS"));
        msgbox.setText(tr("Delete this patient?") + "\n\n" +  patient_details +
                       QString("\n\n<b>THERE ARE %1 ASSOCIATED TASKS!</b>")
                            .arg(n_tasks));
        QAbstractButton* delete_button = msgbox.addButton(
                    tr("Yes, delete despite tasks"), QMessageBox::YesRole);
        msgbox.addButton(tr("No, cancel"), QMessageBox::NoRole);
        msgbox.exec();
        if (msgbox.clickedButton() != delete_button) {
            return;
        }
    }

    // Delete
    qInfo() << "Deleting patient:" << patient_details;
    patient->deleteFromDatabase();
    qInfo() << "... patient deleted";
    build();
}


void ChoosePatientMenu::selectedPatientDetailsChanged(const Patient* patient)
{
    Q_UNUSED(patient);
    build();  // refresh patient list
}
