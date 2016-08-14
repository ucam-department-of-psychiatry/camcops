#pragma once
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class PatientSummaryMenu : public MenuWindow
{
    Q_OBJECT
public:
    PatientSummaryMenu(CamcopsApp& app);
};
