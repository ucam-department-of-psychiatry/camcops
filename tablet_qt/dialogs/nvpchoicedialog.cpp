/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#include "nvpchoicedialog.h"
#include <functional>
#include <QDialogButtonBox>
#include <QEvent>
#include <QVariant>
#include "layouts/layouts.h"
#include "lib/sizehelpers.h"
#include "widgets/clickablelabelwordwrapwide.h"
#include "widgets/verticalscrollarea.h"


NvpChoiceDialog::NvpChoiceDialog(QWidget* parent,
                                 const NameValueOptions& options,
                                 const QString& title) :
    QDialog(parent),
    m_options(options),
    m_title(title),
    m_new_value(nullptr)
{
}


int NvpChoiceDialog::choose(QVariant* new_value)
{
    if (!new_value) {
        return QDialog::DialogCode::Rejected;
    }
    m_new_value = new_value;
    setWindowTitle(m_title);

    QWidget* contentwidget = new QWidget();  // doesn't need to be BaseWidget; contains scroll area
    VBoxLayout* contentlayout = new VBoxLayout();
    contentwidget->setLayout(contentlayout);
    for (int i = 0; i < m_options.size(); ++i) {
        const NameValuePair& nvp = m_options.at(i);
        ClickableLabelWordWrapWide* label = new ClickableLabelWordWrapWide(
                    nvp.name());
        label->setSizePolicy(sizehelpers::expandingFixedHFWPolicy());
        contentlayout->addWidget(label);
        // Safe object lifespan signal: can use std::bind
        connect(label, &ClickableLabelWordWrapWide::clicked,
                std::bind(&NvpChoiceDialog::itemClicked, this, i));
    }

    VerticalScrollArea* scroll = new VerticalScrollArea();
    scroll->setWidget(contentwidget);

    VBoxLayout* mainlayout = new VBoxLayout();
    mainlayout->addWidget(scroll);
    setLayout(mainlayout);

    mainlayout->addStretch();

    // Offer a cancel button
    QDialogButtonBox* standard_buttons = new QDialogButtonBox(
                QDialogButtonBox::Cancel);
    connect(standard_buttons, &QDialogButtonBox::rejected,
            this, &NvpChoiceDialog::reject);
    mainlayout->addWidget(standard_buttons);

    return exec();
}


void NvpChoiceDialog::itemClicked(const int index)
{
    if (!m_new_value) {
        return;
    }
    *m_new_value = m_options.value(index);
    accept();
}


bool NvpChoiceDialog::event(QEvent* e)
{
    const bool result = QDialog::event(e);
    const QEvent::Type type = e->type();
    if (type == QEvent::Type::Show) {
        adjustSize();
    }
    return result;
}
