#include "layoutdumper.h"
#include <QDebug>
#include <QString>
#include <QStringBuilder>

#include <sstream>
#include <string>
#include <iostream>
#include <stdio.h>
#include <QtWidgets/QLayout>
#include <QtWidgets/QWidget>


using namespace LayoutDumper;


QString LayoutDumper::toString(const QSizePolicy::Policy& policy)
{
    switch (policy) {
    case QSizePolicy::Fixed: return "Fixed";
    case QSizePolicy::Minimum: return "Minimum";
    case QSizePolicy::Maximum: return "Maximum";
    case QSizePolicy::Preferred: return "Preferred";
    case QSizePolicy::MinimumExpanding: return "MinimumExpanding";
    case QSizePolicy::Expanding: return "Expanding";
    case QSizePolicy::Ignored: return "Ignored";
    }
    return "unknown";
}


QString LayoutDumper::toString(const QSizePolicy& policy)
{
    QString result = QString("(%1, %2)")
            .arg(toString(policy.horizontalPolicy()))
            .arg(toString(policy.verticalPolicy()));
    if (policy.hasHeightForWidth()) {
        result += " [hasHeightForWidth]";
    }
    if (policy.hasWidthForHeight()) {
        result += " [hasWidthForHeight]";
    }
    return result;
}


QString LayoutDumper::toString(QLayout::SizeConstraint constraint)
{
    switch (constraint) {
    case QLayout::SetDefaultConstraint: return "SetDefaultConstraint";
    case QLayout::SetNoConstraint: return "SetNoConstraint";
    case QLayout::SetMinimumSize: return "SetMinimumSize";
    case QLayout::SetFixedSize: return "SetFixedSize";
    case QLayout::SetMaximumSize: return "SetMaximumSize";
    case QLayout::SetMinAndMaxSize: return "SetMinAndMaxSize";
    }
    return "unknown";
}


QString LayoutDumper::toString(const Qt::Alignment& alignment)
{
    QStringList elements;

    if (alignment & Qt::AlignLeft) {
        elements.append("AlignLeft");
    }
    if (alignment & Qt::AlignRight) {
        elements.append("AlignRight");
    }
    if (alignment & Qt::AlignHCenter) {
        elements.append("AlignHCenter");
    }
    if (alignment & Qt::AlignJustify) {
        elements.append("AlignJustify");
    }
    if (alignment & Qt::AlignAbsolute) {
        elements.append("AlignAbsolute");
    }
    if ((alignment & Qt::AlignHorizontal_Mask) == 0) {
        elements.append("<horizontal_none>");
    }

    if (alignment & Qt::AlignTop) {
        elements.append("AlignTop");
    }
    if (alignment & Qt::AlignBottom) {
        elements.append("AlignBottom");
    }
    if (alignment & Qt::AlignVCenter) {
        elements.append("AlignVCenter");
    }
    if (alignment & Qt::AlignBaseline) {
        elements.append("AlignBaseline");
    }
    if ((alignment & Qt::AlignVertical_Mask) == 0) {
        elements.append("<vertical_none>");
    }

    return elements.join(" | ");
}


QString LayoutDumper::toString(void* pointer)
{
    // http://stackoverflow.com/questions/8881923/how-to-convert-a-pointer-value-to-qstring
    return QString("0x%1").arg((quintptr)pointer,
                               QT_POINTER_SIZE * 2, 16, QChar('0'));
}

QString LayoutDumper::getWidgetInfo(const QWidget& w)
{
    const QRect& geom = w.geometry();
    QSize sizehint = w.sizeHint();
    QSize minsizehint = w.minimumSizeHint();
    // Can't have >9 arguments to QString arg() system.
    // Using QStringBuilder with % leads to more type faff.
    QStringList elements;
    elements.append(QString("%1 %2 ('%3')")
                    .arg(w.metaObject()->className())
                    .arg(toString((void*)&w))
                    .arg(w.objectName()));
    elements.append(QString("pos (%1, %2)")
                    .arg(geom.x())
                    .arg(geom.y()));
    elements.append(QString("size (%1 x %2)")
                    .arg(geom.width())
                    .arg(geom.height()));
//    elements.append(QString("minimumSize (%1 x %2)")
//                    .arg(w.minimumSize().width())
//                    .arg(w.minimumSize().height()));
//    elements.append(QString("maximumSize (%1 x %2)")
//                    .arg(w.maximumSize().width())
//                    .arg(w.maximumSize().height()));
    elements.append(QString("sizeHint (%1 x %2), minimumSizeHint (%3 x %4), policy %5")
                    .arg(sizehint.width())
                    .arg(sizehint.height())
                    .arg(minsizehint.width())
                    .arg(minsizehint.height())
                    .arg(toString(w.sizePolicy())));
    elements.append(QString("stylesheet=%1")
                    .arg(w.styleSheet().isEmpty() ? "false" : "true"));
    elements.append(w.isVisible() ? "visible" : "HIDDEN");
    return elements.join(", ");
}


QString LayoutDumper::getLayoutItemInfo(QLayoutItem* item)
{
    QWidgetItem* wi = dynamic_cast<QWidgetItem*>(item);
    QSpacerItem* si = dynamic_cast<QSpacerItem*>(item);
    if (wi) {
        if (wi->widget()) {
            return QString("%1 [alignment: %2]")
                    .arg(getWidgetInfo(*wi->widget()))
                    .arg(toString(wi->alignment()));
        }
    } else if (si) {
        QSize hint = si->sizeHint();
        QLayout* layout = si->layout();
        return QString("QSpacerItem: sizeHint (%1 x %2), policy %3, "
                       "constraint %4, alignment %5")
                .arg(hint.width())
                .arg(hint.height())
                .arg(toString(si->sizePolicy()))
                .arg(layout ? toString(layout->sizeConstraint())
                            : "[no layout]")
                .arg(si->alignment());
    }
    return "";
}


QString LayoutDumper::getLayoutInfo(QLayout* layout)
{
    if (!layout) {
        return "null_layout";
    }
    QMargins margins = layout->contentsMargins();
    QSize sizehint = layout->sizeHint();
    QSize minsize = layout->minimumSize();
    QString name = layout->metaObject()->className();
    // usually unhelpful (blank): layout->objectName()
    QString margin = QString("margin (l=%1,t=%2,r=%3,b=%4)")
            .arg(margins.left())
            .arg(margins.top())
            .arg(margins.right())
            .arg(margins.bottom());
    QString constraint = QString("constraint %1")
            .arg(toString(layout->sizeConstraint()));
    QString sh = QString("sizeHint (%1 x %2)")
            .arg(sizehint.width())
            .arg(sizehint.height());
    QString ms = QString("minimumSize (%7 x %8)")
            .arg(minsize.width())
            .arg(minsize.height());
    QString hfw = layout->hasHeightForWidth() ? " [hasHeightForWidth]" : "";
    return QString("%1, %2, %3, %4, %5%6")
            .arg(name)
            .arg(margin)
            .arg(constraint)
            .arg(sh)
            .arg(ms)
            .arg(hfw);
}


void LayoutDumper::dumpWidgetAndChildren(QDebug& os, const QWidget* w,
                                         int level)
{
    QString padding;
    for (int i = 0; i <= level; i++) {
        padding += "    ";  // 4 spaces per level
    }

    QLayout* layout = w->layout();
    QList<QWidget*> dumped_children;
    if (layout && !layout->isEmpty()) {
        os << padding << "Layout: " << getLayoutInfo(layout);

        QBoxLayout* box_layout = dynamic_cast<QBoxLayout*>(layout);
        if (box_layout) {
            os << ", spacing " <<  box_layout->spacing();
        }
        os << ":\n";

        int num_items = layout->count();
        for (int i = 0; i < num_items; i++) {
            QLayoutItem* layout_item = layout->itemAt(i);
            QString item_info = getLayoutItemInfo(layout_item);
            if (!item_info.isEmpty()) {
                os << padding << "- " << item_info << "\n";
            }

            QWidgetItem* wi = dynamic_cast<QWidgetItem*>(layout_item);
            if (wi && wi->widget()) {
                dumpWidgetAndChildren(os, wi->widget(), level + 1);
                dumped_children.push_back(wi->widget());
            }
        }
    }

    // now output any child widgets that weren't dumped as part of the layout
    QList<QWidget*> widgets = w->findChildren<QWidget*>(
                QString(), Qt::FindDirectChildrenOnly);
    QList<QWidget*> undumped_children;
    foreach (QWidget* child, widgets) {
        if (dumped_children.indexOf(child) == -1) {
            undumped_children.push_back(child);
        }
    }

    if (!undumped_children.empty()) {
        os << padding << "Non-layout children:\n";
        foreach (QWidget* child, undumped_children) {
            dumpWidgetAndChildren(os, child, level + 1);
        }
    }
}


void LayoutDumper::dumpWidgetHierarchy(const QWidget* w)
{
    QDebug os = qDebug().noquote().nospace();
    os << "WIDGET HIERARCHY:\n";
    os << getWidgetInfo(*w) << "\n";
    dumpWidgetAndChildren(os, w, 0);
}
