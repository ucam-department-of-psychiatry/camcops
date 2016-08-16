#include "element.h"
#include <QWidget>


Element::Element() :
    m_widget(nullptr)
{
}


Element::~Element()
{
}


QPointer<QWidget> Element::getWidget(Questionnaire* questionnaire)
{
    if (!m_widget) {
        // not yet made, or deleted by Qt
        m_widget = makeWidget(questionnaire);
    }
    return m_widget;
}
