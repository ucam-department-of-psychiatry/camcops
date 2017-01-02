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

#include "qucontainervertical.h"
#include <QVBoxLayout>
#include <QWidget>
#include "questionnairelib/questionnaire.h"
#include "widgets/basewidget.h"
#ifdef USE_HFW_LAYOUT
#include "widgets/vboxlayouthfw.h"
#endif


QuContainerVertical::QuContainerVertical()
{
}


QuContainerVertical::QuContainerVertical(const QList<QuElementPtr>& elements) :
    m_elements(elements)
{
}


QuContainerVertical::QuContainerVertical(
        std::initializer_list<QuElementPtr> elements) :
    m_elements(elements)
{
}


QuContainerVertical::QuContainerVertical(
        std::initializer_list<QuElement*> elements)  // takes ownership
{
    for (auto e : elements) {
        addElement(e);
    }
}


QuContainerVertical* QuContainerVertical::addElement(
        const QuElementPtr& element)
{
    m_elements.append(element);
    return this;
}


QuContainerVertical* QuContainerVertical::addElement(
        QuElement* element)  // takes ownership
{
    // If you add a nullptr, it will be ignored.
    if (element) {
        m_elements.append(QuElementPtr(element));
    }
    return this;
}


QPointer<QWidget> QuContainerVertical::makeWidget(Questionnaire* questionnaire)
{
    QPointer<QWidget> widget(new BaseWidget());

#ifdef USE_HFW_LAYOUT
    VBoxLayoutHfw* layout = new VBoxLayoutHfw();
#else
    QVBoxLayout* layout = new QVBoxLayout();
#endif

    // widget->setObjectName(CssConst::DEBUG_YELLOW);
    layout->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(layout);
    for (auto e : m_elements) {
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w);
    }
    return widget;
}


QList<QuElementPtr> QuContainerVertical::subelements() const
{
    return m_elements;
}
