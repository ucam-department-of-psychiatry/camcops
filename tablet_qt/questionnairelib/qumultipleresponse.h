#pragma once
#include <QList>
#include <QSharedPointer>
#include <QVariant>
#include "lib/fieldref.h"
#include "quelement.h"
#include "questionwithonefield.h"

class BooleanWidget;
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
    QuMultipleResponse(const QList<QuestionWithOneField> items);
    QuMultipleResponse(std::initializer_list<QuestionWithOneField> items);
    QuMultipleResponse* addItem(const QuestionWithOneField& item);
    QuMultipleResponse* setMinimumAnswers(int minimum_answers);
    QuMultipleResponse* setMaximumAnswers(int maximum_answers);
    QuMultipleResponse* setRandomize(bool randomize);
    QuMultipleResponse* setShowInstruction(bool show_instruction);
    QuMultipleResponse* setInstruction(const QString& instruction);
    QuMultipleResponse* setAsTextButton(bool as_text_button);
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
protected slots:
    void clicked(int index);
    void fieldValueChanged();
protected:
    QList<QuestionWithOneField> m_items;
    int m_minimum_answers;  // negative for "not specified"
    int m_maximum_answers;  // negative for "not specified"
    bool m_randomize;
    bool m_show_instruction;
    QString m_instruction;
    bool m_as_text_button;

    QList<QPointer<BooleanWidget>> m_widgets;
};
