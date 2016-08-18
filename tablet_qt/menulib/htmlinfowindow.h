#pragma once
#include <QWidget>
#include "common/camcopsapp.h"


class HtmlInfoWindow : public QWidget
{
    Q_OBJECT
public:
    HtmlInfoWindow(CamcopsApp& app, const QString& title,
                   const QString& filename, const QString& icon);
protected:
    CamcopsApp& m_app;
};
