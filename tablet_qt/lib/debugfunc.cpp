/*
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

// #define DEBUG_EVEN_GIANT_VARIANTS

#include "debugfunc.h"
#include <QDebug>
#include <QDialog>
#include <QVariant>
#include <QVBoxLayout>
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "lib/layoutdumper.h"
#include "qobjects/keypresswatcher.h"
#include "qobjects/showwatcher.h"
#include "widgets/vboxlayouthfw.h"


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


void DebugFunc::debugWidget(QWidget* widget, bool set_background_by_name,
                            bool set_background_by_stylesheet,
                            bool show_widget_properties,
                            bool show_widget_attributes,
                            const int spaces_per_level,
                            bool use_hfw_layout)
{
    QDialog dlg;
    dlg.setWindowTitle("Press D/dump layout, A/adjustSize");
    VBoxLayoutHfw* hfwlayout = use_hfw_layout ? new VBoxLayoutHfw() : nullptr;
    QVBoxLayout* vboxlayout = use_hfw_layout ? nullptr : new QVBoxLayout();
    QLayout* layout = use_hfw_layout ? static_cast<QLayout*>(hfwlayout)
                                     : static_cast<QLayout*>(vboxlayout);
    layout->setContentsMargins(UiConst::NO_MARGINS);
    if (widget) {
        if (set_background_by_name) {
            widget->setObjectName(CssConst::DEBUG_GREEN);
        }
        if (set_background_by_stylesheet) {
            widget->setStyleSheet("background: green;");
        }
        // Qt::Alignment align = Qt::AlignTop;
        Qt::Alignment align = 0;
        if (use_hfw_layout) {
            hfwlayout->addWidget(widget, 0, align);
        } else {
            vboxlayout->addWidget(widget, 0, align);
        }
        ShowWatcher* showwatcher = new ShowWatcher(&dlg, true);
        Q_UNUSED(showwatcher);
        KeyPressWatcher* keywatcher = new KeyPressWatcher(&dlg);
        // keywatcher becomes child of dlg,
        // and LayoutDumper is a namespace, so:
        // Safe object lifespan signal: can use std::bind
        keywatcher->addKeyEvent(
            Qt::Key_D,
            std::bind(&LayoutDumper::dumpWidgetHierarchy, &dlg,
                      show_widget_properties, show_widget_attributes,
                      spaces_per_level));
        keywatcher->addKeyEvent(
            Qt::Key_A,
            std::bind(&QWidget::adjustSize, widget));
    } else {
        qDebug() << Q_FUNC_INFO << "null widget";
    }
    dlg.setLayout(layout);
    dlg.exec();
}
