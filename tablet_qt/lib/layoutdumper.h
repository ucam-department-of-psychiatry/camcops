#pragma once
#include <QLayout>
#include <QSizePolicy>
#include <QString>
#include <QWidget>

// Based on https://gist.github.com/pjwhams, though significantly modified


namespace LayoutDumper
{
    QString toString(const QSizePolicy::Policy& policy);
    QString toString(const QSizePolicy& policy);
    QString toString(QLayout::SizeConstraint constraint);
    QString toString(const void* pointer);
    QString toString(const Qt::Alignment& alignment);
    QString getWidgetDescriptor(const QWidget* w);
    QString getWidgetInfo(const QWidget* w,
                          bool show_properties,
                          bool show_attributes);
    QString getWidgetAttributeInfo(const QWidget* w);
    QString getDynamicProperties(const QWidget* w);
    QString getLayoutInfo(const QLayout* layout);
    QString paddingSpaces(int level, int spaces_per_level);
    QList<const QWidget*> dumpLayoutAndChildren(
            QDebug& os, const QLayout* layout, int level,
            bool show_widget_properties,
            bool show_widget_attributes,
            const int spaces_per_level);
    QList<const QWidget*> dumpWidgetAndChildren(
            QDebug& os, const QWidget* w, int level,
            const QString& alignment,
            bool show_widget_properties,
            bool show_widget_attributes,
            const int spaces_per_level);
    void dumpWidgetHierarchy(const QWidget* w,
                             bool show_widget_properties = true,
                             bool show_widget_attributes = false,
                             const int spaces_per_level = 4);
}

/*

NOTES
-   If a widget's size() doesn't match the combination of its sizeHint(),
    minimumSizeHint(), and sizePolicy(), check for setFixedSize() calls.
-   If a QWidget isn't drawing its background... they generally don't.
    Consider:
        - using a QFrame
        - setAttribute(Qt::WidgetAttribute::WA_StyledBackground, true);

*/
