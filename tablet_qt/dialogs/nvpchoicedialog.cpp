#include "nvpchoicedialog.h"
#include <functional>
#include <QDialogButtonBox>
#include <QEvent>
#include <QVariant>
#include <QVBoxLayout>
#include "lib/uifunc.h"
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

    QWidget* contentwidget = new QWidget();
    QVBoxLayout* contentlayout = new QVBoxLayout();
    contentwidget->setLayout(contentlayout);
    for (int i = 0; i < m_options.size(); ++i) {
        const NameValuePair& nvp = m_options.at(i);
        ClickableLabelWordWrapWide* label = new ClickableLabelWordWrapWide(
                    nvp.name());
        label->setSizePolicy(UiFunc::expandingFixedHFWPolicy());
        contentlayout->addWidget(label);
        // Safe object lifespan signal: can use std::bind
        connect(label, &ClickableLabelWordWrapWide::clicked,
                std::bind(&NvpChoiceDialog::itemClicked, this, i));
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
            this, &NvpChoiceDialog::reject);
    mainlayout->addWidget(standard_buttons);

    return exec();
}


void NvpChoiceDialog::itemClicked(int index)
{
    if (!m_new_value) {
        return;
    }
    *m_new_value = m_options.value(index);
    accept();
}


bool NvpChoiceDialog::event(QEvent* e)
{
    bool result = QDialog::event(e);
    QEvent::Type type = e->type();
    if (type == QEvent::Type::Show) {
        adjustSize();
    }
    return result;
}
