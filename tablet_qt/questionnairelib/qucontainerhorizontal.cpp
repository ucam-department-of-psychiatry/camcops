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

#define USE_HFW_LAYOUT  // good

#include "qucontainerhorizontal.h"
#include <QHBoxLayout>
#include <QWidget>
#include "questionnairelib/questionnaire.h"
#include "widgets/basewidget.h"
#include "widgets/flowlayouthfw.h"
#ifdef USE_HFW_LAYOUT
#include "widgets/hboxlayouthfw.h"
#endif


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
    m_flow = true;

    // An alignment of Qt::Alignment(), the default, makes the layout
    // EQUISPACE the widgets, which looks daft.
    // - http://www.qtcentre.org/threads/53609-QHBoxLayout-widget-spacing
    m_widget_alignment = Qt::AlignLeft | Qt::AlignVCenter;

    m_add_stretch_right = true;
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


QuContainerHorizontal* QuContainerHorizontal::setFlow(bool flow)
{
    m_flow = flow;
    return this;
}


QuContainerHorizontal* QuContainerHorizontal::setWidgetAlignment(
        Qt::Alignment widget_alignment)
{
    m_widget_alignment = widget_alignment;
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
    QPointer<QWidget> widget(new BaseWidget());

#ifdef USE_HFW_LAYOUT
    HBoxLayoutHfw* hboxlayout = nullptr;
#else
    QHBoxLayout* hboxlayout = nullptr;
#endif

    FlowLayoutHfw* flowlayout = nullptr;
    QLayout* layout = nullptr;
    if (m_flow) {
        flowlayout = new FlowLayoutHfw();
        layout = static_cast<QLayout*>(flowlayout);
    } else {
#ifdef USE_HFW_LAYOUT
        hboxlayout = new HBoxLayoutHfw();
#else
        hboxlayout = new QHBoxLayout();
#endif
        layout = static_cast<QLayout*>(hboxlayout);
    }
    // widget->setObjectName(CssConst::DEBUG_YELLOW);
    layout->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(layout);
    for (auto e : m_elements) {
        QPointer<QWidget> w = e->widget(questionnaire);
        if (m_flow) {
            flowlayout->addWidget(w);  // uses QLayout::addWidget; no alignment option
            flowlayout->setAlignment(w, m_widget_alignment);  // this is QLayout::setAlignment
        } else {
            hboxlayout->addWidget(w, 0, m_widget_alignment);
        }
    }
    if (m_add_stretch_right && !m_flow) {
        hboxlayout->addStretch();
    }
    return widget;
}


QList<QuElementPtr> QuContainerHorizontal::subelements() const
{
    return m_elements;
}
