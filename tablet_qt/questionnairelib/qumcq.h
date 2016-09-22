#pragma once
#include <QList>
#include <QPointer>
#include "lib/fieldref.h"
#include "namevalueoptions.h"
#include "quelement.h"

class BooleanWidget;


class QuMCQ : public QuElement
{
    // Offers a single multiple-choice question.
    // There are a variety of display formats.

    Q_OBJECT
public:
    QuMCQ(FieldRefPtr fieldref, const NameValueOptions& options);
    QuMCQ* setRandomize(bool randomize);
    QuMCQ* setShowInstruction(bool show_instruction);
    QuMCQ* setHorizontal(bool horizontal);
    QuMCQ* setAsTextButton(bool as_text_button);
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
    QList<QPointer<BooleanWidget>> m_widgets;
};
