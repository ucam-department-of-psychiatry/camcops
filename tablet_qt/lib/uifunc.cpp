#define DEBUG_ICON_LOAD

#include <QApplication>
#include <QDebug>
#include <QMessageBox>
#include <QObject>
#include "uifunc.h"
#include "common/ui_constants.h"


QLabel* iconWidget(const QString& filename, bool scale)
{
#ifdef DEBUG_ICON_LOAD
    qDebug() << "iconWidget:" << filename;
#endif
    QPixmap iconimage = QPixmap(filename);
    QLabel* iconlabel = new QLabel();
    if (scale) {
        iconlabel->setFixedHeight(ICONSIZE);
        iconlabel->setFixedWidth(ICONSIZE);
        iconlabel->setPixmap(iconimage.scaled(ICONSIZE, ICONSIZE,
                                              Qt::IgnoreAspectRatio));
    } else {
        iconlabel->setPixmap(iconimage);
    }
    return iconlabel;
}


void stopApp(const QString& error)
{
    // MODAL DIALOGUE, FOLLOWED BY HARD KILL,
    // so callers don't need to worry about what happens afterwards.
    qDebug() << "ABORTING:" << qPrintable(error);
    QMessageBox msgbox;
    msgbox.setWindowTitle("CamCOPS internal bug: stopping");
    msgbox.setText(error);
    msgbox.setStandardButtons(QMessageBox::Abort);
    msgbox.exec();
    // QApplication::quit();
    exit(EXIT_FAILURE);
}


void alert(const QString& text, const QString& title)
{
    QMessageBox msgbox;
    msgbox.setWindowTitle(title);
    msgbox.setText(text);
    msgbox.setStandardButtons(QMessageBox::Ok);
    msgbox.exec();
}


