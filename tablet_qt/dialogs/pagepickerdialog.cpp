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

#include "pagepickerdialog.h"
#include <functional>
#include <QDialogButtonBox>
#include <QEvent>
#include <QVBoxLayout>
#include "layouts/layouts.h"
#include "lib/sizehelpers.h"
#include "lib/uifunc.h"
#include "widgets/clickablelabelwordwrapwide.h"
#include "widgets/imagebutton.h"
#include "widgets/verticalscrollarea.h"


PagePickerDialog::PagePickerDialog(QWidget* parent,
                                   const PagePickerItemList& pages,
                                   const QString& title) :
    QDialog(parent),
    m_pages(pages),
    m_title(title),
    m_new_page_number(nullptr)
{
}


int PagePickerDialog::choose(int* new_page_number)
{
    if (!new_page_number) {
        return QDialog::DialogCode::Rejected;
    }
    m_new_page_number = new_page_number;
    setWindowTitle(m_title);

    QWidget* contentwidget = new QWidget();  // doesn't need to be BaseWidget; contains scroll area
    VBoxLayout* contentlayout = new VBoxLayout();
    contentwidget->setLayout(contentlayout);
    for (int i = 0; i < m_pages.size(); ++i) {
        const PagePickerItem& page = m_pages.at(i);
        HBoxLayout* itemlayout = new HBoxLayout();

        ClickableLabelWordWrapWide* label = new ClickableLabelWordWrapWide(
                    page.text());
        label->setSizePolicy(sizehelpers::expandingFixedHFWPolicy());
        itemlayout->addWidget(label);

        ImageButton* icon = new ImageButton(page.iconFilename());
        itemlayout->addWidget(icon);

        contentlayout->addLayout(itemlayout);

        // Safe object lifespan signal: can use std::bind
        connect(label, &ClickableLabelWordWrapWide::clicked,
                std::bind(&PagePickerDialog::itemClicked, this, i));
        connect(icon, &ImageButton::clicked,
                std::bind(&PagePickerDialog::itemClicked, this, i));
    }

    VerticalScrollArea* scroll = new VerticalScrollArea();
    scroll->setWidget(contentwidget);

    QVBoxLayout* mainlayout = new QVBoxLayout();  // does not need to adjust height to contents; contains scroll area
    mainlayout->addWidget(scroll);
    setLayout(mainlayout);

    mainlayout->addStretch();

    // Offer a cancel button
    QDialogButtonBox* standard_buttons = new QDialogButtonBox(
                QDialogButtonBox::Cancel);
    connect(standard_buttons, &QDialogButtonBox::rejected,
            this, &PagePickerDialog::reject);
    mainlayout->addWidget(standard_buttons);

    return exec();
}


void PagePickerDialog::itemClicked(const int item_index)
{
    if (!m_new_page_number) {
        return;
    }
    const PagePickerItem& page = m_pages.at(item_index);
    if (!page.selectable()) {
        uifunc::alert("You can’t select this page yet because preceding pages "
                      "(marked with a warning symbol) are incomplete.",
                      "Complete preceding pages first");
        return;
    }
    *m_new_page_number = page.pageNumber();
    accept();
}


bool PagePickerDialog::event(QEvent* e)
{
    const bool result = QDialog::event(e);
    const QEvent::Type type = e->type();
    if (type == QEvent::Type::Show) {
        adjustSize();
    }
    return result;
}
