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

#include "qucontainerhorizontal.h"
#include <QHBoxLayout>
#include <QWidget>
#include "questionnairelib/questionnaire.h"


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
    m_add_stretch_right = false;
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


QuContainerHorizontal* QuContainerHorizontal::setAddStretchRight(
        bool add_stretch_right)
{
    m_add_stretch_right = add_stretch_right;
    return this;
}


QPointer<QWidget> QuContainerHorizontal::makeWidget(
        Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
    // widget->setObjectName(CssConst::DEBUG_YELLOW);
    QHBoxLayout* layout = new QHBoxLayout();
    layout->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(layout);
    for (auto e : m_elements) {
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w);
    }
    if (m_add_stretch_right) {
        layout->addStretch();
    }
    return widget;
}


QList<QuElementPtr> QuContainerHorizontal::subelements() const
{
    return m_elements;
}
