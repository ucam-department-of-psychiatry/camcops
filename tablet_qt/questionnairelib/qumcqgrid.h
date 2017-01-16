/*
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
#include "common/layouts.h"
#include "namevalueoptions.h"
#include "mcqgridsubtitle.h"
#include "quelement.h"
#include "questionwithonefield.h"

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
    QuMcqGrid(QList<QuestionWithOneField> question_field_pairs,
              const NameValueOptions& options);
    virtual ~QuMcqGrid();
    QuMcqGrid* setWidth(int question_width, QList<int> option_widths);
    QuMcqGrid* setTitle(const QString& title);
    QuMcqGrid* setSubtitles(QList<McqGridSubtitle> subtitles);
    QuMcqGrid* setExpand(bool expand);
protected:
    void setFromFields();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int colnum(int value_index) const;
    void addOptions(GridLayout* grid, int row);
protected slots:
    void clicked(int question_index, int value_index);
    void fieldValueChanged(int question_index, const FieldRef* fieldref);

protected:
    QList<QuestionWithOneField> m_question_field_pairs;
    NameValueOptions m_options;
    int m_question_width;
    QList<int> m_option_widths;
    QString m_title;
    QList<McqGridSubtitle> m_subtitles;
    bool m_expand;
    QList<QList<QPointer<BooleanWidget>>> m_widgets;
    QList<QuMcqGridSignaller*> m_signallers;
};
