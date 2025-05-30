/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

// #define DEBUG_EVEN_GIANT_VARIANTS

#include "debugfunc.h"

#include <QDebug>
#include <QVariant>

#include "dialogs/debugdialog.h"

namespace debugfunc {


void debugConcisely(QDebug debug, const QVariant& value)
{
#ifdef DEBUG_EVEN_GIANT_VARIANTS
    debug << value;
#else
    switch (value.typeId()) {

        // Big things; don't show their actual value to the console
        case QMetaType::QByteArray:
            debug << "<ByteArray>";
            break;

        // Normal things
        default:
            debug << value;
            break;
    }
#endif
}

void debugConcisely(QDebug debug, const QVector<QVariant>& values)
{
    QDebug d = debug.nospace();
    d << "(";
    const int n = values.length();
    for (int i = 0; i < n; ++i) {
        if (i > 0) {
            d << ", ";
        }
        debugConcisely(d, values.at(i));
    }
    d << ")";
}

void dumpQObject(QObject* obj)
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

void debugWidget(
    QWidget* widget,
    const bool set_background_by_name,
    const bool set_background_by_stylesheet,
    const layoutdumper::DumperConfig& config,
    const bool use_hfw_layout,
    const QString* dialog_stylesheet
)
{
    auto dlg = new DebugDialog(
        nullptr,
        widget,
        set_background_by_name,
        set_background_by_stylesheet,
        config,
        use_hfw_layout,
        dialog_stylesheet
    );

    dlg->exec();
}


}  // namespace debugfunc
