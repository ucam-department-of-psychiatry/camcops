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
    QString toString(void* pointer);
    QString toString(const Qt::Alignment& alignment);
    QString getWidgetInfo(const QWidget& w);
    QString getLayoutItemInfo(QLayoutItem* item);
    QString getLayoutInfo(QLayout* layout);
    void dumpWidgetAndChildren(QDebug& os, const QWidget* w, int level);
    void dumpWidgetHierarchy(const QWidget* w);
}

/*

NOTES
-   If a widget's size() doesn't match the combination of its sizeHint(),
    minimumSizeHint(), and sizePolicy(), check for setFixedSize() calls.

*/
