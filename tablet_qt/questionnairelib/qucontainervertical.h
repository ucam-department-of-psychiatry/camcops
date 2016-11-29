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

#pragma once
#include "quelement.h"


class QuContainerVertical : public QuElement
{
    // Allows the arrangements of other elements into a vertical layout.

    Q_OBJECT
public:
    QuContainerVertical();
    QuContainerVertical(const QList<QuElementPtr>& elements);
    QuContainerVertical(std::initializer_list<QuElementPtr> elements);
    QuContainerVertical(std::initializer_list<QuElement*> elements);  // takes ownership
    QuContainerVertical* addElement(const QuElementPtr& element);
    QuContainerVertical* addElement(QuElement* element);  // takes ownership
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
protected:
    QList<QuElementPtr> m_elements;
};
