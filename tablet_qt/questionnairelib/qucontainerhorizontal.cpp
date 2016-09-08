#include "qucontainerhorizontal.h"
#include <QHBoxLayout>
#include <QWidget>
#include "questionnaire.h"


QuContainerHorizontal::QuContainerHorizontal()
{
}


QuContainerHorizontal::QuContainerHorizontal(
        const QList<QuElementPtr>& elements) :
    m_elements(elements)
{
}


QuContainerHorizontal::QuContainerHorizontal(
        std::initializer_list<QuElementPtr> elements) :
    m_elements(elements)
{
}


QuContainerHorizontal::QuContainerHorizontal(
        std::initializer_list<QuElement*> elements)
{
    for (auto e : elements) {
        addElement(e);
    }
}


QuContainerHorizontal* QuContainerHorizontal::addElement(
        const QuElementPtr& element)
{
    m_elements.append(element);
    return this;
}


QuContainerHorizontal* QuContainerHorizontal::addElement(
        QuElement* element)  // takes ownership
{
    m_elements.append(QuElementPtr(element));
    return this;
}


QPointer<QWidget> QuContainerHorizontal::makeWidget(
        Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
    QHBoxLayout* layout = new QHBoxLayout();
    widget->setLayout(layout);
    for (auto e : m_elements) {
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w);
    }
    return widget;
}


QList<QuElementPtr> QuContainerHorizontal::subelements() const
{
    return m_elements;
}
