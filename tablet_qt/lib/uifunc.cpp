/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

// #define DEBUG_ICON_LOAD

#include "uifunc.h"
#include <QApplication>
#include <QAbstractButton>
#include <QBrush>
#include <QDebug>
#include <QDesktopServices>
#include <QLabel>
#include <QLayout>
#include <QMessageBox>
#include <QObject>
#include <QPainter>
#include <QPen>
#include <QPixmapCache>
#include <QPlainTextEdit>
#include <QScrollBar>
#include <QScroller>
#include <QStyle>
#include <QToolButton>
#include <QUrl>
#include "common/cssconst.h"
#include "common/platform.h"
#include "common/textconst.h"
#include "common/uiconstants.h"
#include "lib/layoutdumper.h"
#include "lib/stringfunc.h"
#include "dialogs/passwordchangedialog.h"
#include "dialogs/passwordentrydialog.h"
#include "dialogs/scrollmessagebox.h"


namespace uifunc {

// ============================================================================
// Translation convenience function
// ============================================================================

QString tr(const char* text)
{
    return QObject::tr(text);
}


// ============================================================================
// QPixmap loader
// ============================================================================

QPixmap getPixmap(const QString& filename, const QSize& size, bool cache)
{
    QPixmap pm;
    bool success = true;
    if (cache) {
        if (!QPixmapCache::find(filename, &pm)) {
#ifdef DEBUG_ICON_LOAD
            qDebug() << "Loading icon:" << filename;
#endif
            success = pm.load(filename);
            QPixmapCache::insert(filename, pm);
        }
    } else {
        success = pm.load(filename);
    }
    if (success) {
        if (size.isValid()) {
            // Rescale
            pm = pm.scaled(size, Qt::IgnoreAspectRatio);
        }
    } else {
        qCritical() << Q_FUNC_INFO << "Unable to load icon:" << filename;
    }
    return pm;
}


// ============================================================================
// Icons
// ============================================================================

QLabel* iconWidget(const QString& filename, QWidget* parent, bool scale)
{
#ifdef DEBUG_ICON_LOAD
    qDebug() << "iconWidget:" << filename;
#endif
    QSize size;  // invalid size
    if (scale) {
        size = uiconst::ICONSIZE;
    }
    QPixmap iconimage = getPixmap(filename, size);
    QLabel* iconlabel = new QLabel(parent);
    iconlabel->setFixedSize(iconimage.size());
    iconlabel->setPixmap(iconimage);
    return iconlabel;
}


QPixmap addCircleBackground(const QPixmap& image, const QColor& colour,
                            bool behind, qreal pixmap_opacity)
{
    // Assumes it is of size ICONSIZE
    QSize size(image.size());
    QPixmap pm(size);
    pm.fill(uiconst::BLACK_TRANSPARENT);
    QPainter painter(&pm);
    QBrush brush(colour);
    painter.setBrush(brush);
    QPen pen(uiconst::BLACK_TRANSPARENT);
    painter.setPen(pen);
    if (behind) {
        // Background to indicate "being touched"
        painter.drawEllipse(0, 0, size.width(), size.height());
        // Icon
        painter.setOpacity(pixmap_opacity);
        painter.drawPixmap(0, 0, image);
    } else {
        // The other way around
        painter.setOpacity(pixmap_opacity);
        painter.drawPixmap(0, 0, image);
        painter.drawEllipse(0, 0, size.width(), size.height());
    }
    return pm;
}


QPixmap addPressedBackground(const QPixmap& image, bool behind)
{
    return addCircleBackground(image, uiconst::BUTTON_PRESSED_COLOUR, behind);
}


QPixmap addUnpressedBackground(const QPixmap& image, bool behind)
{
    return addCircleBackground(image, uiconst::BUTTON_UNPRESSED_COLOUR, behind);
}


QPixmap makeDisabledIcon(const QPixmap& image)
{
    return addCircleBackground(image, uiconst::BUTTON_DISABLED_COLOUR,
                               true, uiconst::DISABLED_ICON_OPACITY);
}


QLabel* blankIcon(QWidget* parent)
{
    QPixmap iconimage(uiconst::ICONSIZE);
    iconimage.fill(uiconst::BLACK_TRANSPARENT);
    QLabel* iconlabel = new QLabel(parent);
    iconlabel->setFixedSize(uiconst::ICONSIZE);
    iconlabel->setPixmap(iconimage);
    return iconlabel;
}


QString resourceFilename(const QString& resourcepath)
{
    return QString(":/resources/%1").arg(resourcepath);
}


QString iconFilename(const QString& basefile)
{
    return resourceFilename(QString("camcops/images/%1").arg(basefile));
}


// ============================================================================
// Buttons
// ============================================================================

QString iconButtonStylesheet(const QString& normal_filename,
                             const QString& pressed_filename)
{
    QString stylesheet = "QToolButton {"
                         "border-image: url('" + normal_filename + "');"
                         "}";
    if (!pressed_filename.isEmpty()) {
        // http://doc.qt.io/qt-5/stylesheet-syntax.html
        stylesheet += "QToolButton:pressed {"
                      "border-image: url('" + pressed_filename + "');"
                      "}";
    }
    // Related:
    // http://stackoverflow.com/questions/18388098/qt-pushbutton-hover-pressed-icons
    // http://stackoverflow.com/questions/12391125/qpushbutton-css-pressed
    // http://stackoverflow.com/questions/20207224/styling-a-qpushbutton-with-two-images
    return stylesheet;
}


QAbstractButton* iconButton(const QString& normal_filename,
                            const QString& pressed_filename,
                            QWidget* parent)
{
    QToolButton* button = new QToolButton(parent);
    button->setIconSize(uiconst::ICONSIZE);
    // Impossible to do this without stylesheets!
    // But you can do stylesheets in code...
    button->setStyleSheet(iconButtonStylesheet(normal_filename,
                                               pressed_filename));
    return button;
}

/*
QString UiFunc::iconPngFilename(const QString& stem)
{
    return iconFilename(stem + ".png");
}


QString UiFunc::iconTouchedPngFilename(const QString& stem)
{
    return iconFilename(stem + "_T.png");
}
*/


// ============================================================================
// Widget manipulations
// ============================================================================

/*
QString cssColour(const QColor& colour)
{
    QString css = QString("rgba(%1,%2,%3,%4)").arg(
        QString::number(colour.red()),
        QString::number(colour.green()),
        QString::number(colour.blue()),
        QString::number(colour.alpha()));
    return css;
}
*/


/*
void setBackgroundColour(QWidget* widget, const QColor& colour)
{
    // https://wiki.qt.io/How_to_Change_the_Background_Color_of_QWidget

    // Palette method not working. (Conflict with stylesheet?)
    // http://doc.qt.io/qt-5/qwidget.html#autoFillBackground-prop
    //
    // QPalette palette(widget->palette());
    // palette.setColor(QPalette::Background, Qt::red);
    // widget->setPalette(palette);
    // widget->setAutoFillBackground(true);

    // Stylesheet method working.
    widget->setStyleSheet("background-color:" + cssColour(colour) + ";");
}
*/


void removeAllChildWidgets(QObject* object)
{
    // http://stackoverflow.com/questions/22643853/qt-clear-all-widgets-from-inside-a-qwidgets-layout
    // ... modified a little
    qDebug() << "removeAllChildWidgets";
    for (QWidget* w : object->findChildren<QWidget*>()) {
        qDebug() << "1";
        if (!(w->windowFlags() & Qt::Window)) {
            qDebug() << "2";
            delete w;
        }
    }

    // BUT layouts do not become parents of their widgets:
    // http://stackoverflow.com/questions/4065378/qt-get-children-from-layout
}


const Qt::Alignment HALIGN_MASK = (Qt::AlignLeft | Qt::AlignRight |
                                   Qt::AlignHCenter | Qt::AlignJustify);
const Qt::Alignment VALIGN_MASK = (Qt::AlignTop | Qt::AlignBottom |
                                   Qt::AlignVCenter | Qt::AlignBaseline);


Qt::Alignment combineAlignment(Qt::Alignment halign, Qt::Alignment valign)
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


void setProperty(QWidget* widget, const QString& property,
                 const QVariant& value, bool repolish_afterwards)
{
    if (!widget) {
        qWarning() << Q_FUNC_INFO << "- ignored for null widget";
        return;
    }
    QByteArray propdata = property.toLatin1();
    const char* propname = propdata.constData();
    widget->setProperty(propname, value);
    if (repolish_afterwards) {
        repolish(widget);
    }
}


QString cssBoolean(bool value)
{
    return value ? cssconst::VALUE_TRUE : cssconst::VALUE_FALSE;
}


void setPropertyItalic(QWidget* widget, bool italic, bool repolish)
{
    setProperty(widget, cssconst::PROPERTY_ITALIC, cssBoolean(italic),
                repolish);
}


void setPropertyMissing(QWidget* widget, bool missing, bool repolish)
{
    setProperty(widget, cssconst::PROPERTY_MISSING, cssBoolean(missing),
                repolish);
}


void drawText(QPainter& painter, qreal x, qreal y, Qt::Alignment flags,
              const QString& text, QRectF* boundingRect)
{
    // http://stackoverflow.com/questions/24831484
   const qreal size = 32767.0;
   QPointF corner(x, y - size);
   if (flags & Qt::AlignHCenter) {
       corner.rx() -= size / 2.0;
   }
   else if (flags & Qt::AlignRight) {
       corner.rx() -= size;
   }
   if (flags & Qt::AlignVCenter) {
       corner.ry() += size / 2.0;
   }
   else if (flags & Qt::AlignTop) {
       corner.ry() += size;
   }
   else {
       flags |= Qt::AlignBottom;
   }
   QRectF rect(corner, QSizeF(size, size));
   painter.drawText(rect, flags, text, boundingRect);
}


void drawText(QPainter& painter, const QPointF& point, Qt::Alignment flags,
              const QString& text, QRectF* boundingRect)
{
    // http://stackoverflow.com/questions/24831484
   drawText(painter, point.x(), point.y(), flags, text, boundingRect);
}


/*

DANGER if this is used from signals from within this layout; you can get a
segfault from e.g. QAbstractItemView::mouseReleaseEvent.

void UiFunc::clearLayout(QLayout* layout)
{
    if (!layout) {
        qWarning() << "Null pointer passed to clearLayout";
        return;
    }
    // http://stackoverflow.com/questions/4857188/clearing-a-layout-in-qt
    QLayoutItem* item;
    while ((item = layout->takeAt(0))) {
        if (item->layout()) {
            clearLayout(item->layout());
            delete item->layout();
        }
        if (item->widget()) {
            delete item->widget();
        }
        delete item;
    }
    layout->invalidate();
}
*/

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


// ============================================================================
// Killing the app
// ============================================================================

void stopApp(const QString& error, const QString& title)
{
    // MODAL DIALOGUE, FOLLOWED BY HARD KILL,
    // so callers don't need to worry about what happens afterwards.
    QMessageBox msgbox;
    msgbox.setWindowTitle(title);
    msgbox.setText(error);
    msgbox.setStandardButtons(QMessageBox::Abort);
    msgbox.exec();
    QString msg = "ABORTING: " + error;
    qFatal("%s", qPrintable(msg));
    // If the first argument is not a string literal:
    // "format not a string literal and no format arguments"
    // https://bugreports.qt.io/browse/QTBUG-8967

    // qFatal() will kill the app
    // http://doc.qt.io/qt-4.8/qtglobal.html#qFatal

    // exit(EXIT_FAILURE);
}


// ============================================================================
// Alerts
// ============================================================================

void alert(const QString& text, const QString& title, bool scroll)
{
    if (scroll) {
        // Tasks may elect to show long text here
        ScrollMessageBox::plain(nullptr, title, text);
    } else {
        QMessageBox msgbox;
        msgbox.setWindowTitle(title);
        msgbox.setText(text);
        msgbox.setStandardButtons(QMessageBox::Ok);
        msgbox.exec();
    }
}


void alert(const QStringList& lines, const QString& title, bool scroll)
{
    alert(stringfunc::joinHtmlLines(lines), title, scroll);
}


// ============================================================================
// Confirmation
// ============================================================================

bool confirm(const QString& text, const QString& title,
             QString yes, QString no, QWidget* parent)
{
    if (yes.isEmpty()) {
        yes = tr("Yes");
    }
    if (no.isEmpty()) {
        no = tr("No");
    }
    QMessageBox msgbox(
        QMessageBox::Question,  // icon
        title,  // title
        text,  // text
        QMessageBox::Yes | QMessageBox::No,  // buttons
        parent);  // parent
    msgbox.setButtonText(QMessageBox::Yes, yes);
    msgbox.setButtonText(QMessageBox::No, no);
    int reply = msgbox.exec();
    return reply == QMessageBox::Yes;
}


// ============================================================================
// Password checks/changes
// ============================================================================

bool getPassword(const QString& text, const QString& title,
                 QString& password, QWidget* parent)
{
    PasswordEntryDialog dlg(text, title, parent);
    int reply = dlg.exec();
    if (reply != QDialog::Accepted) {
        return false;
    }
    // fetch/write back password
    password = dlg.password();
    return true;
}


bool getOldNewPasswords(const QString& text, const QString& title,
                        bool require_old_password,
                        QString& old_password, QString& new_password,
                        QWidget* parent)
{
    PasswordChangeDialog dlg(text, title, require_old_password, parent);
    int reply = dlg.exec();
    if (reply != QMessageBox::Accepted) {
        return false;
    }
    // Fetch/write back passwords
    old_password = dlg.oldPassword();
    new_password = dlg.newPassword();
    return true;
}


// ============================================================================
// CSS
// ============================================================================

QString textCSS(int fontsize_pt, bool bold, bool italic, const QString& colour)
{
    QString css;
    if (fontsize_pt > 0) {
        css += QString("font-size: %1pt;").arg(fontsize_pt);
    }
    // Only pt and px supported
    // http://doc.qt.io/qt-5.7/stylesheet-reference.html
    if (bold) {
        css += "font-weight: bold;";
    }
    if (italic) {
        css += "font-style: italic";
    }
    if (!colour.isEmpty()) {
        css += QString("color: %1").arg(colour);
    }
    return css;
}


// ============================================================================
// Opening URLS
// ============================================================================

void visitUrl(const QString& url)
{
    bool success = QDesktopServices::openUrl(QUrl(url));
    if (!success) {
        alert(tr("Failed to open browser"));
    }
}


// ============================================================================
// Strings
// ============================================================================

QString escapeString(const QString& string)
{
    // See also http://doc.qt.io/qt-5/qregexp.html#escape
    // Obsolete: Qt::escape()

    // Convert to a C++ literal.
    // There's probably a much more efficient way...
    QByteArray arr = string.toLatin1();
    int len = arr.length();
    QString result;
    result.reserve(len * 1.1);  // as per QString::toHtmlEscaped
    result.append('"');  // opening quote
    for (int i = 0; i < len; ++i) {
        char c = arr.at(i);
        if (c < ' ') {
            result.append('\\');
            result.append(c - 1 + 'a');
        } else {
            result.append(c);
        }
    }
    result.append('"');  // closing quote
    result.squeeze();  // as per QString::toHtmlEscaped
    return result;
}


QString yesNo(bool yes)
{
    return yes ? textconst::YES : textconst::NO;
}


QString yesNoNull(const QVariant& value)
{
    return value.isNull() ? "NULL" : yesNo(value.toBool());
}


QString yesNoUnknown(const QVariant& value)
{
    return value.isNull() ? textconst::UNKNOWN : yesNo(value.toBool());
}


QString trueFalse(bool yes)
{
    return yes ? textconst::TRUE : textconst::FALSE;
}


QString trueFalseNull(const QVariant& value)
{
    return value.isNull() ? "NULL" : trueFalse(value.toBool());
}


QString trueFalseUnknown(const QVariant& value)
{
    return value.isNull() ? textconst::UNKNOWN : trueFalse(value.toBool());
}



// ============================================================================
// Scrolling
// ============================================================================

void applyScrollGestures(QWidget* widget)
{
    if (!widget) {
        stopApp("Null pointer to applyScrollGestures");
    }

    // Unsure if this is necessary:
    widget->setAttribute(Qt::WA_AcceptTouchEvents);

    // 1. Grab the relevant gesture. Only one gesture can be grabbed.
    QScroller::ScrollerGestureType gesture_type = platform::PLATFORM_TABLET
            ? QScroller::TouchGesture
            : QScroller::LeftMouseButtonGesture;
    QScroller::grabGesture(widget, gesture_type);

    // 2. Disable overshoot.
    QScroller* scroller = QScroller::scroller(widget);
    if (scroller) {
        // http://stackoverflow.com/questions/24677152
        QScrollerProperties prop = scroller->scrollerProperties();
        QVariant overshoot_policy = QVariant::fromValue<QScrollerProperties::OvershootPolicy>(
                    QScrollerProperties::OvershootAlwaysOff);
        prop.setScrollMetric(QScrollerProperties::HorizontalOvershootPolicy,
                             overshoot_policy);
        prop.setScrollMetric(QScrollerProperties::VerticalOvershootPolicy,
                             overshoot_policy);
        scroller->setScrollerProperties(prop);
    }

    // Other discussions about this:
    // - https://forum.qt.io/topic/30546/kinetic-scrolling-on-qscrollarea-on-android-device/5
    // - http://falsinsoft.blogspot.co.uk/2015/09/qt-snippet-use-qscroller-with.html
    // - http://nootka-app.blogspot.co.uk/2015/11/story-of-porting-complex-qt-application_18.html
}


} // namespace uifunc
