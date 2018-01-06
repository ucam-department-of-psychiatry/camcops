/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

// #define DEBUG_LAYOUT

#include "quflowcontainer.h"
#include <QWidget>
#include "common/cssconst.h"
#include "layouts/flowlayouthfw.h"
#include "lib/sizehelpers.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/basewidget.h"


const Qt::Alignment QuFlowContainer::DefaultWidgetAlignment =
        Qt::AlignLeft | Qt::AlignVCenter;


QuFlowContainer::QuFlowContainer()
{
}


QuFlowContainer::QuFlowContainer(
        const QVector<QuElementPtr>& elements,
        const Qt::Alignment alignment) :
    m_elements(elements)
{
    createAlignments(alignment);
}


QuFlowContainer::QuFlowContainer(
        std::initializer_list<QuElementPtr> elements,
        const Qt::Alignment alignment) :
    m_elements(elements)
{
    createAlignments(alignment);
}


QuFlowContainer::QuFlowContainer(
        std::initializer_list<QuElement*> elements,
        const Qt::Alignment alignment)
{
    for (auto e : elements) {
        addElement(e, alignment);
    }
}


void QuFlowContainer::createAlignments(const Qt::Alignment alignment)
{
    m_widget_alignments.clear();
    for (int i = 0; i < m_elements.size(); ++i) {
        m_widget_alignments.append(alignment);
    }
}


QuFlowContainer* QuFlowContainer::addElement(
        const QuElementPtr& element, const Qt::Alignment alignment)
{
    m_elements.append(element);
    m_widget_alignments.append(alignment);
    return this;
}


QuFlowContainer* QuFlowContainer::addElement(
        QuElement* element, const Qt::Alignment alignment)  // takes ownership
{
    // If you add a nullptr, it will be ignored.
    if (element) {
        m_elements.append(QuElementPtr(element));
        m_widget_alignments.append(alignment);
    }
    return this;
}


QuFlowContainer* QuFlowContainer::setWidgetAlignment(
        const Qt::Alignment alignment)
{
    createAlignments(alignment);
    return this;
}


QPointer<QWidget> QuFlowContainer::makeWidget(
        Questionnaire* questionnaire)
{
    QPointer<QWidget> widget(new BaseWidget());
    // NO, THIS BREAKS HFW: // widget->setSizePolicy(sizehelpers::expandingFixedHFWPolicy());

    FlowLayoutHfw* layout = new FlowLayoutHfw();
#ifdef DEBUG_LAYOUT
    widget->setObjectName(cssconst::DEBUG_YELLOW);
#endif
    layout->setContentsMargins(uiconst::NO_MARGINS);
    widget->setLayout(layout);
    for (int i = 0; i < m_elements.size(); ++i) {
        auto e = m_elements.at(i);
        auto alignment = m_widget_alignments.at(i);
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w, alignment);  // this is QLayout::setAlignment
    }
    return widget;
}


QVector<QuElementPtr> QuFlowContainer::subelements() const
{
    return m_elements;
}
