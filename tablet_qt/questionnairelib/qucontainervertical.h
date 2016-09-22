#pragma once
#include "quelement.h"


class QuContainerVertical : public QuElement
{
    // Allows the arrangements of other elements into a vertical layout.

    Q_OBJECT
public:
    QuContainerVertical();
    QuContainerVertical(const QList<QuElementPtr>& elements);
    QuContainerVertical(std::initializer_list<QuElementPtr> elements);
    QuContainerVertical(std::initializer_list<QuElement*> elements);  // takes ownership
    QuContainerVertical* addElement(const QuElementPtr& element);
    QuContainerVertical* addElement(QuElement* element);  // takes ownership
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
protected:
    QList<QuElementPtr> m_elements;
};
