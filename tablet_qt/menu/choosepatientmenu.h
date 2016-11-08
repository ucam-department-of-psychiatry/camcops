#pragma once
#include <QList>
#include <QString>
#include "menulib/menuwindow.h"
class Patient;
using PatientPtr = QSharedPointer<Patient>;
using PatientPtrList = QList<PatientPtr>;


class ChoosePatientMenu : public MenuWindow
{
    Q_OBJECT
public:
    ChoosePatientMenu(CamcopsApp& app);
    virtual void build() override;
    virtual void viewItem();
    virtual void editItem();
    virtual void deleteItem();
    void editPatient(bool read_only);
    void deletePatient();
public slots:
    void addPatient();
protected:
    PatientPtrList getAllPatients();
};
