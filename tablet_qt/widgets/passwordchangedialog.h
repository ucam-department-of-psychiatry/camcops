#pragma once
#include <QDialog>
#include <QPointer>
class QLineEdit;


class PasswordChangeDialog : public QDialog
{
    Q_OBJECT
public:
    PasswordChangeDialog(const QString& text, const QString& title,
                         bool require_old_password,
                         QWidget* parent = nullptr);
    QString oldPassword() const;
    QString newPassword() const;
protected:
    void okClicked();
protected:
    QPointer<QLineEdit> m_editor_old;
    QPointer<QLineEdit> m_editor_new1;
    QPointer<QLineEdit> m_editor_new2;
};
