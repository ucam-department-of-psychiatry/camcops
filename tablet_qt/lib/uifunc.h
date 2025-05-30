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

#pragma once
#include <QObject>
#include <QSize>
#include <QString>

#include "common/uiconst.h"

class CamcopsApp;
class QAbstractButton;
class QDialog;
class QLabel;
class QLayout;
class QPainter;
class QPlainTextEdit;
class QPointF;
class QWidget;

namespace uifunc {

// ============================================================================
// QPixmap loader
// ============================================================================

// Loads a pixmap from disk (or a resource file). By default, cache it by
// filename. If size is specified, rescale it.
QPixmap getPixmap(
    const QString& filename, const QSize& size = QSize(), bool cache = true
);

// ============================================================================
// Icons
// ============================================================================

// Returns a QLabel with an image loaded from the specified filename.
// If scale is true, scale to the specified size.
QLabel* iconWidget(
    const QString& filename,
    QWidget* parent = nullptr,
    bool scale = true,
    const QSize& size = uiconst::g_iconsize
);

// Given an existing QLabel, force it to show an icon of the standard size
// (or nothing, with zero size, if "filename" is empty).
void setLabelToIcon(
    QLabel* iconlabel,
    const QString& filename,
    bool scale = true,
    const QSize& size = uiconst::g_iconsize
);

// Adds a circle behind (or on top of) the supplied image (used for "you are
// touching this" indicators on icons).
QPixmap addCircleBackground(
    const QPixmap& image,
    const QColor& colour,
    bool behind = true,
    qreal pixmap_opacity = 1.0
);

// Adds a standard "you are touching this" indicator.
QPixmap addPressedBackground(const QPixmap& image, bool behind = true);

// Adds a standard "you could press this" indicator.
QPixmap addUnpressedBackground(const QPixmap& image, bool behind = true);

// Adds a standard "this button is unavailable" indicator.
QPixmap makeDisabledIcon(const QPixmap& image);

// Creates a blank icon of our standard size (or a specified size).
QLabel* blankIcon(
    QWidget* parent = nullptr, const QSize& size = uiconst::g_iconsize
);

// Returns the full "path" to a Qt QRC resource file; e.g. if given
// "somepath/somefile.txt", returns ":/resources/somepath/somefile.txt".
QString resourceFilename(const QString& resourcepath);

// Returns the full URL to a Qt QRC resource file; e.g. if given
// "somepath/somefile.txt", returns "qrc:///resources/somepath/somefile.txt".
QUrl resourceUrl(const QString& resourcepath);

// Returns a filename for a CamCOPS icon.
// From a basefilename like "something.png", returns
// ":/resources/camcops/images/something.png".
QString iconFilename(const QString& basefile);

// ============================================================================
// Buttons
// ============================================================================

// Returns CSS for a QToolButton that shows one image normally and another
// when being pressed/touched.
QString iconButtonStylesheet(
    const QString& normal_filename, const QString& pressed_filename
);

// Returns a button (a QToolButton) that shows one image normally and another
// when being pressed/touched.
QAbstractButton* iconButton(
    const QString& normal_filename,
    const QString& pressed_filename = QString(),
    QWidget* parent = nullptr
);


// ============================================================================
// Killing the app
// ============================================================================

// Are we in the application's main (GUI) thread?
bool amInGuiThread();

// Kill the app. Pops up a modal dialogue, then performs a hard kill.
[[noreturn]] void stopApp(
    const QString& error,
    // QStringLiteral() here causing compilation error on Windows
    // "function declared with 'noreturn' has a return statement"
    const QString& title = "CamCOPS internal bug: stopping"
);

// ============================================================================
// Alerts
// ============================================================================

// Show an alert message via a ScrollMessageBox.
void alert(const QString& text, const QString& title = QObject::tr("Alert"));

// Show an alert message via a ScrollMessageBox, joining the lines with "<br>".
void alert(
    const QStringList& lines, const QString& title = QObject::tr("Alert")
);

// Show an alert via a LogMessageBox.
void alertLogMessageBox(
    const QString& text, const QString& title, bool as_html = true
);

// Show an alert via a LogMessageBox, joining the lines with "\n" or
// "<br>" depending on as_html.
void alertLogMessageBox(
    const QStringList& lines, const QString& title, bool as_html = true
);

// Show an alert to say "you can't do this while CamCOPS is locked".
void alertNotWhenLocked();

// ============================================================================
// Confirmation
// ============================================================================

// Shows text and yes/no options in a modal dialogue box.
// Returns: does the user want to proceed?
bool confirm(
    const QString& text,
    const QString& title,
    QString yes,
    QString no,
    QWidget* parent = nullptr
);

// Shows text in a modal dialogue box. The user must type 'Yes' to proceed
// Returns: does the user want to proceed?
bool confirmDangerousOperation(
    const QString& text, const QString& title, QWidget* parent = nullptr
);

// ============================================================================
// Password checks/changes
// ============================================================================

// Asks the user for a password and stores it in "password".
// Returns: did the user enter one (rather than cancel)?
bool getPassword(
    const QString& text,
    const QString& title,
    QString& password,
    QWidget* parent
);

// Asks the user for an old password and a new password (twice) and stores
// them.
// Ensures that the new password is not blank and that the two copies match.
// Returns: did the user enter one (rather than cancel)?
bool getOldNewPasswords(
    const QString& text,
    const QString& title,
    bool require_old_password,
    QString& old_password,
    QString& new_password,
    QWidget* parent
);

// ============================================================================
// Choose language
// ============================================================================

// Allow the user to choose a language
void chooseLanguage(CamcopsApp& app, QWidget* parent_window);


// ============================================================================
// Fonts; CSS
// ============================================================================

// Generates a CSS string applicable to text, such as
// "font-size: 11pt; font-weight: bold;"
QString textCSS(
    int fontsize_pt,
    bool bold = false,
    bool italic = false,
    const QString& colour = QString()
);

// ============================================================================
// Opening URLS
// ============================================================================

// Uses QDesktopServices::openUrl() to launch a URL.
void visitUrl(const QString& url);

// ============================================================================
// Strings
// ============================================================================

// Converts a bool to a tr()-translated "Yes" or "No".
QString yesNo(bool yes);

// Converts a boolean QVariant to a tr()-translated "Yes"/"No" or "NULL".
QString yesNoNull(const QVariant& value);

// Converts a boolean QVariant to a tr()-translated "Yes"/"No" or "Unknown"
// for NULL.
QString yesNoUnknown(const QVariant& value);

// Converts a bool to a tr()-translated "True" or "False".
QString trueFalse(bool yes);

// Converts a boolean QVariant to a tr()-translated "True"/"False" or "NULL".
QString trueFalseNull(const QVariant& value);

// Converts a boolean QVariant to a tr()-translated "True"/"False" or "Unknown"
// for NULL.
QString trueFalseUnknown(const QVariant& value);

// ============================================================================
// Scrolling
// ============================================================================

// Applies scroll gestures to a widget, linking a gesture to a QScroller. Works
// well unless the widget also handles mouse events; that can be confusing!
void applyScrollGestures(QWidget* widget);

// If the object is a QAbstractItemView, puts its scrolling into ScrollPerPixel
// (smooth scrolling) mode.
void makeItemViewScrollSmoothly(QObject* object);

// ============================================================================
// Sizing
// ============================================================================

QSize minimumSizeForTitle(
    const QDialog* dialog, bool include_app_name = false
);

QScreen* screen();
QRect screenGeometry();
int screenWidth();
int screenHeight();
qreal screenDpi();

}  // namespace uifunc
