#include "nvpchoicedialog.h"
#include <functional>
#include <QVariant>
#include <QVBoxLayout>
#include "verticalscrollarea.h"
#include "labelwordwrapwide.h"


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
        LabelWordWrapWide* label = new LabelWordWrapWide(nvp.name());
        label->setClickable(true);
        contentlayout->addWidget(label);
        connect(label, &LabelWordWrapWide::clicked,
                std::bind(&NvpChoiceDialog::itemClicked, this, i));
    }

    VerticalScrollArea* scroll = new VerticalScrollArea();
    scroll->setWidget(contentwidget);

    QVBoxLayout* mainlayout = new QVBoxLayout();
    mainlayout->addWidget(scroll);
    setLayout(mainlayout);

    // NvpChoiceDialog: offer a cancel button? ***
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
