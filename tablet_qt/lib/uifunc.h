#pragma once
#include <QLabel>
#include <QObject>
#include <QString>


QLabel* icon_widget(const QString& filename);
void stop_app(const QString& error);
void alert(const QString& text, const QString& title = QObject::tr("Alert"));
