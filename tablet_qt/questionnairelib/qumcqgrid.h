#pragma once
#include "namevalueoptions.h"
#include "mcqgridsubtitle.h"
#include "quelement.h"
#include "questionwithonefield.h"

class BooleanWidget;
class QGridLayout;


class QuMCQGrid : public QuElement
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
public:
    QuMCQGrid(QList<QuestionWithOneField> question_field_pairs,
              const NameValueOptions& options);
    QuMCQGrid* setWidth(int question_width, QList<int> option_widths);
    QuMCQGrid* setTitle(const QString& title);
    QuMCQGrid* setSubtitles(QList<McqGridSubtitle> subtitles);
    QuMCQGrid* setExpand(bool expand);
protected:
    void setFromFields();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int colnum(int value_index) const;
    void addOptions(QGridLayout* grid, int row);
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
};
