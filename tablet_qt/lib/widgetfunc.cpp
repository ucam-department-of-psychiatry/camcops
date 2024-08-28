/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/
// ============================================================================
// Widget manipulations
// ============================================================================

#include "widgetfunc.h"

#include <QByteArray>
#include <QColor>
#include <QDebug>
#include <QLayout>
#include <QLayoutItem>
#include <QPlainTextEdit>
#include <QScrollBar>
#include <QString>
#include <QStyle>
#include <QVariant>
#include <QWidget>

#include "common/cssconst.h"
#include "lib/css.h"

namespace widgetfunc {

void setBackgroundColour(QWidget* widget, const QColor& colour)
{
    // https://wiki.qt.io/How_to_Change_the_Background_Color_of_QWidget

    // Palette method not working. (Conflict with stylesheet?)
    // https://doc.qt.io/qt-6.5/qwidget.html#autoFillBackground-prop
    //
    // QPalette palette(widget->palette());
    // palette.setColor(QPalette::Background, Qt::red);
    // widget->setPalette(palette);
    // widget->setAutoFillBackground(true);

    // Stylesheet method working.
    widget->setStyleSheet("background-color:" + css::colourCss(colour) + ";");

    // See also:
    // https://stackoverflow.com/questions/25466030/make-qwidget-transparent
    // https://doc.qt.io/qt-6.5/qwidget.html#transparency-and-double-buffering
}

void setBackgroundAndPressedColour(
    QWidget* widget, const QColor& background, const QColor& pressed
)
{
    // untested
    widget->setStyleSheet(
        QString("QWidget {"
                "  background-color: %1;"
                "}"
                "QWidget:pressed {"
                "  background-color: %1;"
                "}")
            .arg(css::colourCss(background), css::colourCss(pressed))
    );
}

void removeAllChildWidgets(QObject* object)
{
    // http://stackoverflow.com/questions/22643853/qt-clear-all-widgets-from-inside-a-qwidgets-layout
    // ... modified a little
    qDebug() << "removeAllChildWidgets";
    for (QWidget* w : object->findChildren<QWidget*>()) {
        // qDebug() << "1";
        if (!(w->windowFlags() & Qt::Window)) {
            // qDebug() << "2";
            delete w;
        }
    }

    // BUT layouts do not become parents of their widgets:
    // http://stackoverflow.com/questions/4065378/qt-get-children-from-layout
}

const Qt::Alignment HALIGN_MASK
    = (Qt::AlignLeft | Qt::AlignRight | Qt::AlignHCenter | Qt::AlignJustify);
const Qt::Alignment VALIGN_MASK
    = (Qt::AlignTop | Qt::AlignBottom | Qt::AlignVCenter | Qt::AlignBaseline);

Qt::Alignment
    combineAlignment(const Qt::Alignment halign, const Qt::Alignment valign)
{
    return (halign & HALIGN_MASK) | (valign & VALIGN_MASK);
}

void repolish(QWidget* widget)
{
    // http://wiki.qt.io/DynamicPropertiesAndStylesheets
    // http://stackoverflow.com/questions/18187376/stylesheet-performance-hits-with-qt

    widget->style()->unpolish(widget);
    widget->style()->polish(widget);
    widget->update();
}

void setProperty(
    QWidget* widget,
    const QString& property,
    const QVariant& value,
    const bool repolish_afterwards
)
{
    if (!widget) {
        qWarning() << Q_FUNC_INFO << "- ignored for null widget";
        return;
    }
    const QByteArray propdata = property.toLatin1();
    const char* propname = propdata.constData();
    widget->setProperty(propname, value);
    if (repolish_afterwards) {
        repolish(widget);
    }
}

QString cssBoolean(const bool value)
{
    return value ? cssconst::VALUE_TRUE : cssconst::VALUE_FALSE;
}

void setPropertyItalic(QWidget* widget, const bool italic, const bool repolish)
{
    setProperty(
        widget, cssconst::PROPERTY_ITALIC, cssBoolean(italic), repolish
    );
}

void setPropertyMissing(
    QWidget* widget, const bool missing, const bool repolish
)
{
    setProperty(
        widget, cssconst::PROPERTY_MISSING, cssBoolean(missing), repolish
    );
}

void clearLayout(QLayout* layout, bool delete_widgets)
{
    // DANGER: do not use "delete"; use "deleteLater()".
    // If you use delete, if this is used from signals from within this layout;
    // you can get a segfault from e.g. QAbstractItemView::mouseReleaseEvent.

    if (!layout) {
        qWarning() << "Null pointer passed to clearLayout";
        return;
    }
    // http://stackoverflow.com/questions/4857188/clearing-a-layout-in-qt
    // https://stackoverflow.com/questions/4272196/qt-remove-all-widgets-from-layout

    // For all the layout items in our layout...
    while (QLayoutItem* item = layout->takeAt(0)) {
        // We now own "item", so may (and will) delete it.

        // If the layout item has a layout, clear it out
        if (QLayout* child_layout = item->layout()) {
            clearLayout(child_layout, delete_widgets);
            child_layout->deleteLater();
        }

        // If the layout item has a widget, and we're deleting widgets, delete
        // this widget
        if (delete_widgets) {
            if (QWidget* child_widget = item->widget()) {
                child_widget->deleteLater();
            }
        }

        // Delete the layout item (which we own).
        delete item;
    }
    layout->invalidate();
}

void scrollToEnd(QPlainTextEdit* editor)
{
    QScrollBar* vsb = editor->verticalScrollBar();
    if (vsb) {
        vsb->setValue(vsb->maximum());
    }
    QScrollBar* hsb = editor->horizontalScrollBar();
    if (hsb) {
        hsb->setValue(0);
    }
}

void scrollToStart(QPlainTextEdit* editor)
{
    QScrollBar* vsb = editor->verticalScrollBar();
    if (vsb) {
        vsb->setValue(0);
    }
    QScrollBar* hsb = editor->horizontalScrollBar();
    if (hsb) {
        hsb->setValue(0);
    }
}

/*
bool isScrollAtEnd(QPlainTextEdit* editor)
{
    QScrollBar* vsb = editor->verticalScrollBar();
    return vsb && vsb->value() == vsb->maximum();
}
*/

}  // namespace widgetfunc
