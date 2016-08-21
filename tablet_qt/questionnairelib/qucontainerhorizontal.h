#pragma once
#include "quelement.h"


class QuContainerHorizontal : public Cloneable<QuElement,
                                               QuContainerHorizontal>
{
public:
    QuContainerHorizontal();
    QuContainerHorizontal(const QList<QuElementPtr>& elements);
    QuContainerHorizontal(std::initializer_list<QuElementPtr> elements);
    QuContainerHorizontal& addElement(const QuElementPtr& element);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
protected:
    QList<QuElementPtr> m_elements;
};
