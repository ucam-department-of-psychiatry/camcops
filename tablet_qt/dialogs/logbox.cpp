#include "logbox.h"
#include <QApplication>
#include <QDebug>
#include <QHBoxLayout>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QScrollBar>
#include <QVBoxLayout>


LogBox::LogBox(QWidget* parent, const QString& title, bool offer_cancel,
               bool offer_ok_at_end, int maximum_block_count) :
    QDialog(parent),
    m_editor(nullptr),
    m_ok(nullptr),
    m_cancel(nullptr)
{
    // qDebug() << Q_FUNC_INFO;
    setWindowTitle(title);
    setMinimumWidth(600);
    setMinimumHeight(600);

    QVBoxLayout* mainlayout = new QVBoxLayout();
    setLayout(mainlayout);

    m_editor = new QPlainTextEdit();
    // QPlainTextEdit better than QTextEdit because it supports
    // maximumBlockCount while still allowing HTML (via appendHtml,
    // not insertHtml).
    m_editor->setReadOnly(true);
    m_editor->setLineWrapMode(QPlainTextEdit::NoWrap);
    m_editor->setMaximumBlockCount(maximum_block_count);
    mainlayout->addWidget(m_editor);

    QHBoxLayout* buttonlayout = new QHBoxLayout();
    QPushButton* copybutton = new QPushButton(tr("Copy"));
    buttonlayout->addWidget(copybutton);
    buttonlayout->addStretch();
    connect(copybutton, &QPushButton::clicked, this, &LogBox::copyClicked);

    if (offer_cancel) {
        m_cancel = new QPushButton(tr("Cancel"));
        buttonlayout->addWidget(m_cancel);
        connect(m_cancel, &QPushButton::clicked, this, &LogBox::reject);
    }

    buttonlayout->addStretch();

    if (offer_ok_at_end) {
        m_ok = new QPushButton(tr("OK"));
        buttonlayout->addWidget(m_ok);
        connect(m_ok, &QPushButton::clicked, this, &LogBox::okClicked);
        m_ok->hide();
    }

    mainlayout->addLayout(buttonlayout);
}


void LogBox::open()
{
    // qDebug() << Q_FUNC_INFO;
    QApplication::setOverrideCursor(Qt::WaitCursor);
    QDialog::open();
}


void LogBox::statusMessage(const QString& msg, bool as_html)
{
    if (!m_editor) {
        return;
    }
    if (as_html) {
        m_editor->appendHtml(msg);
    } else {
        m_editor->appendPlainText(msg);
    }
}


void LogBox::finish()
{
    // qDebug() << Q_FUNC_INFO;
    // If we're waiting for the user to press OK (so they can look at the log,
    // enable the OK button and await the accepted() signal via that button).
    // Otherwise, accept() now. Either way, restore the cursor.
    QApplication::restoreOverrideCursor();
    if (m_cancel) {
        m_cancel->hide();
    }
    if (m_ok) {
        m_ok->show();  // and await the accepted() signal via the button
    } else {
        accept();  // will emit accepted()
    }
}


void LogBox::okClicked()
{
    // qDebug() << Q_FUNC_INFO;
    accept();
    hide();  // hide explicitly, as we may be called using open() not exec()
}


void LogBox::copyClicked()
{
    m_editor->selectAll();
    m_editor->copy();
    m_editor->moveCursor(QTextCursor::End);
    scrollToEndOfLog();
}


void LogBox::scrollToEndOfLog()
{
    QScrollBar* vsb = m_editor->verticalScrollBar();
    if (vsb) {
        vsb->setValue(vsb->maximum());
    }
    QScrollBar* hsb = m_editor->horizontalScrollBar();
    if (hsb) {
        hsb->setValue(0);
    }
}
