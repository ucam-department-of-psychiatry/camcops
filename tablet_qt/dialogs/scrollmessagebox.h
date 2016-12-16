/*
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

// http://www.qtforum.org/article/18183/messagebox-with-qscrollbar.html

#pragma once
#include <QMessageBox>
#include <QDialogButtonBox>


class ScrollMessageBox : public QDialog
{
    Q_OBJECT

    using StandardButton = QDialogButtonBox::StandardButton;

public:
    ScrollMessageBox(const QMessageBox::Icon& icon,
                     const QString& title,
                     const QString& text,
                     QDialogButtonBox::StandardButtons buttons = QDialogButtonBox::Ok,
                     QWidget* parent = nullptr);
    void setDefaultButton(StandardButton button);

    static StandardButton critical(
            QWidget* parent,
            const QString& title,
            const QString& text,
            QDialogButtonBox::StandardButtons buttons = QDialogButtonBox::Ok,
            StandardButton defaultButton = QDialogButtonBox::NoButton);
    static StandardButton information(
            QWidget* parent,
            const QString& title,
            const QString& text,
            QDialogButtonBox::StandardButtons buttons = QDialogButtonBox::Ok,
            StandardButton defaultButton = QDialogButtonBox::NoButton);
    static StandardButton question(
            QWidget* parent,
            const QString& title,
            const QString& text,
            QDialogButtonBox::StandardButtons buttons = QDialogButtonBox::Ok,
            StandardButton defaultButton = QDialogButtonBox::NoButton);
    static StandardButton warning(
            QWidget* parent,
            const QString& title,
            const QString& text,
            QDialogButtonBox::StandardButtons buttons = QDialogButtonBox::Ok,
            StandardButton defaultButton = QDialogButtonBox::NoButton);

    // void showEvent(QShowEvent* event) override;

private:
    QPixmap standardIcon(QMessageBox::Icon icon);
    void setDefaultButton(QPushButton *button);
    // void updateSize();

    QLabel* m_label;
    QDialogButtonBox* m_button_box;

private slots:
    void handle_buttonClicked(QAbstractButton* button);
};
