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
    QMessageBox msgBox;
    msgBox.setWindowTitle("CamCOPS internal bug: stopping");
    msgBox.setText(error);
    msgBox.setStandardButtons(QMessageBox::Abort);
    msgBox.exec();
    // QApplication::quit();
    exit(EXIT_FAILURE);
}

void alert(const QString& text, const QString& title)
{
    QMessageBox msgBox;
    msgBox.setWindowTitle(title);
    msgBox.setText(text);
    msgBox.setStandardButtons(QMessageBox::Ok);
    msgBox.exec();
}


