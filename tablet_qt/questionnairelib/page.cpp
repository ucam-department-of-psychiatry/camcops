#include "page.h"
#include <QVBoxLayout>
#include <QWidget>


Page::Page() :
    m_type(PageType::Inherit)
{

}


Page::Page(const QList<ElementPtr>& elements) :
    m_type(PageType::Inherit),
    m_elements(elements)
{
}


Page::Page(std::initializer_list<ElementPtr> elements) :
    m_type(PageType::Inherit),
    m_elements(elements)
{
}


Page* Page::setType(PageType type)
{
    m_type = type;
    return this;
}


Page* Page::setTitle(const QString& title)
{
    m_title = title;
    return this;
}


Page* Page::addElement(const ElementPtr& element)
{
    m_elements.append(element);
    return this;
}


PageType Page::type() const
{
    return m_type;
}


QString Page::title() const
{
    return m_title;
}


QPointer<QWidget> Page::widget(Questionnaire* questionnaire) const
{
    QPointer<QWidget> pagewidget = new QWidget();
    QVBoxLayout* pagelayout = new QVBoxLayout;
    pagewidget->setLayout(pagelayout);
    for (ElementPtr e : m_elements) {
        pagelayout->addWidget(e->getWidget(questionnaire));
    }
    QSizePolicy sp(QSizePolicy::Ignored, QSizePolicy::Minimum);
    pagewidget->setSizePolicy(sp);
    pagewidget->setObjectName("debug_yellow"); // ***
    return pagewidget;
}
