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
#include "namevalueoptions.h"
#include "mcqgridsubtitle.h"
#include "quelement.h"
#include "questionwithtwofields.h"

class BooleanWidget;
class QGridLayout;
class QuMCQGridDoubleSignaller;


class QuMCQGridDouble : public QuElement
{
    // Offers a grid of pairs of multiple-choice questions, where several
    // sets of questions share the same possible responses. For example:
    //
    //              How much do you like it?    How expensive is it?
    //              Not at all ... Lots         Cheap ... Expensive
    // 1. Banana        O       O   O             O    O      O
    // 2. Diamond       O       O   O             O    O      O
    // 3. ...

    Q_OBJECT
    friend class QuMCQGridDoubleSignaller;
public:
    QuMCQGridDouble(QList<QuestionWithTwoFields> questions_with_fields,
                    const NameValueOptions& options1,
                    const NameValueOptions& options2);
    virtual ~QuMCQGridDouble();
    QuMCQGridDouble* setWidth(int question_width,
                              QList<int> option1_widths,
                              QList<int> option2_widths);
    QuMCQGridDouble* setTitle(const QString& title);
    QuMCQGridDouble* setSubtitles(QList<McqGridSubtitle> subtitles);
    QuMCQGridDouble* setExpand(bool expand);
protected:
    void setFromFields();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int spacercol(bool first_field) const;
    int colnum(bool first_field, int value_index) const;
    void addOptions(QGridLayout* grid, int row);
protected slots:
    void clicked(int question_index, bool first_field, int value_index);
    void fieldValueChanged(int question_index, bool first_field,
                           const FieldRef* fieldref);
protected:
    QList<QuestionWithTwoFields> m_questions_with_fields;
    NameValueOptions m_options1;
    NameValueOptions m_options2;
    int m_question_width;
    QList<int> m_option1_widths;
    QList<int> m_option2_widths;
    QString m_title;
    QList<McqGridSubtitle> m_subtitles;
    bool m_expand;

    QList<QList<QPointer<BooleanWidget>>> m_widgets1;
    QList<QList<QPointer<BooleanWidget>>> m_widgets2;
    QList<QuMCQGridDoubleSignaller*> m_signallers;
};
