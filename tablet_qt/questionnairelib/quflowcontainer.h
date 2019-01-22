/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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


class QuFlowContainer : public QuElement
{
    // Allows the arrangements of other elements into a horizontal
    // but flowing layout. It uses FlowLayoutHfw (q.v.).

    Q_OBJECT
public:

    static const Qt::Alignment DefaultWidgetAlignment;
    // An alignment of Qt::Alignment(), the default, makes the layout
    // EQUISPACE the widgets, which can look daft. So we alter that by default.
    // - http://www.qtcentre.org/threads/53609-QHBoxLayout-widget-spacing

public:

    // Plain constructor
    QuFlowContainer();

    // Construct and add elements
    QuFlowContainer(
            const QVector<QuElementPtr>& elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuFlowContainer(
            std::initializer_list<QuElementPtr> elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuFlowContainer(
            std::initializer_list<QuElement*> elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);  // takes ownership

    // Add an element
    QuFlowContainer* addElement(
            const QuElementPtr& element,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuFlowContainer* addElement(
            QuElement* element,
            Qt::Alignment alignment = DefaultWidgetAlignment);  // takes ownership

    // Sets the alignment of all widgets (within their layout cells) to
    // alignment.
    QuFlowContainer* setWidgetAlignment(Qt::Alignment alignment);

protected:
    void commonConstructor();

    // Make all widgets have alignment "alignment".
    void createAlignments(Qt::Alignment alignment);

    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QVector<QuElementPtr> subelements() const override;

protected:
    QVector<QuElementPtr> m_elements;  // all our elements
    QVector<Qt::Alignment> m_widget_alignments;  // all their alignments
};
