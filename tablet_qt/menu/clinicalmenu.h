#pragma once
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class ClinicalMenu : public MenuWindow
{
    Q_OBJECT
public:
    ClinicalMenu(CamcopsApp& app);
};
