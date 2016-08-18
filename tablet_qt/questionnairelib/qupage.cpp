#include "qupage.h"
#include <QVBoxLayout>
#include <QWidget>


QuPage::QuPage() :
    m_type(QuPageType::Inherit)
{

}


QuPage::QuPage(const QList<QuElementPtr>& elements) :
    m_type(QuPageType::Inherit),
    m_elements(elements)
{
}


QuPage::QuPage(std::initializer_list<QuElementPtr> elements) :
    m_type(QuPageType::Inherit),
    m_elements(elements)
{
}


QuPage* QuPage::setType(QuPageType type)
{
    m_type = type;
    return this;
}


QuPage* QuPage::setTitle(const QString& title)
{
    m_title = title;
    return this;
}


QuPage* QuPage::addElement(const QuElementPtr& element)
{
    m_elements.append(element);
    return this;
}


QuPageType QuPage::type() const
{
    return m_type;
}


QString QuPage::title() const
{
    return m_title;
}


QPointer<QWidget> QuPage::widget(Questionnaire* questionnaire) const
{
    QPointer<QWidget> pagewidget = new QWidget();
    QVBoxLayout* pagelayout = new QVBoxLayout;
    pagewidget->setLayout(pagelayout);
    for (QuElementPtr e : m_elements) {
        QPointer<QWidget> w = e->getWidget(questionnaire);
        pagelayout->addWidget(w);
    }
//    // In case the questionnaire is vertically short:
//    pagelayout->addStretch(); // ***
    QSizePolicy sp(QSizePolicy::Ignored, QSizePolicy::Minimum);
    pagewidget->setSizePolicy(sp);
    pagewidget->setObjectName("debug_yellow"); // ***
    return pagewidget;
}


QList<QuElementPtr> QuPage::allElements() const
{
    QList<QuElementPtr> elements;
    for (QuElementPtr e : m_elements) {
        elements.append(e);
        elements.append(e->subelements());
    }
    return elements;
}


bool QuPage::missingInput() const
{
    QList<QuElementPtr> elements = allElements();
    for (QuElementPtr e : elements) {
        if (e->missingInput()) {
            return true;
        }
    }
    return false;
}
