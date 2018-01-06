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


class QuHorizontalContainer : public QuElement
{
    // Allows the arrangements of other elements into a horizontal layout.

    Q_OBJECT
public:
    static const Qt::Alignment DefaultWidgetAlignment;
    // An alignment of Qt::Alignment(), the default, makes the layout
    // EQUISPACE the widgets, which can look daft.
    // - http://www.qtcentre.org/threads/53609-QHBoxLayout-widget-spacing
public:
    QuHorizontalContainer();
    QuHorizontalContainer(
            const QVector<QuElementPtr>& elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuHorizontalContainer(
            std::initializer_list<QuElementPtr> elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuHorizontalContainer(
            std::initializer_list<QuElement*> elements,
            Qt::Alignment alignment = DefaultWidgetAlignment);  // takes ownership
    QuHorizontalContainer* addElement(
            const QuElementPtr& element,
            Qt::Alignment alignment = DefaultWidgetAlignment);
    QuHorizontalContainer* addElement(
            QuElement* element,
            Qt::Alignment alignment = DefaultWidgetAlignment);  // takes ownership
    QuHorizontalContainer* setWidgetAlignment(Qt::Alignment alignment);
    QuHorizontalContainer* setAddStretchRight(bool add_stretch_right);
protected:
    void commonConstructor();
    void createAlignments(Qt::Alignment alignment);
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QVector<QuElementPtr> subelements() const override;
protected:
    QVector<QuElementPtr> m_elements;
    QVector<Qt::Alignment> m_widget_alignments;
    bool m_add_stretch_right;
};
