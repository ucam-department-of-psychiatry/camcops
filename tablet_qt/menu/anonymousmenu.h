#pragma once
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class AnonymousMenu : public MenuWindow
{
    Q_OBJECT
public:
    AnonymousMenu(CamcopsApp& app);
};
