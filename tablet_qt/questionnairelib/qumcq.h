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
#include <QList>
#include <QPointer>
#include "db/fieldref.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/quelement.h"

class BooleanWidget;


class QuMcq : public QuElement
{
    // Offers a single multiple-choice question.
    // There are a variety of display formats.

    Q_OBJECT
public:
    QuMcq(FieldRefPtr fieldref, const NameValueOptions& options);
    QuMcq* setRandomize(bool randomize);
    QuMcq* setShowInstruction(bool show_instruction);
    QuMcq* setHorizontal(bool horizontal);
    QuMcq* setAsTextButton(bool as_text_button);
    QuMcq* setBold(bool bold);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void clicked(int index);
    void fieldValueChanged(const FieldRef* fieldref);
protected:
    FieldRefPtr m_fieldref;
    NameValueOptions m_options;
    bool m_randomize;
    bool m_show_instruction;
    bool m_horizontal;
    bool m_as_text_button;
    bool m_bold;
    QVector<QPointer<BooleanWidget>> m_widgets;
};
