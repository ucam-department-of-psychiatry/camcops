#pragma once
#include <QDialog>
#include <QPointer>
class QLineEdit;


class PasswordEntryDialog : public QDialog
{
    Q_OBJECT
public:
    PasswordEntryDialog(const QString& text, const QString& title,
                        QWidget* parent = nullptr);
    QString password() const;
protected:
    QPointer<QLineEdit> m_editor;
};
