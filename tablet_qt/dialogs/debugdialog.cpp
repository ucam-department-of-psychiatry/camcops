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

#include "debugdialog.h"

#include <QDialog>
#include <QDialogButtonBox>
#include <QVariant>
#include <QVBoxLayout>

#include "common/cssconst.h"
#include "common/uiconst.h"
#include "layouts/vboxlayouthfw.h"
#include "qobjects/keypresswatcher.h"
#include "qobjects/showwatcher.h"
#include "qobjects/widgetpositioner.h"

DebugDialog::DebugDialog(
    QWidget* parent,
    QWidget* widget,
    const bool set_background_by_name,
    const bool set_background_by_stylesheet,
    const layoutdumper::DumperConfig& config,
    const bool use_hfw_layout,
    const QString* dialog_stylesheet
) :
    QDialog(parent)
{
    QDialogButtonBox::StandardButtons buttons = QDialogButtonBox::Close;

    QSizePolicy dlg_sp(QSizePolicy::Preferred, QSizePolicy::Preferred);
    setSizePolicy(dlg_sp);
    setWindowTitle("Press D/dump layout, A/adjustSize");

    if (use_hfw_layout) {
        dlg_sp.setHeightForWidth(true);
    }
    if (dialog_stylesheet) {
        setStyleSheet(*dialog_stylesheet);
    }
    VBoxLayoutHfw* hfwlayout = use_hfw_layout ? new VBoxLayoutHfw() : nullptr;
    QVBoxLayout* vboxlayout = use_hfw_layout ? nullptr : new QVBoxLayout();
    QLayout* layout = use_hfw_layout ? static_cast<QLayout*>(hfwlayout)
                                     : static_cast<QLayout*>(vboxlayout);
    layout->setContentsMargins(uiconst::NO_MARGINS);
    if (widget) {
        if (set_background_by_name) {
            widget->setObjectName(cssconst::DEBUG_GREEN);
        }
        if (set_background_by_stylesheet) {
            widget->setStyleSheet("background: green;");
        }
        // const Qt::Alignment align = Qt::AlignTop;
        const Qt::Alignment align = Qt::Alignment();
        // We can't do what follows via the QLayout* pointer, which is why we
        // have to maintain these two:
        if (use_hfw_layout) {
            hfwlayout->addWidget(widget, 0, align);
        } else {
            vboxlayout->addWidget(widget, 0, align);
        }
        auto showwatcher = new ShowWatcher(this, true);
        Q_UNUSED(showwatcher)
        auto keywatcher = new KeyPressWatcher(this);
        // keywatcher becomes child of this,
        // and LayoutDumper is a namespace, so:
        // Safe object lifespan signal: can use std::bind
        keywatcher->addKeyEvent(
            Qt::Key_D,
            std::bind(&layoutdumper::dumpWidgetHierarchy, this, config)
        );
        keywatcher->addKeyEvent(
            Qt::Key_A, std::bind(&QWidget::adjustSize, widget)
        );
    } else {
        qDebug() << Q_FUNC_INFO << "null widget";
    }

    auto buttonbox = new QDialogButtonBox(buttons);
    connect(
        buttonbox, &QDialogButtonBox::rejected, this, &DebugDialog::reject
    );
    layout->addWidget(buttonbox);

    new WidgetPositioner(this);

    setLayout(layout);
}
