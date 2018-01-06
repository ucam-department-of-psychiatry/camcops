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
#include <QSharedPointer>
#include <QVariant>
#include "db/fieldref.h"
#include "questionnairelib/quelement.h"
#include "questionnairelib/questionwithonefield.h"

class BooleanWidget;
class LabelWordWrapWide;
class QSignalMapper;


class QuMultipleResponse : public QuElement
{
    // Offers an n-from-many question. For example:
    //
    // Which are your TWO favourites, from the list:
    //   [X] Banana
    //   [ ] Diamond
    //   [ ] Apple
    //   [X] Bapple
    //   [ ] Gru

    Q_OBJECT
public:
    QuMultipleResponse();
    QuMultipleResponse(const QVector<QuestionWithOneField>& items);
    QuMultipleResponse(std::initializer_list<QuestionWithOneField> items);
    QuMultipleResponse* addItem(const QuestionWithOneField& item);
    QuMultipleResponse* setRandomize(bool randomize);
    QuMultipleResponse* setShowInstruction(bool show_instruction);
    QuMultipleResponse* setInstruction(const QString& instruction);
    QuMultipleResponse* setHorizontal(bool horizontal);
    QuMultipleResponse* setAsTextButton(bool as_text_button);
    QuMultipleResponse* setBold(bool bold);
public slots:
    QuMultipleResponse* setMinimumAnswers(int minimum_answers);
    QuMultipleResponse* setMaximumAnswers(int maximum_answers);
protected:
    void commonConstructor();
    void setFromFields();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int minimumAnswers() const;
    int maximumAnswers() const;
    int nTrueAnswers() const;
    QString defaultInstruction() const;
    bool validIndex(int index);
    virtual bool missingInput() const override;
    void minOrMaxChanged();
protected slots:
    void clicked(int index);
    void fieldValueChanged();
protected:
    QVector<QuestionWithOneField> m_items;
    int m_minimum_answers;  // negative for "not specified"
    int m_maximum_answers;  // negative for "not specified"
    bool m_randomize;
    bool m_show_instruction;
    QString m_instruction;
    bool m_horizontal;
    bool m_as_text_button;
    bool m_bold;

    QVector<QPointer<BooleanWidget>> m_widgets;
    LabelWordWrapWide* m_instruction_label;
};
