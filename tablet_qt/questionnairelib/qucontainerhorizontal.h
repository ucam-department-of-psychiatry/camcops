#pragma once
#include "quelement.h"


class QuContainerHorizontal : public QuElement
{
    // Allows the arrangements of other elements into a horizontal layout.

    Q_OBJECT
public:
    QuContainerHorizontal();
    QuContainerHorizontal(const QList<QuElementPtr>& elements);
    QuContainerHorizontal(std::initializer_list<QuElementPtr> elements);
    QuContainerHorizontal(std::initializer_list<QuElement*> elements);  // takes ownership
    QuContainerHorizontal* addElement(const QuElementPtr& element);
    QuContainerHorizontal* addElement(QuElement* element);  // takes ownership
    QuContainerHorizontal* setAddStretchRight(bool add_stretch_right);
protected:
    void commonConstructor();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
protected:
    QList<QuElementPtr> m_elements;
    bool m_add_stretch_right;
};
