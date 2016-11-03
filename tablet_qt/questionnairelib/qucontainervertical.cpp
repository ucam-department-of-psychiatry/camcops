#include "qucontainervertical.h"
#include <QVBoxLayout>
#include <QWidget>
#include "questionnairelib/questionnaire.h"


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


QuContainerVertical::QuContainerVertical(
        std::initializer_list<QuElement*> elements)  // takes ownership
{
    for (auto e : elements) {
        addElement(e);
    }
}


QuContainerVertical* QuContainerVertical::addElement(
        const QuElementPtr& element)
{
    m_elements.append(element);
    return this;
}


QuContainerVertical* QuContainerVertical::addElement(
        QuElement* element)  // takes ownership
{
    // If you add a nullptr, it will be ignored.
    if (element) {
        m_elements.append(QuElementPtr(element));
    }
    return this;
}


QPointer<QWidget> QuContainerVertical::makeWidget(Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
    // widget->setObjectName(CssConst::DEBUG_YELLOW);
    QVBoxLayout* layout = new QVBoxLayout();
    layout->setContentsMargins(UiConst::NO_MARGINS);
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
