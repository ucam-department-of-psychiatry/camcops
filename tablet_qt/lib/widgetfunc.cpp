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

// #define DEBUG_MIN_SIZE_FOR_TITLE

#include "widgetfunc.h"

#include <QApplication>
#include <QByteArray>
#include <QColor>
#include <QDebug>
#include <QFont>
#include <QFontMetrics>
#include <QLayout>
#include <QLayoutItem>
#include <QPlainTextEdit>
#include <QScrollBar>
#include <QSize>
#include <QString>
#include <QStyle>
#include <QVariant>
#include <QWidget>

#include "common/cssconst.h"
#include "common/platform.h"
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

void setPropertyValid(
    QWidget* widget, const bool valid, const bool repolish
)
{
    setProperty(
        widget, cssconst::PROPERTY_VALID, cssBoolean(valid), repolish
    );
}

void setPropertyInvalid(
    QWidget* widget, const bool invalid, const bool repolish
)
{
    setProperty(
        widget, cssconst::PROPERTY_INVALID, cssBoolean(invalid), repolish
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

QSize minimumSizeForTitle(const QWidget* widget, const bool include_app_name)
{
    if (!widget) {
        return QSize();
    }
    // +---------------------------------------------+
    // | ICON  TITLETEXT - APPTITLE    WINDOWBUTTONS |
    // |                                             |
    // | contents                                    |
    // +---------------------------------------------+

    // https://doc.qt.io/qt-6.5/qwidget.html#windowTitle-prop
    const QString window_title = widget->windowTitle();
    const QString app_name = QApplication::applicationDisplayName();
    QString full_title = window_title;
    if (include_app_name && !platform::PLATFORM_TABLET) {
        // Qt for Android doesn't append this suffix.
        // It does for Linux and Windows.
        const QString title_suffix = QString(" — %1").arg(app_name);
        full_title += title_suffix;
    }
    const QFont title_font = QApplication::font("QWorkspaceTitleBar");
    const QFontMetrics fm(title_font);
    const int title_w = fm.boundingRect(full_title).width();
    // ... "_w" means width

    // dialog->ensurePolished();
    // const QSize frame_size = dialog->frameSize();
    // const QSize content_size = dialog->size();
    // ... problem was that both are QSize(640, 480) upon creation
    // ... even if ensurePolished() is called first
    // const QSize frame_extra = frame_size - content_size;

    // How to count the number of icons shown on a window? ***
    // - Android: 0
    // - Linux: presumably may vary with window manager, but 4 is typical under
    //   XFCE (1 icon on left, 3 [rollup/maximize/close] on right), but need a
    //   bit more for spacing; 6 works better (at 24 pixels width per icon)
    // - Windows: also 4 (icon left, minimize/maximize/close on right)
    const int n_icons = platform::PLATFORM_TABLET ? 0 : 6;

    // How to read the size (esp. width) of a window icon? ***
    // const int icon_w = frame_extra.height();
    // ... on the basis that window icons are square!
    // ... but the problem is that frame size may as yet be zero
    const int icon_w = 24;

    const int final_w = title_w + n_icons * icon_w;
    const QSize widget_min_size = widget->minimumSize();
    QSize size(widget_min_size);
    size.setWidth(qMax(size.width(), final_w));
    size.setWidth(qMin(size.width(), widget->maximumWidth()));
#ifdef DEBUG_MIN_SIZE_FOR_TITLE
    qDebug().nospace() << Q_FUNC_INFO << "window_title = " << window_title
                       << ", app_name = " << app_name
                       << ", full_title = " << full_title
                       << ", title_font = " << title_font << ", title_w = "
                       << title_w
                       // << ", frame_size = " << frame_size
                       // << ", content_size = " << content_size
                       // << ", frame_extra = " << frame_extra
                       << ", n_icons = " << n_icons << ", icon_w = " << icon_w
                       << ", widget_min_size = " << widget_min_size
                       << ", size = " << size;
#endif
    return size;
}

}  // namespace widgetfunc
