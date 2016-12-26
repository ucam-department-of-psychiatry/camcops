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

#include "quelement.h"
#include <QWidget>
#include "db/fieldref.h"


QuElement::QuElement() :
    m_widget(nullptr),
    m_visible(true)
{
}


QuElement::~QuElement()
{
}


QuElement* QuElement::addTag(const QString& tag)
{
    m_tags.append(tag);
    return this;
}


bool QuElement::hasTag(const QString &tag) const
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


QPointer<QWidget> QuElement::cachedWidget() const
{
    return m_widget;
}


QList<QuElementPtr> QuElement::subelements() const
{
    return QList<QuElementPtr>();
}


QList<QuElement*> QuElement::subelementsRaw() const
{
    QList<QuElement*> raw;
    for (auto e : subelements()) {
        raw.append(e.data());
    }
    return raw;
}


bool QuElement::missingInput() const
{
    FieldRefPtrList frefs = fieldrefs();
    for (FieldRefPtr f : frefs) {
        if (f->missingInput()) {
            return true;
        }
    }
    return false;
}


FieldRefPtrList QuElement::fieldrefs() const
{
    return FieldRefPtrList();
}


void QuElement::show()
{
    setVisible(true);
}


void QuElement::hide()
{
    setVisible(false);
}


bool QuElement::visible() const
{
    return m_visible;
}


void QuElement::setVisible(bool visible)
{
    // qDebug() << Q_FUNC_INFO << visible;
    if (visible == m_visible) {
        return;
    }
    m_visible = visible;
    if (m_widget) {
        m_widget->setVisible(visible);
    }
}


void QuElement::closing()
{
}
