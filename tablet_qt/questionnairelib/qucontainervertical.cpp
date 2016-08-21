#include "qucontainervertical.h"
#include <QVBoxLayout>
#include <QWidget>
#include "questionnaire.h"


QuContainerVertical::QuContainerVertical()
{
}


QuContainerVertical::QuContainerVertical(const QList<QuElementPtr>& elements) :
    m_elements(elements)
{
}


QuContainerVertical::QuContainerVertical(
        std::initializer_list<QuElementPtr> elements) :
    m_elements(elements)
{
}


QuContainerVertical& QuContainerVertical::addElement(
        const QuElementPtr& element)
{
    m_elements.append(element);
    return *this;
}


QPointer<QWidget> QuContainerVertical::makeWidget(Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
    QVBoxLayout* layout = new QVBoxLayout();
    widget->setLayout(layout);
    for (auto e : m_elements) {
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w);
    }
    return widget;
}


QList<QuElementPtr> QuContainerVertical::subelements() const
{
    return m_elements;
}
