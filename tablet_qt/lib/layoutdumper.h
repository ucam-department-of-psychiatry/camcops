#pragma once
#include <QLayout>
#include <QSizePolicy>
#include <QString>
#include <QWidget>

// Based on https://gist.github.com/pjwhams


namespace LayoutDumper
{
    QString toString(const QSizePolicy::Policy& policy);
    QString toString(const QSizePolicy& policy);
    QString toString(QLayout::SizeConstraint constraint);
    QString toString(const void* pointer);
    QString toString(const Qt::Alignment& alignment);
    QString getWidgetDescriptor(const QWidget* w);
    QString getWidgetInfo(const QWidget* w);
    QString getWidgetAttributeInfo(const QWidget* w);
    QString getDynamicProperties(const QWidget* w);
    QString getLayoutInfo(const QLayout* layout);
    QList<const QWidget*> dumpLayoutAndChildren(
            QDebug& os, const QLayout* layout, int level);
    QList<const QWidget*> dumpWidgetAndChildren(
            QDebug& os, const QWidget* w, int level,
            const QString& alignment = "");
    void dumpWidgetHierarchy(const QWidget* w);
}

/*

NOTES
-   If a widget's size() doesn't match the combination of its sizeHint(),
    minimumSizeHint(), and sizePolicy(), check for setFixedSize() calls.

*/
