#pragma once
#include <QLabel>
#include <QObject>
#include <QString>


QLabel* iconWidget(const QString& filename, bool scale = true);
void stopApp(const QString& error);
void alert(const QString& text, const QString& title = QObject::tr("Alert"));
