/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
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
    virtual OpenableWidget* editor();

protected:
    CamcopsApp& m_app;
    virtual QString getPageTitle();
    void fontSizeChanged();
    void fontSettingsSaved();
    void fontSettingsCancelled();
    void resetFontSize();
    virtual void setUpPage(QuPagePtr page);
    QString
        demoText(const QString& text, uiconst::FontSize fontsize_type) const;

    QPointer<Questionnaire> m_fontsize_questionnaire;
    FieldRefPtr m_fontsize_fr;
};
