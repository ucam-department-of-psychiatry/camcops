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

#pragma once
#include <QObject>
#include <QSize>
#include <QString>

class QAbstractButton;
class QLabel;
class QLayout;
class QPainter;
class QPlainTextEdit;
class QPointF;


namespace uifunc {

// ============================================================================
// Translation convenience function
// ============================================================================

QString tr(const char* text);

// ============================================================================
// QPixmap loader
// ============================================================================

QPixmap getPixmap(const QString& filename, const QSize& size = QSize(),
                  bool cache = true);

// ============================================================================
// Icons
// ============================================================================

QLabel* iconWidget(const QString& filename,
                   QWidget* parent = nullptr,
                   bool scale = true);
QPixmap addCircleBackground(const QPixmap& image, const QColor& colour,
                            bool behind = true,
                            qreal pixmap_opacity = 1.0);
QPixmap addPressedBackground(const QPixmap& image, bool behind = true);
QPixmap addUnpressedBackground(const QPixmap& image, bool behind = true);
QPixmap makeDisabledIcon(const QPixmap& image);
QLabel* blankIcon(QWidget* parent = nullptr);
QString resourceFilename(const QString& resourcepath);
QString iconFilename(const QString& basefile);

// ============================================================================
// Buttons
// ============================================================================

QString iconButtonStylesheet(const QString& normal_filename,
                             const QString& pressed_filename);
QAbstractButton* iconButton(const QString& normal_filename,
                            const QString& pressed_filename = "",
                            QWidget* parent = nullptr);
// QString iconPngFilename(const QString& stem);
// QString iconTouchedPngFilename(const QString& stem);

// ============================================================================
// Widget manipulations, and other Qt internals
// ============================================================================

// QString cssColour(const QColor& colour);
// void setBackgroundColour(QWidget* widget, const QColor& colour);
void removeAllChildWidgets(QObject* object);
Qt::Alignment combineAlignment(Qt::Alignment halign, Qt::Alignment valign);
void repolish(QWidget* widget);
void setProperty(QWidget* widget, const QString& property,
                 const QVariant& value, bool repolish = true);
QString cssBoolean(bool value);
// And some specific ones:
void setPropertyItalic(QWidget* widget, bool italic, bool repolish = true);
void setPropertyMissing(QWidget* widget, bool missing,
                        bool repolish = true);
// Drawing text with alignment at a point (not a rectangle):
void drawText(QPainter& painter, qreal x, qreal y, Qt::Alignment flags,
              const QString& text, QRectF* boundingRect = 0);
void drawText(QPainter& painter, const QPointF& point, Qt::Alignment flags,
              const QString& text, QRectF* boundingRect = 0);

// void clearLayout(QLayout* layout);

// Handy functions:

void scrollToEnd(QPlainTextEdit* editor);
void scrollToStart(QPlainTextEdit* editor);
// bool isScrollAtEnd(QPlainTextEdit* editor);

// ============================================================================
// Killing the app
// ============================================================================

void stopApp(const QString& error,
             const QString& title = "CamCOPS internal bug: stopping");

// ============================================================================
// Alerts
// ============================================================================

void alert(const QString& text,
           const QString& title = QObject::tr("Alert"),
           bool scroll = false);
void alert(const QStringList& lines,
           const QString& title = QObject::tr("Alert"),
           bool scroll = false);

// ============================================================================
// Confirmation
// ============================================================================

bool confirm(const QString& text, const QString& title,
             QString yes, QString no, QWidget* parent);

// ============================================================================
// Password checks/changes
// ============================================================================

bool getPassword(const QString& text, const QString& title,
                 QString& password, QWidget* parent);
bool getOldNewPasswords(const QString& text, const QString& title,
                        bool require_old_password,
                        QString& old_password, QString& new_password,
                        QWidget* parent);

// ============================================================================
// Fonts; CSS
// ============================================================================

QString textCSS(int fontsize_pt, bool bold = false, bool italic = false,
                const QString& colour = "");

// ============================================================================
// Opening URLS
// ============================================================================

void visitUrl(const QString& url);

// ============================================================================
// Strings
// ============================================================================

QString escapeString(const QString& string);
QString yesNo(bool yes);

// ============================================================================
// Scrolling
// ============================================================================

void applyScrollGestures(QWidget* widget);

}  // namespace uifunc
