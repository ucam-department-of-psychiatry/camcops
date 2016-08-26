// #define DEBUG_ICON_LOAD

#include <QApplication>
#include <QAbstractButton>
#include <QBrush>
#include <QDebug>
#include <QDesktopServices>
#include <QLabel>
#include <QMessageBox>
#include <QObject>
#include <QPainter>
#include <QPen>
#include <QPixmapCache>
#include <QStyle>
#include <QToolButton>
#include <QUrl>
#include "uifunc.h"
#include "common/uiconstants.h"

// ============================================================================
// QPixmap loader
// ============================================================================

QPixmap UiFunc::getPixmap(const QString& filename, const QSize& size,
                          bool cache)
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
        qCritical() << "Unable to load icon:" << filename;
    }
    return pm;
}


// ============================================================================
// Icons
// ============================================================================

QLabel* UiFunc::iconWidget(const QString& filename, QWidget* parent, bool scale)
{
#ifdef DEBUG_ICON_LOAD
    qDebug() << "iconWidget:" << filename;
#endif
    QSize size;  // invalid size
    if (scale) {
        size = UiConst::ICONSIZE;
    }
    QPixmap iconimage = getPixmap(filename, size);
    QLabel* iconlabel = new QLabel(parent);
    iconlabel->setFixedSize(iconimage.size());
    iconlabel->setPixmap(iconimage);
    return iconlabel;
}


QPixmap UiFunc::addCircleBackground(const QPixmap& image, const QColor& colour,
                                    bool behind, qreal pixmap_opacity)
{
    // Assumes it is of size ICONSIZE
    QSize size(image.size());
    QPixmap pm(size);
    pm.fill(UiConst::BLACK_TRANSPARENT);
    QPainter painter(&pm);
    QBrush brush(colour);
    painter.setBrush(brush);
    QPen pen(UiConst::BLACK_TRANSPARENT);
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


QPixmap UiFunc::addPressedBackground(const QPixmap& image, bool behind)
{
    return addCircleBackground(image, UiConst::BUTTON_PRESSED_COLOUR, behind);
}


QPixmap UiFunc::addUnpressedBackground(const QPixmap& image, bool behind)
{
    return addCircleBackground(image, UiConst::BUTTON_UNPRESSED_COLOUR, behind);
}


QPixmap UiFunc::makeDisabledIcon(const QPixmap& image)
{
    return addCircleBackground(image, UiConst::BUTTON_DISABLED_COLOUR,
                               true, UiConst::DISABLED_ICON_OPACITY);
}


QLabel* UiFunc::blankIcon(QWidget* parent)
{
    QPixmap iconimage(UiConst::ICONSIZE);
    iconimage.fill(UiConst::BLACK_TRANSPARENT);
    QLabel* iconlabel = new QLabel(parent);
    iconlabel->setFixedSize(UiConst::ICONSIZE);
    iconlabel->setPixmap(iconimage);
    return iconlabel;
}


QString UiFunc::imageFilename(const QString& imagepath)
{
    return QString(":/images/%1").arg(imagepath);
}


QString UiFunc::iconFilename(const QString& basefile)
{
    return imageFilename(QString("camcops/%1").arg(basefile));
}


// ============================================================================
// Buttons
// ============================================================================

QString UiFunc::iconButtonStylesheet(const QString& normal_filename,
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


QAbstractButton* UiFunc::iconButton(const QString& normal_filename,
                                    const QString& pressed_filename,
                                    QWidget* parent)
{
    QToolButton* button = new QToolButton(parent);
    button->setIconSize(UiConst::ICONSIZE);
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
    //
    // QPalette palette(widget->palette());
    // palette.setColor(QPalette::Background, Qt::red);
    // widget->setPalette(palette);
    // widget->setAutoFillBackground(true);

    // Stylesheet method working.
    widget->setStyleSheet("background-color:" + cssColour(colour) + ";");
}
*/


void UiFunc::removeAllChildWidgets(QObject* object)
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


Qt::Alignment UiFunc::combineAlignment(Qt::Alignment halign,
                                       Qt::Alignment valign)
{
    return (halign & HALIGN_MASK) | (valign & VALIGN_MASK);
}


void UiFunc::repolish(QWidget* widget)
{
    // http://wiki.qt.io/DynamicPropertiesAndStylesheets
    widget->style()->unpolish(widget);
    widget->style()->polish(widget);
    widget->update();
}


void UiFunc::setProperty(QWidget* widget, const QString& property,
                         const QVariant& value, bool repolish)
{
    const char* propname = property.toLatin1().data();
    widget->setProperty(propname, value);
    if (repolish) {
        UiFunc::repolish(widget);
    }
}


QString UiFunc::cssBoolean(bool value)
{
    return value ? "true" : "false";
}


void UiFunc::setPropertyItalic(QWidget* widget, bool italic, bool repolish)
{
    setProperty(widget, UiConst::CSS_PROP_ITALIC, cssBoolean(italic),
                repolish);
}


void UiFunc::setPropertyMissing(QWidget* widget, bool missing, bool repolish)
{
    setProperty(widget, UiConst::CSS_PROP_MISSING, cssBoolean(missing),
                repolish);
}


void UiFunc::drawText(QPainter& painter, qreal x, qreal y, Qt::Alignment flags,
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


void UiFunc::drawText(QPainter& painter, const QPointF& point,
                      Qt::Alignment flags, const QString& text,
                      QRectF* boundingRect)
{
    // http://stackoverflow.com/questions/24831484
   drawText(painter, point.x(), point.y(), flags, text, boundingRect);
}


// ============================================================================
// Killing the app
// ============================================================================

void UiFunc::stopApp(const QString& error)
{
    // MODAL DIALOGUE, FOLLOWED BY HARD KILL,
    // so callers don't need to worry about what happens afterwards.
    QMessageBox msgbox;
    msgbox.setWindowTitle("CamCOPS internal bug: stopping");
    msgbox.setText(error);
    msgbox.setStandardButtons(QMessageBox::Abort);
    msgbox.exec();
    QString msg = "ABORTING: " + error;
    qFatal("%s", qPrintable(msg));
    // If the first argument is not a string literal:
    // "format not a string literal and no format arguments"
    // https://bugreports.qt.io/browse/QTBUG-8967

    // exit(EXIT_FAILURE);
}


// ============================================================================
// Alerts
// ============================================================================

void UiFunc::alert(const QString& text, const QString& title)
{
    QMessageBox msgbox;
    msgbox.setWindowTitle(title);
    msgbox.setText(text);
    msgbox.setStandardButtons(QMessageBox::Ok);
    msgbox.exec();
}


// ============================================================================
// CSS
// ============================================================================

QString UiFunc::textCSS(int fontsize_pt, bool bold, bool italic,
                        const QString& colour)
{
    QString css = QString("font-size: %1pt;").arg(fontsize_pt);
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

void UiFunc::visitUrl(const QString& url)
{
    bool success = QDesktopServices::openUrl(QUrl(url));
    if (!success) {
        alert(QObject::tr("Failed to open browser"));
    }
}
