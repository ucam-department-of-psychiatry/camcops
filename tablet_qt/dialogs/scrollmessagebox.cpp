/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
// ... modified a bit

#include "scrollmessagebox.h"
#include <QApplication>
#include <QDebug>
#include <QDesktopWidget>
#include <QFontMetrics>
#include <QGridLayout>
#include <QLabel>
#include <QLayout>
#include <QPushButton>
#include <QScrollArea>
#include <QSize>
// #include <QSpacerItem>
#include <QStyle>
#include "lib/uifunc.h"

const QSize MIN_SIZE(600, 600);
// const QSize MAX_SIZE(1024, 1500);


ScrollMessageBox::ScrollMessageBox(const QMessageBox::Icon& icon,
                                   const QString& title,
                                   const QString& text,
                                   QDialogButtonBox::StandardButtons buttons,
                                   QWidget* parent) :
    QDialog(parent,
            Qt::Dialog | Qt::WindowTitleHint |
            Qt::CustomizeWindowHint | Qt::WindowCloseButtonHint)
{
    setWindowTitle(title);
    setMinimumSize(MIN_SIZE);

    QLabel* icon_label = nullptr;
    QScrollArea* scroll = nullptr;

    m_label = new QLabel(text);
    m_label->setTextInteractionFlags(Qt::TextInteractionFlags(style()->styleHint(
                    QStyle::SH_MessageBox_TextInteractionFlags, 0, this)));
    m_label->setAlignment(Qt::AlignVCenter | Qt::AlignLeft);
    m_label->setOpenExternalLinks(true);
    // m_label->setContentsMargins(2, 0, 0, 0);
    // m_label->setIndent(9);

    scroll = new QScrollArea(this);
    // scroll->setGeometry(QRect(10, 20, 560, 430));
    scroll->setWidget(m_label);
    scroll->setWidgetResizable(true);

    uifunc::applyScrollGestures(scroll->viewport());

    if (icon != QMessageBox::NoIcon) {
        icon_label = new QLabel();
        icon_label->setPixmap(standardIcon((QMessageBox::Icon)icon));
        icon_label->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    }

    m_button_box = new QDialogButtonBox(buttons);
    m_button_box->setCenterButtons(style()->styleHint(
                                QStyle::SH_MessageBox_CenterButtons, 0, this));
    QObject::connect(m_button_box, &QDialogButtonBox::clicked,
                     this, &ScrollMessageBox::handle_buttonClicked);

    QGridLayout *grid = new QGridLayout();  // not GridLayoutHfw/GridLayout

    if (icon != QMessageBox::NoIcon) {
        grid->addWidget(icon_label, 0, 0, 2, 1, Qt::AlignTop);
    }
    grid->addWidget(scroll, 0, 1, 1, 1);
    grid->addWidget(m_button_box, 1, 0, 1, 2);
    // grid->addItem(new QSpacerItem(0, 0), 2, 1);  // in case box bigger than text
    grid->setSizeConstraint(QLayout::SetNoConstraint);
    setLayout(grid);

    setModal(true);
}


QPixmap ScrollMessageBox::standardIcon(QMessageBox::Icon icon)
{
    QStyle *style = this->style();
    int icon_size = style->pixelMetric(QStyle::PM_MessageBoxIconSize, 0, this);
    QIcon tmp_icon;
    switch (icon) {
    case QMessageBox::Information:
        tmp_icon = style->standardIcon(QStyle::SP_MessageBoxInformation, 0, this);
        break;
    case QMessageBox::Warning:
        tmp_icon = style->standardIcon(QStyle::SP_MessageBoxWarning, 0, this);
        break;
    case QMessageBox::Critical:
        tmp_icon = style->standardIcon(QStyle::SP_MessageBoxCritical, 0, this);
        break;
    case QMessageBox::Question:
        tmp_icon = style->standardIcon(QStyle::SP_MessageBoxQuestion, 0, this);
    default:
        break;
    }
    if (!tmp_icon.isNull()) {
        return tmp_icon.pixmap(icon_size, icon_size);
    }
    return QPixmap();
}


void ScrollMessageBox::handle_buttonClicked(QAbstractButton* button)
{
    int ret = m_button_box->standardButton(button);
    done(ret);
}


void ScrollMessageBox::setDefaultButton(QPushButton *button)
{
    if (!m_button_box->buttons().contains(button)) {
        return;
    }
    button->setDefault(true);
    button->setFocus();
}


void ScrollMessageBox::setDefaultButton(QDialogButtonBox::StandardButton button)
{
    setDefaultButton(m_button_box->button(button));
}

/*
void ScrollMessageBox::showEvent(QShowEvent *e)
{
      updateSize();
      QDialog::showEvent(e);
}
*/

// Qt does a better job than this function or its predecessor...
/*
void ScrollMessageBox::updateSize()
{
    if (!isVisible()) {
        return;
    }

    QSize screen_size = QApplication::desktop()->availableGeometry(QCursor::pos()).size();
    QSize hard_limit = MAX_SIZE.boundedTo(screen_size);

    layout()->activate();
    QSize layout_size = layout()->sizeHint();

    QFontMetrics fmt(QApplication::font("QWorkspaceTitleBar"));
    int window_title_width = fmt.width(windowTitle()) + 50;

    QSize desired_size(
                qMin(layout_size.width(), window_title_width),
                layout_size.height() + 100);  // ??? some sort of extra
    QSize final_size = desired_size.boundedTo(hard_limit);

    resize(final_size);
}
*/


QDialogButtonBox::StandardButton ScrollMessageBox::critical(
        QWidget* parent,
        const QString& title,
        const QString& text,
        QDialogButtonBox::StandardButtons buttons,
        StandardButton defaultButton)
{
    ScrollMessageBox box(QMessageBox::Critical, title, text, buttons, parent);
    box.setDefaultButton(defaultButton);
    return static_cast<QDialogButtonBox::StandardButton>(box.exec());
}


QDialogButtonBox::StandardButton ScrollMessageBox::information(
        QWidget* parent,
        const QString& title,
        const QString& text,
        QDialogButtonBox::StandardButtons buttons,
        StandardButton defaultButton)
{
    ScrollMessageBox box(QMessageBox::Information, title, text, buttons, parent);
    box.setDefaultButton(defaultButton);
    return static_cast<QDialogButtonBox::StandardButton>(box.exec());
}


QDialogButtonBox::StandardButton ScrollMessageBox::question(
        QWidget* parent,
        const QString& title,
        const QString& text,
        QDialogButtonBox::StandardButtons buttons,
        StandardButton defaultButton)
{
    ScrollMessageBox box(QMessageBox::Question, title, text, buttons, parent);
    box.setDefaultButton(defaultButton);
    return static_cast<QDialogButtonBox::StandardButton>(box.exec());
}


QDialogButtonBox::StandardButton ScrollMessageBox::warning(
        QWidget* parent,
        const QString& title,
        const QString& text,
        QDialogButtonBox::StandardButtons buttons,
        StandardButton defaultButton)
{
    ScrollMessageBox box(QMessageBox::Warning, title, text, buttons, parent);
    box.setDefaultButton(defaultButton);
    return static_cast<QDialogButtonBox::StandardButton>(box.exec());
}


QDialogButtonBox::StandardButton ScrollMessageBox::plain(
        QWidget* parent,
        const QString& title,
        const QString& text,
        QDialogButtonBox::StandardButtons buttons,
        StandardButton defaultButton)
{
    ScrollMessageBox box(QMessageBox::NoIcon, title, text, buttons, parent);
    box.setDefaultButton(defaultButton);
    return static_cast<QDialogButtonBox::StandardButton>(box.exec());
}
