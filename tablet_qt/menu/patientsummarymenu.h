#pragma once
#include "menulib/menuwindow.h"


class PatientSummaryMenu : public MenuWindow
{
    Q_OBJECT
public:
    PatientSummaryMenu(CamcopsApp& app);
    virtual void build() override;
public slots:
    void selectedPatientChanged(const Patient* patient);
    void taskFinished();
};
