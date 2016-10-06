#pragma once
#include <QDialog>
#include <QPointer>
class QPlainTextEdit;
class QPushButton;


class LogBox : public QDialog
{
    // Modal dialogue with a textual log window, used for displaying progress,
    // e.g. during network operations (see NetworkManager).

    Q_OBJECT
public:
    LogBox(QWidget* parent, const QString& title, bool offer_cancel = true,
           bool offer_ok_at_end = true, int maximum_block_count = 1000);
    void statusMessage(const QString& msg, bool as_html = false);
    void finish();
protected:
    void scrollToEndOfLog();
public slots:
    virtual void open() override;
    void okClicked();
    void copyClicked();
signals:
    void cancelled();
    void finished();
protected:
    QPointer<QPlainTextEdit> m_editor;
    QPointer<QPushButton> m_ok;
    QPointer<QPushButton> m_cancel;
};
