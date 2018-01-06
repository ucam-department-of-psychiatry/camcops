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
#include <QLayout>
#include <QSizePolicy>
#include <QString>
#include <QWidget>

// Based on https://gist.github.com/pjwhams, though significantly modified


namespace layoutdumper {

class DumperConfig {
public:
    DumperConfig() {}
    DumperConfig(bool show_widget_properties,
                 bool show_all_widget_attributes,
                 bool show_set_widget_attributes,
                 bool show_widget_stylesheets,
                 bool spaces_per_level) :
        show_widget_properties(show_widget_properties),
        show_all_widget_attributes(show_all_widget_attributes),
        show_set_widget_attributes(show_set_widget_attributes),
        show_widget_stylesheets(show_widget_stylesheets),
        spaces_per_level(spaces_per_level)
    {}

public:
    bool show_widget_properties = false;
    // ... e.g.:
    // [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"]

    bool show_all_widget_attributes = false;
    // ... e.g.:
    // [WA_NoSystemBackground 0, WA_OpaquePaintEvent 0, WA_SetStyle 0,
    //  WA_StyleSheet 1, WA_TranslucentBackground 0, WA_StyledBackground 0]

    bool show_set_widget_attributes = false;
    // ... e.g.:
    // [WA_StyleSheet]

    bool show_widget_stylesheets = false;
    // ... the CSS attached by the user

    int spaces_per_level = 4;

    bool use_ultimate_parent = false;
    // ... travel up to the ultimate parent before travelling down
};

QString toString(const QSizePolicy::Policy& policy);
QString toString(const QSizePolicy& policy);
QString toString(QLayout::SizeConstraint constraint);
QString toString(const void* pointer);
QString toString(const Qt::Alignment& alignment);
QString toString(bool boolean);
QString getWidgetDescriptor(const QWidget* w);
QString getWidgetInfo(const QWidget* w,
                      const DumperConfig& config = DumperConfig());
QString getWidgetAttributeInfo(const QWidget* w, bool all = false);
QString getDynamicProperties(const QWidget* w);
QString getLayoutInfo(const QLayout* layout);
QString getSpacerInfo(QSpacerItem* si);
QString paddingSpaces(int level, int spaces_per_level);
QVector<const QWidget*> dumpLayoutAndChildren(
        QDebug& os, const QLayout* layout, int level,
        const DumperConfig& config);
QVector<const QWidget*> dumpWidgetAndChildren(
        QDebug& os, const QWidget* w, int level,
        const QString& alignment, const DumperConfig& config);
void dumpWidgetHierarchy(const QWidget* w,
                         const DumperConfig& config = DumperConfig());
const QWidget* ultimateParentWidget(const QWidget* w);

}  // namespace layoutdumper

/*

NOTES
-   If a widget's size() doesn't match the combination of its sizeHint(),
    minimumSizeHint(), and sizePolicy(), check for setFixedSize() calls.
-   If a QWidget isn't drawing its background... they generally don't.
    Consider:
        - using a QFrame
        - setAttribute(Qt::WidgetAttribute::WA_StyledBackground, true);

*/
