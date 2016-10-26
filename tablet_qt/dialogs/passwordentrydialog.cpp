#include "passwordentrydialog.h"
#include <QDialogButtonBox>
#include <QLabel>
#include <QLineEdit>
#include <QVBoxLayout>


PasswordEntryDialog::PasswordEntryDialog(const QString& text,
                                         const QString& title,
                                         QWidget* parent) :
    QDialog(parent)
{
    setWindowTitle(title);

    QLabel* prompt = new QLabel(text);

    m_editor = new QLineEdit();
    m_editor->setEchoMode(QLineEdit::Password);

    QDialogButtonBox* buttonbox = new QDialogButtonBox(
                QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    connect(buttonbox, &QDialogButtonBox::accepted,
            this, &PasswordEntryDialog::accept);
    connect(buttonbox, &QDialogButtonBox::rejected,
            this, &PasswordEntryDialog::reject);

    QVBoxLayout* mainlayout = new QVBoxLayout();
    mainlayout->addWidget(prompt);
    mainlayout->addWidget(m_editor);
    mainlayout->addWidget(buttonbox);
    setLayout(mainlayout);
}


QString PasswordEntryDialog::password() const
{
    if (!m_editor) {
        return "";
    }
    return m_editor->text();
}
