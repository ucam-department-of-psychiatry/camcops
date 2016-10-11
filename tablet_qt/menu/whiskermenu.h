#pragma once
#include "menulib/menuwindow.h"


class WhiskerMenu : public MenuWindow
{
    Q_OBJECT
public:
    WhiskerMenu(CamcopsApp& app);
protected:
    OpenableWidget* configureWhisker(CamcopsApp& app);
    QString makeTitle(const QString& part1, const QString& part2) const;
    QString makeHint(const QString& part1, const QString& part2) const;
};
