#include "quelement.h"
#include <QWidget>


QuElement::QuElement() :
    m_widget(nullptr),
    m_visible(true),
    m_mandatory(true)
{
}


QuElement::~QuElement()
{
}


QuElement* QuElement::setMandatory(bool mandatory)
{
    m_mandatory = mandatory;
    return this;
}


QuElement* QuElement::addTag(const QString& tag)
{
    m_tags.append(tag);
    return this;
}


bool QuElement::hasTag(const QString &tag)
{
    return m_tags.contains(tag);
}


QPointer<QWidget> QuElement::widget(Questionnaire* questionnaire)
{
    if (!m_widget) {
        // not yet made, or deleted by Qt
        m_widget = makeWidget(questionnaire);
    }
    return m_widget;
}


QList<QuElementPtr> QuElement::subelements() const
{
    return QList<QuElementPtr>();
}


void QuElement::show()
{
    setVisible(true);
}


void QuElement::hide()
{
    setVisible(false);
}


void QuElement::setVisible(bool visible)
{
    if (!m_widget || visible == m_visible) {
        return;
    }
    m_widget->setVisible(visible);
}


bool QuElement::mandatory() const
{
    return m_mandatory;
}


bool QuElement::complete() const
{
    return true;
}


bool QuElement::missingInput() const
{
    return mandatory() && !complete();
}


void QuElement::closing()
{
}
