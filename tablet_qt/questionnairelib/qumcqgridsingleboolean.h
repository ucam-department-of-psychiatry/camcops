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
class QuMCQGridSingleBooleanSignaller;


class QuMCQGridSingleBoolean : public QuElement
{
    // Offers a grid of multiple-choice questions, each with a single boolean.
    // For example:
    //
    //              How much do you like it?    Do you own one?
    //              Not at all ... Lots
    // 1. Banana        O       O   O                X
    // 2. Diamond       O       O   O                .
    // 3. ...

    Q_OBJECT
    friend class QuMCQGridSingleBooleanSignaller;
public:
    QuMCQGridSingleBoolean();
public:
    QuMCQGridSingleBoolean(QList<QuestionWithTwoFields> questions_with_fields,
                           const NameValueOptions& mcq_options,
                           const QString& boolean_text);
    virtual ~QuMCQGridSingleBoolean();
    QuMCQGridSingleBoolean* setBooleanLeft(bool boolean_left);
    QuMCQGridSingleBoolean* setWidth(int question_width,
                                     QList<int> mcq_option_widths,
                                     int boolean_width);
    QuMCQGridSingleBoolean* setTitle(const QString& title);
    QuMCQGridSingleBoolean* setSubtitles(QList<McqGridSubtitle> subtitles);
    QuMCQGridSingleBoolean* setExpand(bool expand);
protected:
    void setFromFields();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int mcqColnum(int value_index) const;
    int booleanColnum() const;
    int spacercol(bool first) const;
    void addOptions(QGridLayout* grid, int row);
protected slots:
    void mcqClicked(int question_index, int value_index);
    void booleanClicked(int question_index);
    void mcqFieldValueChanged(int question_index, const FieldRef* fieldref);
    void booleanFieldValueChanged(int question_index, const FieldRef* fieldref);
protected:
    bool m_boolean_left;
    QList<QuestionWithTwoFields> m_questions_with_fields;
    NameValueOptions m_mcq_options;
    QString m_boolean_text;
    int m_question_width;
    QList<int> m_mcq_option_widths;
    int m_boolean_width;
    QString m_title;
    QList<McqGridSubtitle> m_subtitles;
    bool m_expand;

    QList<QList<QPointer<BooleanWidget>>> m_mcq_widgets;
    QList<QPointer<BooleanWidget>> m_boolean_widgets;
    QList<QuMCQGridSingleBooleanSignaller*> m_signallers;
};
