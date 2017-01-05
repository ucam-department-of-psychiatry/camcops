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

#include "quflowcontainer.h"
#include <QWidget>
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/basewidget.h"
#include "widgets/flowlayouthfw.h"


const Qt::Alignment QuFlowContainer::DefaultWidgetAlignment = Qt::AlignLeft | Qt::AlignVCenter;


QuFlowContainer::QuFlowContainer()
{
}


QuFlowContainer::QuFlowContainer(
        const QList<QuElementPtr>& elements,
        Qt::Alignment alignment) :
    m_elements(elements)
{
    createAlignments(alignment);
}


QuFlowContainer::QuFlowContainer(
        std::initializer_list<QuElementPtr> elements,
        Qt::Alignment alignment) :
    m_elements(elements)
{
    createAlignments(alignment);
}


QuFlowContainer::QuFlowContainer(
        std::initializer_list<QuElement*> elements,
        Qt::Alignment alignment)
{
    for (auto e : elements) {
        addElement(e, alignment);
    }
}


void QuFlowContainer::createAlignments(Qt::Alignment alignment)
{
    m_widget_alignments.clear();
    for (int i = 0; i < m_elements.size(); ++i) {
        m_widget_alignments.append(alignment);
    }
}


QuFlowContainer* QuFlowContainer::addElement(
        const QuElementPtr& element, Qt::Alignment alignment)
{
    m_elements.append(element);
    m_widget_alignments.append(alignment);
    return this;
}


QuFlowContainer* QuFlowContainer::addElement(
        QuElement* element, Qt::Alignment alignment)  // takes ownership
{
    // If you add a nullptr, it will be ignored.
    if (element) {
        m_elements.append(QuElementPtr(element));
        m_widget_alignments.append(alignment);
    }
    return this;
}


QuFlowContainer* QuFlowContainer::setWidgetAlignment(
        Qt::Alignment alignment)
{
    createAlignments(alignment);
    return this;
}


QPointer<QWidget> QuFlowContainer::makeWidget(
        Questionnaire* questionnaire)
{
    QPointer<QWidget> widget(new BaseWidget());
    widget->setSizePolicy(UiFunc::expandingFixedHFWPolicy());

    FlowLayoutHfw* layout = new FlowLayoutHfw();
    // widget->setObjectName(CssConst::DEBUG_YELLOW);
    layout->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(layout);
    for (int i = 0; i < m_elements.size(); ++i) {
        auto e = m_elements.at(i);
        auto alignment = m_widget_alignments.at(i);
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w);  // uses QLayout::addWidget; no alignment option
        layout->setAlignment(w, alignment);  // this is QLayout::setAlignment
    }
    return widget;
}


QList<QuElementPtr> QuFlowContainer::subelements() const
{
    return m_elements;
}
