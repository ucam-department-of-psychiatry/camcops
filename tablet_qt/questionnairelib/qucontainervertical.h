#pragma once
#include "quelement.h"


class QuContainerVertical : public Cloneable<QuElement, QuContainerVertical>
{
public:
    QuContainerVertical();
    QuContainerVertical(const QList<QuElementPtr>& elements);
    QuContainerVertical(std::initializer_list<QuElementPtr> elements);
    QuContainerVertical& addElement(const QuElementPtr& element);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
protected:
    QList<QuElementPtr> m_elements;
};
