/*
    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "quhorizontalcontainer.h"
#include <QWidget>
#include "common/layouts.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/basewidget.h"
#include "widgets/flowlayouthfw.h"


const Qt::Alignment QuHorizontalContainer::DefaultWidgetAlignment = Qt::AlignLeft | Qt::AlignVCenter;
// - http://stackoverflow.com/questions/4539406/nonstatic-member-as-a-default-argument-of-a-nonstatic-member-function
// - http://en.cppreference.com/w/cpp/language/default_arguments


QuHorizontalContainer::QuHorizontalContainer()
{
}


QuHorizontalContainer::QuHorizontalContainer(
        const QList<QuElementPtr>& elements,
        Qt::Alignment alignment) :
    m_elements(elements)
{
    createAlignments(alignment);
    commonConstructor();
}


QuHorizontalContainer::QuHorizontalContainer(
        std::initializer_list<QuElementPtr> elements,
        Qt::Alignment alignment) :
    m_elements(elements)
{
    createAlignments(alignment);
    commonConstructor();
}


QuHorizontalContainer::QuHorizontalContainer(
        std::initializer_list<QuElement*> elements,
        Qt::Alignment alignment)
{
    for (auto e : elements) {
        addElement(e, alignment);
    }
    commonConstructor();
}


void QuHorizontalContainer::commonConstructor()
{
    m_add_stretch_right = true;
}


void QuHorizontalContainer::createAlignments(Qt::Alignment alignment)
{
    m_widget_alignments.clear();
    for (int i = 0; i < m_elements.size(); ++i) {
        m_widget_alignments.append(alignment);
    }
}


QuHorizontalContainer* QuHorizontalContainer::addElement(
        const QuElementPtr& element, Qt::Alignment alignment)
{
    m_elements.append(element);
    m_widget_alignments.append(alignment);
    return this;
}


QuHorizontalContainer* QuHorizontalContainer::addElement(
        QuElement* element, Qt::Alignment alignment)  // takes ownership
{
    // If you add a nullptr, it will be ignored.
    if (element) {
        m_elements.append(QuElementPtr(element));
        m_widget_alignments.append(alignment);
    }
    return this;
}


QuHorizontalContainer* QuHorizontalContainer::setWidgetAlignment(
        Qt::Alignment alignment)
{
    createAlignments(alignment);
    return this;
}


QuHorizontalContainer* QuHorizontalContainer::setAddStretchRight(
        bool add_stretch_right)
{
    m_add_stretch_right = add_stretch_right;
    return this;
}


QPointer<QWidget> QuHorizontalContainer::makeWidget(
        Questionnaire* questionnaire)
{
    QPointer<QWidget> widget(new BaseWidget());
    widget->setSizePolicy(UiFunc::expandingFixedHFWPolicy());

    HBoxLayout* layout = new HBoxLayout();

    // widget->setObjectName(CssConst::DEBUG_YELLOW);
    layout->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(layout);
    for (int i = 0; i < m_elements.size(); ++i) {
        auto e = m_elements.at(i);
        auto alignment = m_widget_alignments.at(i);
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w, 0, alignment);
    }
    if (m_add_stretch_right) {
        layout->addStretch();
    }
    return widget;
}


QList<QuElementPtr> QuHorizontalContainer::subelements() const
{
    return m_elements;
}
