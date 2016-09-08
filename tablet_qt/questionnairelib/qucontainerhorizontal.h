#pragma once
#include "quelement.h"


class QuContainerHorizontal : public QuElement
{
    Q_OBJECT
public:
    QuContainerHorizontal();
    QuContainerHorizontal(const QList<QuElementPtr>& elements);
    QuContainerHorizontal(std::initializer_list<QuElementPtr> elements);
    QuContainerHorizontal(std::initializer_list<QuElement*> elements);  // takes ownership
    QuContainerHorizontal* addElement(const QuElementPtr& element);
    QuContainerHorizontal* addElement(QuElement* element);  // takes ownership
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
protected:
    QList<QuElementPtr> m_elements;
};
