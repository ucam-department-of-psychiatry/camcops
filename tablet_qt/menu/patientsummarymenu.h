#pragma once
#include "menulib/menuwindow.h"


class PatientSummaryMenu : public MenuWindow
{
    Q_OBJECT
public:
    PatientSummaryMenu(CamcopsApp& app);
    virtual void build() override;
};
