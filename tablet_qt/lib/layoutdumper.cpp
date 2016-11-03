// #define SHOW_WIDGET_ATTRIBUTES
// #define SHOW_WIDGET_PROPERTIES

#include "layoutdumper.h"
#include <iostream>
#include <sstream>
#include <string>
#include <stdio.h>
#include <QDebug>
#include <QString>
#include <QStringBuilder>
#include <QtWidgets/QLayout>
#include <QtWidgets/QWidget>
#include "lib/uifunc.h"

const QString NULL_WIDGET_STRING("<null_widget>");
const int SPACES_PER_LEVEL = 4;

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
    return "unknown_QSizePolicy";
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
    return "unknown_SizeConstraint";
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


QString LayoutDumper::toString(const void* pointer)
{
    // http://stackoverflow.com/questions/8881923/how-to-convert-a-pointer-value-to-qstring
    return QString("0x%1").arg((quintptr)pointer,
                               QT_POINTER_SIZE * 2, 16, QChar('0'));
}


QString LayoutDumper::getWidgetDescriptor(const QWidget* w)
{
    if (!w) {
        return NULL_WIDGET_STRING;
    }
    return QString("%1<%2 '%3'>")
            .arg(w->metaObject()->className())
            .arg(toString((void*)w))
            .arg(w->objectName());
}


QString LayoutDumper::getWidgetInfo(const QWidget* w)
{
    if (!w) {
        return NULL_WIDGET_STRING;
    }

    const QRect& geom = w->geometry();
    QSize sizehint = w->sizeHint();
    QSize minsizehint = w->minimumSizeHint();

    // Can't have >9 arguments to QString arg() system.
    // Using QStringBuilder with % leads to more type faff.
    QStringList elements;
    elements.append(getWidgetDescriptor(w));
    elements.append(w->isVisible() ? "visible" : "HIDDEN");
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
    elements.append(
        QString("sizeHint (%1 x %2), minimumSizeHint (%3 x %4), sizePolicy %5")
                    .arg(sizehint.width())
                    .arg(sizehint.height())
                    .arg(minsizehint.width())
                    .arg(minsizehint.height())
                    .arg(toString(w->sizePolicy())));
    elements.append(QString("stylesheet: %1")
                    .arg(w->styleSheet().isEmpty() ? "false" : "true"));

#ifdef SHOW_WIDGET_ATTRIBUTES
    elements.append(QString("attributes: [%1]").arg(getWidgetAttributeInfo(w)));
#endif

#ifdef SHOW_WIDGET_PROPERTIES
    QString properties = getDynamicProperties(w);
    if (!properties.isEmpty()) {
        elements.append(QString("properties: [%1]").arg(properties));
    }
#endif

    return elements.join(", ");
}


QString LayoutDumper::getWidgetAttributeInfo(const QWidget* w)
{
    // http://doc.qt.io/qt-5/qt.html#WidgetAttribute-enum
    if (!w) {
        return NULL_WIDGET_STRING;
    }
    QStringList elements;
    elements.append(QString("WA_NoSystemBackground %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_NoSystemBackground)));
    elements.append(QString("WA_OpaquePaintEvent %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_OpaquePaintEvent)));
    elements.append(QString("WA_SetStyle %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_SetStyle)));
    elements.append(QString("WA_StyleSheet %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_StyleSheet)));
    elements.append(QString("WA_TranslucentBackground %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_TranslucentBackground)));
    elements.append(QString("WA_StyledBackground %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_StyledBackground)));
    return elements.join(", ");
}


QString LayoutDumper::getDynamicProperties(const QWidget* w)
{
    if (!w) {
        return NULL_WIDGET_STRING;
    }
    QStringList elements;
    QList<QByteArray> property_names = w->dynamicPropertyNames();
    for (const QByteArray& arr : property_names) {
        QString name(arr);
        QVariant value = w->property(arr);
        QString value_string = UiFunc::escapeString(value.toString());
        elements.append(QString("%1=%2").arg(name).arg(value_string));
    }
    return elements.join(", ");
}


QString LayoutDumper::getLayoutInfo(const QLayout* layout)
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


QList<const QWidget*> LayoutDumper::dumpLayoutAndChildren(QDebug& os,
                                                    const QLayout* layout,
                                                    int level)
{
    QString padding(level * SPACES_PER_LEVEL, ' ');
    QString next_padding((level + 1) * SPACES_PER_LEVEL, ' ');
    QList<const QWidget*> dumped_children;

    os << padding << "Layout: " << getLayoutInfo(layout);

    const QBoxLayout* box_layout = dynamic_cast<const QBoxLayout*>(layout);
    if (box_layout) {
        os << ", spacing " <<  box_layout->spacing();
    }
    os << "\n";

    if (layout->isEmpty()) {
        os << padding << "... empty layout\n";
    } else {
        int num_items = layout->count();
        for (int i = 0; i < num_items; i++) {
            QLayoutItem* layout_item = layout->itemAt(i);
            QLayout* child_layout = layout_item->layout();
            QWidgetItem* wi = dynamic_cast<QWidgetItem*>(layout_item);
            QSpacerItem* si = dynamic_cast<QSpacerItem*>(layout_item);
            if (wi && wi->widget()) {
                QString alignment = QString(" [alignment: %1]")
                        .arg(toString(wi->alignment()));
                dumped_children.append(
                    dumpWidgetAndChildren(os, wi->widget(), level + 1,
                                          alignment));
            } else if (child_layout) {
                dumped_children.append(
                    dumpLayoutAndChildren(os, child_layout, level + 1));
            } else if (si) {
                QSize si_hint = si->sizeHint();
                QLayout* si_layout = si->layout();
                os << next_padding << QString(
                          "QSpacerItem: sizeHint (%1 x %2), sizePolicy %3, "
                          "constraint %4 [alignment %5]\n")
                        .arg(si_hint.width())
                        .arg(si_hint.height())
                        .arg(toString(si->sizePolicy()))
                        .arg(si_layout ? toString(si_layout->sizeConstraint())
                                       : "<no_layout>")
                        .arg(toString(si->alignment()));
            } else {
                os << next_padding << "<unknown_QLayoutItem>";
            }
        }
    }
    return dumped_children;
}


QList<const QWidget*> LayoutDumper::dumpWidgetAndChildren(QDebug& os,
                                                    const QWidget* w,
                                                    int level,
                                                    const QString& alignment)
{
    QString padding(level * SPACES_PER_LEVEL, ' ');
    QString next_padding((level + 1) * SPACES_PER_LEVEL, ' ');

    os << padding << getWidgetInfo(w) << alignment << "\n";

    QLayout* layout = w->layout();
    QList<const QWidget*> dumped_children;
    dumped_children.append(w);
    if (layout) {
        dumped_children.append(
            dumpLayoutAndChildren(os, layout, level + 1));
    }

    // now output any child widgets that weren't dumped as part of the layout
    QList<QWidget*> widgets = w->findChildren<QWidget*>(
                QString(), Qt::FindDirectChildrenOnly);
    // Search options: FindDirectChildrenOnly or FindChildrenRecursively.
    QList<QWidget*> undumped_children;
    foreach (QWidget* child, widgets) {
        if (!dumped_children.contains(child)) {
            undumped_children.push_back(child);
        }
    }
    if (!undumped_children.empty()) {
        os << padding << "Non-layout children:\n";
        foreach (QWidget* child, undumped_children) {
            dumped_children.append(
                dumpWidgetAndChildren(os, child, level + 1));
        }
    }
    return dumped_children;
}


void LayoutDumper::dumpWidgetHierarchy(const QWidget* w)
{
    QDebug os = qDebug().noquote().nospace();
    os << "WIDGET HIERARCHY:\n";
    dumpWidgetAndChildren(os, w, 0);
}
