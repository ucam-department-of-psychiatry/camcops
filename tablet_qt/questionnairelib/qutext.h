/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
#include "db/fieldref.h"
#include "common/uiconst.h"
#include "questionnairelib/quelement.h"

class LabelWordWrapWide;


class QuText : public QuElement
{
    // Provides static text, or text from a field.

    Q_OBJECT
public:
    QuText(const QString& text = "");
    QuText(FieldRefPtr fieldref);
    QuText* setBig(bool setBig = true);
    QuText* setBold(bool setBold = true);
    QuText* setItalic(bool setItalic = true);
    QuText* setWarning(bool setWarning = true);
    QuText* setFormat(Qt::TextFormat format);
    QuText* setOpenLinks(bool open_links = true);
    QuText* setAlignment(Qt::Alignment alignment);
    void setText(const QString& text, bool repolish = true);
    friend class SettingsMenu;
protected:
    void commonConstructor();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    void forceFontSize(int fontsize_pt, bool repolish = true);  // for SettingsMenu only
    void setWidgetFontSize(int fontsize_pt, bool repolish = false);
    void repolishWidget();
protected slots:
    void fieldValueChanged(const FieldRef* fieldref);
protected:
    QString m_text;
    FieldRefPtr m_fieldref;
    uiconst::FontSize m_fontsize;
    bool m_bold;
    bool m_italic;
    bool m_warning;
    Qt::TextFormat m_text_format;
    bool m_open_links;
    Qt::Alignment m_alignment;
    QPointer<LabelWordWrapWide> m_label;
    int m_forced_fontsize_pt;
};
