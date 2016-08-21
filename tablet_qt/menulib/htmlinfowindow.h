#pragma once
#include "widgets/openablewidget.h"

class CamcopsApp;


class HtmlInfoWindow : public OpenableWidget
{
    Q_OBJECT
public:
    HtmlInfoWindow(CamcopsApp& app, const QString& title,
                   const QString& filename, const QString& icon);
protected:
    CamcopsApp& m_app;
};
