#include "qucontainerhorizontal.h"
#include <QHBoxLayout>
#include <QWidget>
#include "questionnairelib/questionnaire.h"


QuContainerHorizontal::QuContainerHorizontal()
{
}


QuContainerHorizontal::QuContainerHorizontal(
        const QList<QuElementPtr>& elements) :
    m_elements(elements)
{
    commonConstructor();
}


QuContainerHorizontal::QuContainerHorizontal(
        std::initializer_list<QuElementPtr> elements) :
    m_elements(elements)
{
    commonConstructor();
}


QuContainerHorizontal::QuContainerHorizontal(
        std::initializer_list<QuElement*> elements)
{
    for (auto e : elements) {
        addElement(e);
    }
    commonConstructor();
}


void QuContainerHorizontal::commonConstructor()
{
    m_add_stretch_right = false;
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
    // If you add a nullptr, it will be ignored.
    if (element) {
        m_elements.append(QuElementPtr(element));
    }
    return this;
}


QuContainerHorizontal* QuContainerHorizontal::setAddStretchRight(
        bool add_stretch_right)
{
    m_add_stretch_right = add_stretch_right;
    return this;
}


QPointer<QWidget> QuContainerHorizontal::makeWidget(
        Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
    // widget->setObjectName("debug_yellow");
    QHBoxLayout* layout = new QHBoxLayout();
    layout->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(layout);
    for (auto e : m_elements) {
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w);
    }
    if (m_add_stretch_right) {
        layout->addStretch();
    }
    return widget;
}


QList<QuElementPtr> QuContainerHorizontal::subelements() const
{
    return m_elements;
}
