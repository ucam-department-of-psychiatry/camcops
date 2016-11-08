#include "choosepatientmenu.h"
#include <QDebug>
#include "dbobjects/patient.h"
#include "lib/uifunc.h"
#include "menulib/menuheader.h"


ChoosePatientMenu::ChoosePatientMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Choose patient"),
               UiFunc::iconFilename(UiConst::ICON_CHOOSE_PATIENT))
{
}


void ChoosePatientMenu::build()
{
    // Patient
    PatientPtrList patients = m_app.getAllPatients();
    m_items.clear();
    qDebug() << Q_FUNC_INFO << "-" << patients.size() << "patients";
    for (auto patient : patients) {
        m_items.append(MenuItem(patient));
    }

    // Call parent buildMenu()
    MenuWindow::build();

    // Set header buttons
    m_p_header->offerAdd(true);
    m_p_header->offerView(false);  // until one is clicked
    m_p_header->offerEditDelete(false);  // until one is clicked

    connect(m_p_header, &MenuHeader::addClicked,
            this, &ChoosePatientMenu::addPatient,
            Qt::UniqueConnection);
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
    qDebug() << Q_FUNC_INFO;
    // The patient we create here needs to stay in scope for the duration of
    // editing! The simplest way is to use a member object to hold the pointer.

    PatientPtr patient = PatientPtr(new Patient(m_app, m_app.db()));
    patient->save();
    OpenableWidget* widget = patient->editor(false);
    m_app.open(widget, TaskPtr(nullptr), false, patient);
}


void ChoosePatientMenu::editPatient(bool read_only)
{
    qDebug() << Q_FUNC_INFO;
    PatientPtr patient = currentPatient();
    OpenableWidget* widget = patient->editor(read_only);
    m_app.open(widget, TaskPtr(nullptr), false, patient);
}


void ChoosePatientMenu::deletePatient()
{
    qDebug() << Q_FUNC_INFO;
}
