/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once
#include "common/aliases_camcops.h"
#include "common/uiconst.h"
#include "widgets/openablewidget.h"

class CamcopsApp;
class Questionnaire;

class FontSizeWindow : public QObject
{
    Q_OBJECT
public:
    FontSizeWindow(CamcopsApp& app);
    OpenableWidget* editor(bool simplified);

protected:
    CamcopsApp& m_app;
    void fontSizeChanged();
    void fontSettingsSaved();
    void fontSettingsCancelled();
    void resetFontSize();
    QString demoText(const QString& text, uiconst::FontSize fontsize_type) const;
    void dpiOverrideChanged();

    QPointer<Questionnaire> m_fontsize_questionnaire;
    FieldRefPtr m_fontsize_fr;

    FieldRefPtr m_dpi_override_logical_fr;
    FieldRefPtr m_dpi_override_logical_x_fr;
    FieldRefPtr m_dpi_override_logical_y_fr;
    FieldRefPtr m_dpi_override_physical_fr;
    FieldRefPtr m_dpi_override_physical_x_fr;
    FieldRefPtr m_dpi_override_physical_y_fr;
};
