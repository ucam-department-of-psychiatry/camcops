#pragma once
#include <QDebug>
#include <QList>

class Questionnaire;
class QuElement;

class QVariant;


namespace DebugFunc
{
    void debugConcisely(QDebug debug, const QVariant& value);
    void debugConcisely(QDebug debug, const QList<QVariant>& values);

    void dumpQObject(QObject* obj);

    void debugWidget(QWidget* widget, bool set_background_by_name = false,
                     bool set_background_by_stylesheet = true);
}
