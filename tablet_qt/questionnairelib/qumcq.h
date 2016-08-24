#pragma once
#include <QList>
#include <QPointer>
#include "lib/fieldref.h"
#include "widgets/booleanwidget.h"
#include "namevaluepair.h"
#include "quelement.h"


class QuMCQ : public QuElement
{
    Q_OBJECT
public:
    QuMCQ(FieldRefPtr fieldref, const NameValuePairList& options);
    QuMCQ* setRandomize(bool randomize);
    QuMCQ* setShowInstruction(bool show_instruction);
    QuMCQ* setHorizontal(bool horizontal);
    QuMCQ* setAsTextButton(bool as_text_button);
    void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual bool complete() const override;
protected slots:
    void clicked(int index);
    void valueChanged(const QVariant& value);
    int chosenIndex(const QVariant& value) const;
protected:
    FieldRefPtr m_fieldref;
    NameValuePairList m_options;
    bool m_randomize;
    bool m_show_instruction;
    bool m_horizontal;
    bool m_as_text_button;
    QList<QPointer<BooleanWidget>> m_widgets;
    QMap<QVariant, int> m_value_to_index;
    QMap<int, QVariant> m_index_to_value;
};
