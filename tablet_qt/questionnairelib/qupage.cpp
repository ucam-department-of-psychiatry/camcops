#include "qupage.h"
#include <QVBoxLayout>
#include <QWidget>
#include "lib/fieldref.h"


QuPage::QuPage() :
    m_type(PageType::Inherit)
{

}


QuPage::QuPage(const QList<QuElementPtr>& elements) :
    m_type(PageType::Inherit),
    m_elements(elements)
{
}


QuPage::QuPage(std::initializer_list<QuElementPtr> elements) :
    m_type(PageType::Inherit),
    m_elements(elements)
{
}

QuPage::QuPage(std::initializer_list<QuElement*> elements) :  // takes ownership
    m_type(PageType::Inherit)
{
    for (auto e : elements) {
        addElement(e);
    }
}


QuPage* QuPage::setType(PageType type)
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


QuPage* QuPage::addElement(QuElement* element)  // takes ownership
{
    addElement(QuElementPtr(element));
    return this;
}


QuPage::PageType QuPage::type() const
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
    QVBoxLayout* pagelayout = new QVBoxLayout();
    pagewidget->setLayout(pagelayout);
    for (QuElementPtr e : m_elements) {
        QPointer<QWidget> w = e->widget(questionnaire);
        pagelayout->addWidget(w);  // takes ownership
        connect(e.data(), &QuElement::elementValueChanged,
                this, &QuPage::elementValueChanged,
                Qt::UniqueConnection);
    }
    pagewidget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);
    // pagewidget->setObjectName("debug_yellow");
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
            if (!e->visible()) {
                qWarning() << Q_FUNC_INFO << "TASK BUG: invisible widget "
                                             "blocking progress";
            }
            return true;
        }
    }
    return false;
}


void QuPage::closing()
{
    QList<QuElementPtr> elements = allElements();
    for (QuElementPtr e : elements) {
        e->closing();
    }
}
