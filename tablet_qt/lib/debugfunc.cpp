// #define DEBUG_EVEN_GIANT_VARIANTS
#include "debugfunc.h"
#include <QDebug>
#include <QDialog>
#include <QVariant>
#include <QVBoxLayout>
#include "lib/layoutdumper.h"
#include "qobjects/keypresswatcher.h"
#include "qobjects/showwatcher.h"


void DebugFunc::debugConcisely(QDebug debug, const QVariant& value)
{
#ifdef DEBUG_EVEN_GIANT_VARIANTS
    debug << value;
#else
    switch (value.type()) {

    // Big things; don't show their actual value to the console
    case QVariant::ByteArray:
        debug << "<ByteArray>";
        break;

    // Normal things
    default:
        debug << value;
        break;
    }
#endif
}


void DebugFunc::debugConcisely(QDebug debug, const QList<QVariant>& values)
{
    QDebug d = debug.nospace();
    d << "(";
    int n = values.length();
    for (int i = 0; i < n; ++i) {
        if (i > 0) {
            d << ", ";
        }
        debugConcisely(d, values.at(i));
    }
    d << ")";
}


void DebugFunc::dumpQObject(QObject* obj)
{
    qDebug("----------------------------------------------------");
    qDebug("Widget name : %s", qPrintable(obj->objectName()));
    qDebug("Widget class: %s", obj->metaObject()->className());
    qDebug("\nObject info [if Qt itself built in debug mode]:");
    obj->dumpObjectInfo();
    qDebug("\nObject tree [if Qt itself built in debug mode]:");
    obj->dumpObjectTree();
    qDebug("----------------------------------------------------");
}


void DebugFunc::debugWidget(QWidget* widget, bool set_background)
{
    QDialog dlg;
    dlg.setWindowTitle("Press D/dump layout, A/adjustSize");
    QVBoxLayout* layout = new QVBoxLayout();
    if (widget) {
        if (set_background) {
            widget->setObjectName("debug_green");
        }
        // Qt::Alignment align = Qt::AlignTop;
        Qt::Alignment align = 0;
        layout->addWidget(widget, 0, align);
        ShowWatcher* showwatcher = new ShowWatcher(&dlg, true);
        Q_UNUSED(showwatcher);
        KeyPressWatcher* keywatcher = new KeyPressWatcher(&dlg);
        keywatcher->addKeyEvent(
            Qt::Key_D,
            std::bind(&LayoutDumper::dumpWidgetHierarchy, &dlg));
        keywatcher->addKeyEvent(
            Qt::Key_A,
            std::bind(&QWidget::adjustSize, widget));
    } else {
        qDebug() << Q_FUNC_INFO << "null widget";
    }
    dlg.setLayout(layout);
    dlg.exec();
}
