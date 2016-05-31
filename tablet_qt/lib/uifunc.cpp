#include <QApplication>
#include <QDebug>
#include <QMessageBox>
#include <QObject>
#include "uifunc.h"
#include "common/ui_constants.h"


QLabel* icon_widget(const QString& filename)
{
    qDebug() << "icon_widget:" << filename;
    QPixmap iconimage = QPixmap(filename);
    QLabel* iconlabel = new QLabel();
    iconlabel->setFixedHeight(ICONSIZE);
    iconlabel->setFixedWidth(ICONSIZE);
    iconlabel->setPixmap(iconimage.scaled(ICONSIZE, ICONSIZE, Qt::IgnoreAspectRatio));
    return iconlabel;
}


void stop_app(const QString& error)
{
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
