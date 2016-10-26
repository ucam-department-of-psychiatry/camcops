#include "pagepickerdialog.h"
#include <functional>
#include <QDialogButtonBox>
#include <QHBoxLayout>
#include <QVBoxLayout>
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

    QWidget* contentwidget = new QWidget();
    QVBoxLayout* contentlayout = new QVBoxLayout();
    contentwidget->setLayout(contentlayout);
    for (int i = 0; i < m_pages.size(); ++i) {
        const PagePickerItem& page = m_pages.at(i);
        QHBoxLayout* itemlayout = new QHBoxLayout();

        ClickableLabelWordWrapWide* label = new ClickableLabelWordWrapWide(
                    page.text());
        label->setSizePolicy(UiFunc::horizExpandingHFWPolicy());
        itemlayout->addWidget(label);

        ImageButton* icon = new ImageButton(page.iconFilename());
        itemlayout->addWidget(icon);

        contentlayout->addLayout(itemlayout);

        connect(label, &ClickableLabelWordWrapWide::clicked,
                std::bind(&PagePickerDialog::itemClicked, this, i));
        connect(icon, &ImageButton::clicked,
                std::bind(&PagePickerDialog::itemClicked, this, i));
    }

    VerticalScrollArea* scroll = new VerticalScrollArea();
    scroll->setWidget(contentwidget);

    QVBoxLayout* mainlayout = new QVBoxLayout();
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


void PagePickerDialog::itemClicked(int item_index)
{
    if (!m_new_page_number) {
        return;
    }
    const PagePickerItem& page = m_pages.at(item_index);
    if (!page.selectable()) {
        UiFunc::alert("You can’t select this page yet because preceding pages "
                      "(marked in yellow) are incomplete.",
                      "Complete preceding pages first");
        return;
    }
    *m_new_page_number = page.pageNumber();
    accept();
}
