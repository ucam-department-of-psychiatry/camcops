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
#include "layouts/layouts.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/mcqgridsubtitle.h"
#include "questionnairelib/quelement.h"
#include "questionnairelib/questionwithonefield.h"

class BooleanWidget;
class QuMcqGridSignaller;


class QuMcqGrid : public QuElement
{
    // Offers a grid of multiple-choice questions, where several questions
    // share the same possible responses. For example:
    //
    //              How much do you like it?
    //              Not at all ... Lots
    // 1. Banana        O       O   O
    // 2. Diamond       O       O   O
    // 3. ...

    Q_OBJECT
    friend class QuMcqGridSignaller;

public:
    QuMcqGrid(const QVector<QuestionWithOneField>& question_field_pairs,
              const NameValueOptions& options);
    virtual ~QuMcqGrid();
    QuMcqGrid* setWidth(int question_width, const QVector<int>& option_widths);
    QuMcqGrid* setTitle(const QString& title);
    QuMcqGrid* setSubtitles(const QVector<McqGridSubtitle>& subtitles);
    QuMcqGrid* setExpand(bool expand);
    QuMcqGrid* setStripy(bool stripy);
protected:
    void setFromFields();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int colnum(int value_index) const;
    void addOptions(GridLayout* grid, int row);
protected slots:
    void clicked(int question_index, int value_index);
    void fieldValueOrMandatoryChanged(int question_index,
                                      const FieldRef* fieldref);

protected:
    QVector<QuestionWithOneField> m_question_field_pairs;
    NameValueOptions m_options;
    int m_question_width;
    QVector<int> m_option_widths;
    QString m_title;
    QVector<McqGridSubtitle> m_subtitles;
    bool m_expand;
    bool m_stripy;
    QVector<QVector<QPointer<BooleanWidget>>> m_widgets;
    QVector<QuMcqGridSignaller*> m_signallers;
};
