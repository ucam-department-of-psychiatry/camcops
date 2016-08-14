// #define DEBUG_ICON_LOAD

#include <QApplication>
#include <QAbstractButton>
#include <QDebug>
#include <QMessageBox>
#include <QObject>
#include <QToolButton>

#include "uifunc.h"
#include "common/uiconstants.h"

// ============================================================================
// QPixmap loader
// ============================================================================

QPixmap getPixmap(const QString& filename)
{
    QPixmap pixmap(filename);
    if (pixmap.isNull()) {
        qCritical() << "Unable to load icon:" << filename;
    }
    return pixmap;
}


// ============================================================================
// Icons
// ============================================================================

QLabel* iconWidget(const QString& filename, QWidget* parent, bool scale)
{
#ifdef DEBUG_ICON_LOAD
    qDebug() << "iconWidget:" << filename;
#endif
    QPixmap iconimage = getPixmap(filename);
    QLabel* iconlabel = new QLabel(parent);
    if (scale) {
        iconlabel->setFixedSize(QSize(ICONSIZE, ICONSIZE));
        iconlabel->setPixmap(iconimage.scaled(ICONSIZE, ICONSIZE,
                                              Qt::IgnoreAspectRatio));
    } else {
        iconlabel->setFixedSize(iconimage.size());
        iconlabel->setPixmap(iconimage);
    }
    return iconlabel;
}


QLabel* blankIcon(QWidget* parent)
{
    QPixmap iconimage(ICONSIZE, ICONSIZE);
    iconimage.fill(QColor(0, 0, 0, 0));  // a=0 means fully transparent
    QLabel* iconlabel = new QLabel(parent);
    iconlabel->setFixedSize(QSize(ICONSIZE, ICONSIZE));
    iconlabel->setPixmap(iconimage);
    return iconlabel;
}


// ============================================================================
// Buttons
// ============================================================================

QAbstractButton* iconButton(const QString& normal_filename,
                            const QString& pressed_filename,
                            QWidget* parent)
{
    QToolButton* button = new QToolButton(parent);
    button->setIconSize(QSize(ICONSIZE, ICONSIZE));
    // Impossible to do this without stylesheets!
    // But you can do stylesheets in code...
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

    button->setStyleSheet(stylesheet);
    return button;
}


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


// ============================================================================
// Killing the app
// ============================================================================

void stopApp(const QString& error)
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

void alert(const QString& text, const QString& title)
{
    QMessageBox msgbox;
    msgbox.setWindowTitle(title);
    msgbox.setText(text);
    msgbox.setStandardButtons(QMessageBox::Ok);
    msgbox.exec();
}
