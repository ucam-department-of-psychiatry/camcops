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

#pragma once
#include "questionnairelib/quelement.h"


class QuVerticalContainer : public QuElement
{
    // Allows the arrangements of other elements into a vertical layout.

    Q_OBJECT
public:
    static const Qt::Alignment DefaultWidgetAlignment;
public:
    QuVerticalContainer();
    QuVerticalContainer(
            const QVector<QuElementPtr>& elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuVerticalContainer(
            std::initializer_list<QuElementPtr> elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuVerticalContainer(
            std::initializer_list<QuElement*> elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);  // takes ownership
    QuVerticalContainer* addElement(
            const QuElementPtr& element,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuVerticalContainer* addElement(
            QuElement* element,
            Qt::Alignment alignment = DefaultWidgetAlignment);  // takes ownership
    QuVerticalContainer* setWidgetAlignment(Qt::Alignment alignment);
protected:
    void createAlignments(Qt::Alignment alignment);
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QVector<QuElementPtr> subelements() const override;
protected:
    QVector<QuElementPtr> m_elements;
    QVector<Qt::Alignment> m_widget_alignments;
};
