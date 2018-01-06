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
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/quelement.h"

class ClickableLabelWordWrapWide;


class QuPickerPopup : public QuElement
{
    // Offers a pop-up dialogue of choices, or device equivalent.

    Q_OBJECT
public:
    QuPickerPopup(FieldRefPtr fieldref, const NameValueOptions& options);
    QuPickerPopup* setPopupTitle(const QString& popup_title);
    QuPickerPopup* setRandomize(bool randomize);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void clicked();
    void fieldValueChanged(const FieldRef* fieldref);
protected:
    FieldRefPtr m_fieldref;
    NameValueOptions m_options;
    QString m_popup_title;
    bool m_randomize;
    QPointer<ClickableLabelWordWrapWide> m_label;
};
